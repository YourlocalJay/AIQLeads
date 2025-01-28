"""
Geospatial visualization service for generating lead data visualizations.

This module provides optimized geospatial visualizations including:
- Density heatmaps
- Clustering analysis
- Market penetration choropleths
- Competitor proximity analysis

All visualizations use proper GeoJSON formatting, optimized PostGIS queries,
and implement caching with Redis.
"""

# ... [Previous imports and type definitions remain the same] ...

class GeospatialVisualizer:
    """
    Generates geospatial visualizations for lead data analysis with proper GeoJSON 
    formatting and optimized queries.
    """

    # ... [Previous __init__ and utility methods remain the same] ...

    @monitor(metric_name="geospatial_heatmap_generation")
    async def generate_density_heatmap(
        self,
        region: str,
        grid_size: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate heatmap data for lead density in GeoJSON format.
        
        Args:
            region: Region identifier
            grid_size: Optional grid size in meters (overrides config)
            
        Returns:
            GeoJSON feature collection with density data
        """
        grid_size = grid_size or self.grid_size
        cache_key = f"heatmap:{region}:{grid_size}"

        # Check cache
        if cached := await self.cache.get(cache_key):
            CACHE_HIT_RATE.labels("heatmap").observe(1.0)
            return cached

        CACHE_HIT_RATE.labels("heatmap").observe(0.0)

        try:
            with QUERY_TIME.labels("heatmap").time():
                # Use CTE for better query plan
                query = text("""
                    WITH grid AS (
                        SELECT 
                            ST_SnapToGrid(location, :grid_size) AS cell,
                            COUNT(*) as lead_count,
                            MIN(ST_X(location::geometry)) as min_x,
                            MIN(ST_Y(location::geometry)) as min_y,
                            MAX(ST_X(location::geometry)) as max_x,
                            MAX(ST_Y(location::geometry)) as max_y
                        FROM leads
                        WHERE region = :region
                        GROUP BY cell
                    )
                    SELECT 
                        ST_AsGeoJSON(cell) as geometry,
                        lead_count,
                        (max_x - min_x) as width,
                        (max_y - min_y) as height
                    FROM grid
                    WHERE cell IS NOT NULL
                """)

                result = await self.session.execute(
                    query,
                    {"region": region, "grid_size": grid_size}
                )
                rows = result.fetchall()

                features = [{
                    "coordinates": json.loads(row.geometry),
                    "properties": {
                        "count": row.lead_count,
                        "width": float(row.width),
                        "height": float(row.height)
                    }
                } for row in rows if row.geometry]

                heatmap_data = self._format_geojson(features, "Polygon")

                # Cache with configured TTL
                await self.cache.set(
                    cache_key,
                    heatmap_data,
                    expire=self.cache_ttl
                )
                return heatmap_data

        except Exception as e:
            logger.error(f"Failed to generate heatmap: {str(e)}", exc_info=True)
            raise

    @monitor(metric_name="geospatial_cluster_generation")
    async def generate_cluster_visualization(
        self,
        region: str,
        eps: Optional[float] = None,
        min_points: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate cluster visualization data using DBSCAN.
        
        Args:
            region: Region identifier
            eps: Optional cluster radius (overrides config)
            min_points: Optional minimum points per cluster (overrides config)
            
        Returns:
            GeoJSON feature collection with cluster data
        """
        eps = eps or self.cluster_eps
        min_points = min_points or self.cluster_min_points
        cache_key = f"clusters:{region}:{eps}:{min_points}"

        # Check cache
        if cached := await self.cache.get(cache_key):
            CACHE_HIT_RATE.labels("clusters").observe(1.0)
            return cached

        CACHE_HIT_RATE.labels("clusters").observe(0.0)

        try:
            with QUERY_TIME.labels("clusters").time():
                # Use CTE for improved query organization
                query = text("""
                    WITH clustered_points AS (
                        SELECT 
                            id,
                            location,
                            ST_ClusterDBSCAN(
                                location,
                                eps := :eps,
                                minpoints := :min_points
                            ) OVER () as cluster_id
                        FROM leads
                        WHERE region = :region
                    ),
                    cluster_stats AS (
                        SELECT
                            cluster_id,
                            COUNT(*) as point_count,
                            ST_ConvexHull(ST_Collect(location)) as hull
                        FROM clustered_points
                        GROUP BY cluster_id
                    )
                    SELECT
                        cluster_id,
                        point_count,
                        ST_AsGeoJSON(hull) as geometry,
                        ST_Area(hull) as area
                    FROM cluster_stats
                    WHERE cluster_id IS NOT NULL
                """)

                result = await self.session.execute(
                    query,
                    {
                        "region": region,
                        "eps": eps,
                        "min_points": min_points
                    }
                )
                rows = result.fetchall()

                features = [{
                    "coordinates": json.loads(row.geometry),
                    "properties": {
                        "cluster_id": row.cluster_id,
                        "point_count": row.point_count,
                        "area": float(row.area)
                    }
                } for row in rows if row.geometry]

                cluster_data = self._format_geojson(features, "Polygon")

                # Cache results
                await self.cache.set(
                    cache_key,
                    cluster_data,
                    expire=self.cache_ttl
                )
                return cluster_data

        except Exception as e:
            logger.error(f"Failed to generate clusters: {str(e)}", exc_info=True)
            raise

    @monitor(metric_name="geospatial_choropleth_generation")
    async def generate_market_penetration_choropleth(
        self,
        region: str,
        subdivision_level: Optional[SubdivisionLevel] = None
    ) -> Dict[str, Any]:
        """
        Generate choropleth map data showing market penetration.
        
        Args:
            region: Region identifier
            subdivision_level: Optional subdivision level (overrides config)
            
        Returns:
            GeoJSON feature collection with penetration data
        """
        subdivision_level = subdivision_level or self.subdivision_level
        cache_key = f"choropleth:{region}:{subdivision_level}"

        if cached := await self.cache.get(cache_key):
            CACHE_HIT_RATE.labels("choropleth").observe(1.0)
            return cached

        CACHE_HIT_RATE.labels("choropleth").observe(0.0)

        try:
            with QUERY_TIME.labels("choropleth").time():
                # Use window functions for efficient aggregation
                query = text("""
                    WITH lead_counts AS (
                        SELECT 
                            subdivision->:level as area,
                            COUNT(*) FILTER (WHERE NOT is_competitor) as our_leads,
                            COUNT(*) as total_leads
                        FROM leads
                        WHERE region = :region
                        GROUP BY subdivision->:level
                    )
                    SELECT
                        r.name,
                        ST_AsGeoJSON(r.geometry) as geometry,
                        COALESCE(lc.our_leads, 0) as our_leads,
                        COALESCE(lc.total_leads, 0) as total_leads
                    FROM regions r
                    LEFT JOIN lead_counts lc ON r.name = lc.area
                    WHERE r.level = :level
                """)

                result = await self.session.execute(
                    query,
                    {
                        "region": region,
                        "level": subdivision_level
                    }
                )
                rows = result.fetchall()

                features = [{
                    "coordinates": json.loads(row.geometry),
                    "properties": {
                        "name": row.name,
                        "our_leads": row.our_leads,
                        "total_leads": row.total_leads,
                        "penetration": (
                            row.our_leads / row.total_leads 
                            if row.total_leads > 0 else 0
                        )
                    }
                } for row in rows if row.geometry]

                choropleth_data = self._format_geojson(
                    features,
                    "MultiPolygon"
                )

                await self.cache.set(
                    cache_key,
                    choropleth_data,
                    expire=self.cache_ttl
                )
                return choropleth_data

        except Exception as e:
            logger.error(
                f"Failed to generate choropleth: {str(e)}",
                exc_info=True
            )
            raise
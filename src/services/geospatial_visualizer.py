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
# [Previous content remains the same... until competitor_proximity method]

    @monitor(metric_name="geospatial_proximity_generation")
    async def generate_competitor_proximity_analysis(
        self,
        region: str,
        radius: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate competitor proximity analysis with optimized spatial queries.
        
        Args:
            region: Region identifier
            radius: Optional search radius in meters (overrides config)
            
        Returns:
            GeoJSON feature collection with proximity data and competitor metrics
        """
        radius = radius or self.proximity_radius
        cache_key = f"competitor_proximity:{region}:{radius}"

        if cached := await self.cache.get(cache_key):
            CACHE_HIT_RATE.labels("proximity").observe(1.0)
            return cached

        CACHE_HIT_RATE.labels("proximity").observe(0.0)

        try:
            with QUERY_TIME.labels("proximity").time():
                # Use CTE for efficient spatial joins
                query = text("""
                    WITH our_leads AS (
                        SELECT 
                            id,
                            location,
                            ST_Buffer(location::geography, :radius)::geometry as search_area
                        FROM leads
                        WHERE region = :region 
                        AND NOT is_competitor
                    ),
                    proximity_analysis AS (
                        SELECT 
                            ol.id as lead_id,
                            ST_AsGeoJSON(ol.location) as lead_location,
                            COUNT(c.id) as competitor_count,
                            MIN(ST_Distance(
                                ol.location::geography, 
                                c.location::geography
                            )) as nearest_distance,
                            array_agg(json_build_object(
                                'id', c.id,
                                'location', ST_AsGeoJSON(c.location),
                                'distance', ST_Distance(
                                    ol.location::geography,
                                    c.location::geography
                                )
                            )) as competitors
                        FROM our_leads ol
                        LEFT JOIN leads c ON ST_Intersects(ol.search_area, c.location)
                        WHERE c.is_competitor
                        GROUP BY ol.id, ol.location
                    )
                    SELECT
                        lead_id,
                        lead_location,
                        competitor_count,
                        nearest_distance,
                        competitors,
                        AVG(nearest_distance) OVER () as avg_distance,
                        STDDEV(nearest_distance) OVER () as std_distance,
                        MIN(nearest_distance) OVER () as min_distance,
                        MAX(nearest_distance) OVER () as max_distance
                    FROM proximity_analysis
                """)

                result = await self.session.execute(
                    query,
                    {
                        "region": region,
                        "radius": radius
                    }
                )
                rows = result.fetchall()

                # Calculate competitive pressure scores
                features = []
                for row in rows:
                    # Normalize distance scores
                    distance_score = 1.0
                    if row.std_distance:
                        normalized_dist = (row.nearest_distance - row.min_distance) / row.std_distance
                        distance_score = 1.0 / (1.0 + normalized_dist)

                    competitors = json.loads(row.competitors) if row.competitors else []
                    features.append({
                        "coordinates": json.loads(row.lead_location),
                        "properties": {
                            "lead_id": row.lead_id,
                            "competitor_count": row.competitor_count,
                            "nearest_distance": float(row.nearest_distance) if row.nearest_distance else None,
                            "distance_score": float(distance_score),
                            "competitors": competitors
                        }
                    })

                analysis_data = self._format_geojson(features, "Point")

                await self.cache.set(
                    cache_key,
                    analysis_data,
                    expire=self.cache_ttl
                )
                return analysis_data

        except Exception as e:
            logger.error(
                f"Failed to generate competitor proximity analysis: {str(e)}", 
                exc_info=True
            )
            raise
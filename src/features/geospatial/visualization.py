from typing import List, Dict, Any
from geoalchemy2 import Geography
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from src.models.lead import Lead
from src.cache import RedisCache
from src.monitoring import monitor

class GeospatialVisualizer:
    """
    Generates geospatial visualizations for lead data analysis.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        cache: RedisCache,
        cache_ttl: int = 3600  # 1 hour
    ):
        self.session = session
        self.cache = cache
        self.cache_ttl = cache_ttl
    
    @monitor(metric_name="geospatial_heatmap_generation")
    async def generate_density_heatmap(
        self,
        region: str,
        grid_size: float = 1000  # 1km grid
    ) -> Dict[str, Any]:
        """Generate heatmap data for lead density."""
        cache_key = f"heatmap:{region}:{grid_size}"
        
        if cached := await self.cache.get(cache_key):
            return cached
            
        query = select([
            func.ST_SnapToGrid(Lead.location, grid_size).label('cell'),
            func.count().label('count')
        ]).where(
            Lead.region == region
        ).group_by('cell')
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        heatmap_data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': json.loads(row.cell),
                'properties': {
                    'count': row.count
                }
            } for row in rows]
        }
        
        await self.cache.set(cache_key, heatmap_data, expire=self.cache_ttl)
        return heatmap_data
    
    @monitor(metric_name="geospatial_cluster_generation")    
    async def generate_cluster_visualization(
        self,
        region: str,
        eps: float = 5000,  # 5km
        min_points: int = 5
    ) -> Dict[str, Any]:
        """Generate cluster visualization data."""
        cache_key = f"clusters:{region}:{eps}:{min_points}"
        
        if cached := await self.cache.get(cache_key):
            return cached
            
        query = select([
            Lead.location,
            func.ST_ClusterDBSCAN(
                Lead.location,
                eps=eps,
                minpoints=min_points
            ).over().label('cluster_id')
        ]).where(Lead.region == region)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        clusters = {}
        for row in rows:
            cluster_id = row.cluster_id if row.cluster_id is not None else -1
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(json.loads(row.location))
        
        visualization_data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'MultiPoint',
                    'coordinates': points
                },
                'properties': {
                    'cluster_id': cluster_id
                }
            } for cluster_id, points in clusters.items()]
        }
        
        await self.cache.set(cache_key, visualization_data, expire=self.cache_ttl)
        return visualization_data
    
    @monitor(metric_name="geospatial_choropleth_generation")
    async def generate_market_penetration_choropleth(
        self,
        region: str,
        subdivision_level: str = 'district'  # or 'neighborhood', 'zip_code'
    ) -> Dict[str, Any]:
        """Generate choropleth map data for market penetration."""
        cache_key = f"choropleth:{region}:{subdivision_level}"
        
        if cached := await self.cache.get(cache_key):
            return cached
            
        query = select([
            Lead.subdivision[subdivision_level].label('area'),
            func.count().filter(Lead.is_competitor == False).label('our_leads'),
            func.count().label('total_leads')
        ]).where(
            Lead.region == region
        ).group_by('area')
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        choropleth_data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {
                    'area': row.area,
                    'penetration': row.our_leads / row.total_leads if row.total_leads > 0 else 0,
                    'total_leads': row.total_leads,
                    'our_leads': row.our_leads
                }
            } for row in rows]
        }
        
        await self.cache.set(cache_key, choropleth_data, expire=self.cache_ttl)
        return choropleth_data
    
    @monitor(metric_name="geospatial_proximity_generation")
    async def generate_competitor_proximity_analysis(
        self,
        region: str,
        radius: float = 5000  # 5km radius
    ) -> Dict[str, Any]:
        """Generate competitor proximity analysis visualization."""
        cache_key = f"competitor_proximity:{region}:{radius}"
        
        if cached := await self.cache.get(cache_key):
            return cached
            
        # First get our leads
        our_leads_query = select([
            Lead.location,
            Lead.id
        ]).where(
            Lead.region == region,
            Lead.is_competitor == False
        )
        
        our_leads = await self.session.execute(our_leads_query)
        
        # For each lead, find nearby competitors
        proximity_data = []
        for lead in our_leads:
            nearby_query = select([
                Lead.location,
                func.ST_Distance(Lead.location, lead.location).label('distance')
            ]).where(
                Lead.region == region,
                Lead.is_competitor == True,
                func.ST_DWithin(Lead.location, lead.location, radius)
            ).order_by('distance')
            
            nearby = await self.session.execute(nearby_query)
            
            proximity_data.append({
                'lead_id': lead.id,
                'location': json.loads(lead.location),
                'competitors': [{
                    'location': json.loads(comp.location),
                    'distance': float(comp.distance)
                } for comp in nearby]
            })
        
        analysis_data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': data['location']
                },
                'properties': {
                    'lead_id': data['lead_id'],
                    'competitor_count': len(data['competitors']),
                    'nearest_distance': min([c['distance'] for c in data['competitors']], default=None),
                    'competitors': data['competitors']
                }
            } for data in proximity_data]
        }
        
        await self.cache.set(cache_key, analysis_data, expire=self.cache_ttl)
        return analysis_data
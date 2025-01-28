from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from geoalchemy2 import Geography
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.features.base import BaseFeatureExtractor
from src.models.lead import Lead
from src.cache import RedisCache
from src.monitoring import monitor

class GeospatialFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts geospatial features from lead data using PostGIS.
    
    Features extracted:
    - location_cluster: Assigned cluster based on DBSCAN
    - nearest_competitor_distance: Distance to nearest competitor
    - location_density: Number of leads within 5km radius
    - market_penetration: Market share within region
    - geographic_spread: Standard deviation of distances
    """
    
    def __init__(
        self,
        session: AsyncSession,
        cache: RedisCache,
        cluster_distance: float = 5000,  # 5km
        min_cluster_size: int = 5
    ):
        super().__init__(session, cache)
        self.cluster_distance = cluster_distance
        self.min_cluster_size = min_cluster_size
        
    @monitor(metric_name="geospatial_feature_extraction")
    async def extract_features(self, lead: Lead) -> Dict[str, float]:
        """Extract geospatial features for a given lead."""
        cache_key = f"geo_features:{lead.id}"
        
        # Check cache first
        if cached := await self.cache.get(cache_key):
            return cached
            
        features = {}
        
        # Run feature extractions concurrently
        tasks = [
            self._extract_location_cluster(lead),
            self._extract_nearest_competitor(lead),
            self._extract_location_density(lead),
            self._extract_market_penetration(lead),
            self._extract_geographic_spread(lead)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Combine results
        for result in results:
            features.update(result)
            
        # Cache results
        await self.cache.set(
            cache_key,
            features,
            expire=3600  # 1 hour cache
        )
        
        return features
        
    async def _extract_location_cluster(self, lead: Lead) -> Dict[str, float]:
        """Extract location cluster using DBSCAN."""
        query = select(func.ST_ClusterDBSCAN(
            Lead.location,
            eps=self.cluster_distance,
            minpoints=self.min_cluster_size
        )).where(Lead.location.ST_DWithin(
            lead.location,
            self.cluster_distance * 2
        ))
        
        result = await self.session.execute(query)
        cluster_id = result.scalar()
        
        return {"location_cluster": float(cluster_id) if cluster_id is not None else -1.0}
        
    async def _extract_nearest_competitor(self, lead: Lead) -> Dict[str, float]:
        """Find distance to nearest competitor."""
        query = select(
            func.MIN(
                func.ST_Distance(Lead.location, lead.location)
            )
        ).where(
            Lead.is_competitor == True,
            Lead.id != lead.id
        )
        
        result = await self.session.execute(query)
        distance = result.scalar()
        
        return {"nearest_competitor_distance": float(distance) if distance else -1.0}
        
    async def _extract_location_density(self, lead: Lead) -> Dict[str, float]:
        """Calculate number of leads within 5km radius."""
        query = select(func.COUNT()).where(
            Lead.location.ST_DWithin(
                lead.location,
                5000  # 5km radius
            )
        )
        
        result = await self.session.execute(query)
        count = result.scalar()
        
        return {"location_density": float(count)}
        
    async def _extract_market_penetration(self, lead: Lead) -> Dict[str, float]:
        """Calculate market penetration in the region."""
        # Get total leads in region
        region_query = select(func.COUNT()).where(
            Lead.region == lead.region
        )
        
        # Get our leads in region
        our_leads_query = select(func.COUNT()).where(
            Lead.region == lead.region,
            Lead.is_competitor == False
        )
        
        total, our_leads = await asyncio.gather(
            self.session.execute(region_query),
            self.session.execute(our_leads_query)
        )
        
        total = total.scalar() or 0
        our_leads = our_leads.scalar() or 0
        
        penetration = our_leads / total if total > 0 else 0
        return {"market_penetration": float(penetration)}
        
    async def _extract_geographic_spread(self, lead: Lead) -> Dict[str, float]:
        """Calculate geographic spread of leads in region."""
        query = select(
            func.ST_StandardDeviationSpheric(Lead.location)
        ).where(
            Lead.region == lead.region
        )
        
        result = await self.session.execute(query)
        spread = result.scalar()
        
        return {"geographic_spread": float(spread) if spread else 0.0}

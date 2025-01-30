from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint, ST_Buffer, ST_Intersection, ST_Area, ST_DWithin
from .base import BaseFeatureExtractor
from ..models import Lead, Market
from ..exceptions import FeatureExtractionError
from ..utils.metrics import track_timing
from ..utils.cache import batch_cache
from ..config import settings

@dataclass
class GeospatialContext:
    """Validated geospatial context container."""
    location: Tuple[float, float]
    market_id: int
    radius_km: float = settings.DEFAULT_GEO_RADIUS_KM
    timestamp: datetime = None

    def __post_init__(self):
        if not (-90 <= self.location[0] <= 90) or not (-180 <= self.location[1] <= 180):
            raise ValueError("Invalid geographic coordinates")

class GeospatialFeatureExtractor(BaseFeatureExtractor):
    """Production-optimized geospatial feature extractor with batch processing."""

    _market_cache: Dict[int, Dict] = {}
    BATCH_CONCURRENCY = settings.GEO_BATCH_CONCURRENCY

    def __init__(
        self,
        session: AsyncSession,
        cache_ttl: int = settings.GEO_CACHE_TTL,
        batch_size: int = settings.GEO_BATCH_SIZE
    ):
        super().__init__(name="geospatial_features")
        self.session = session
        self.cache_ttl = cache_ttl
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(self.BATCH_CONCURRENCY)

    @batch_cache(ttl_seconds=3600, batch_key="market_id", geo_precision=3)
    async def extract_features(self, lead: Lead) -> Dict[str, float]:
        """Extract features with batch-optimized spatial queries."""
        try:
            context = await self._build_context(lead)
            return {
                **await self._core_features(context),
                **await self._market_features(context)
            }
        except Exception as e:
            self._log_error(lead.id, str(e))
            return self._feature_defaults()

    async def _core_features(self, context: GeospatialContext) -> Dict[str, float]:
        """Core features optimized for spatial index performance."""
        point = self._create_geo_point(context)
        radius_meters = context.radius_km * 1000

        # Parallel execution for fast batch queries
        distance_task = self._market_distance(context.market_id, point)
        density_task = self._nearby_density(point, radius_meters)
        
        distance, count = await asyncio.gather(distance_task, density_task)
        
        return {
            'distance_to_market_center': distance,
            'nearby_leads_count': count,
            'area_density': count / (3.14159 * (context.radius_km ** 2)) if context.radius_km > 0 else 0
        }

    async def _market_features(self, context: GeospatialContext) -> Dict[str, float]:
        """Market-specific features with caching and preloading."""
        market_data = await self._get_market_data(context.market_id)
        coverage = await self._calculate_coverage(context, market_data['boundary'])
        return {
            'market_coverage': coverage,
            'market_avg_density': market_data['avg_density']
        }

    @track_timing("geo_context")
    async def _build_context(self, lead: Lead) -> GeospatialContext:
        """Build validated geospatial context."""
        return GeospatialContext(
            location=(lead.latitude, lead.longitude),
            market_id=lead.market_id,
            timestamp=lead.created_at
        )

    async def _get_market_data(self, market_id: int) -> Dict:
        """Load market data with caching."""
        if market_id not in self._market_cache:
            market = await self.session.get(Market, market_id)
            self._market_cache[market_id] = {
                'boundary': market.boundary,
                'center': market.center_point,
                'avg_density': await self._calculate_market_density(market)
            }
        return self._market_cache[market_id]

    async def _calculate_market_density(self, market: Market) -> float:
        """Compute market density with spatial calculations."""
        if not market.boundary:
            return 0.0
            
        area = await self.session.scalar(
            select(ST_Area(market.boundary.cast(Geography), True))
        )
        return market.lead_count / (area / 1e6) if area > 0 else 0.0  # Convert to km²

    async def _market_distance(self, market_id: int, point: Geography) -> float:
        """Calculate distance to market center using geography."""
        market_center = await self.session.scalar(
            select(Market.center_point.cast(Geography)).where(Market.id == market_id)
        )
        return (await self.session.scalar(
            select(func.ST_Distance(point, market_center))
        )) / 1000  # Convert meters to km

    async def _nearby_density(self, point: Geography, radius_meters: float) -> int:
        """Compute nearby lead density using spatial index."""
        return await self.session.scalar(
            select(func.count()).where(
                ST_DWithin(
                    Lead.geolocation.cast(Geography),
                    point,
                    radius_meters
                )
            )
        )

    async def _calculate_coverage(self, context: GeospatialContext, boundary: Geography) -> float:
        """Calculate market coverage percentage."""
        if not boundary:
            return 0.0

        buffer = ST_Buffer(
            self._create_geo_point(context).cast(Geography),
            context.radius_km * 1000
        )
        return await self.session.scalar(
            select(
                ST_Area(ST_Intersection(buffer, boundary).cast(Geography), True) /
                ST_Area(boundary, True)
            )
        ) or 0.0

    def _create_geo_point(self, context: GeospatialContext) -> Geography:
        """Helper function to create a valid geography point."""
        return ST_SetSRID(ST_MakePoint(context.location[1], context.location[0]), 4326).cast(Geography)

    async def process_batch(self, leads: List[Lead]) -> List[Dict[str, float]]:
        """Batch process leads using concurrent execution."""
        results = []
        for i in range(0, len(leads), self.batch_size):
            async with self.semaphore:
                batch_results = await asyncio.gather(*[
                    self._safe_extract(lead) 
                    for lead in leads[i:i+self.batch_size]
                ])
                results.extend(batch_results)
        return results

    async def _safe_extract(self, lead: Lead) -> Dict[str, float]:
        """Safe extraction with error handling."""
        try:
            return await self.extract_features(lead)
        except Exception as e:
            self._log_error(lead.id, str(e))
            return self._feature_defaults()

    def _feature_defaults(self) -> Dict[str, float]:
        """Default values for failed feature extractions."""
        return {
            'distance_to_market_center': -1.0,
            'nearby_leads_count': 0,
            'area_density': 0.0,
            'market_coverage': 0.0,
            'market_avg_density': 0.0
        }

    def _log_error(self, lead_id: int, error: str):
        """Centralized error logging."""
        logger.error(f"Feature extraction failed for lead {lead_id}: {error}")
        # Add metrics tracking here

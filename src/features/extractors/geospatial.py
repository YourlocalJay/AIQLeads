from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint, ST_Buffer, ST_Intersection, ST_Area
from .base import BaseFeatureExtractor
from ..models import Lead, Market
from ..exceptions import FeatureExtractionError
from ..utils.metrics import track_timing
from ..utils.cache import redis_cache

@dataclass
class GeospatialContext:
    """Container for geospatial context information."""
    location: Tuple[float, float]  # (latitude, longitude)
    market_id: int
    radius_km: float = 5.0
    timestamp: datetime = None

class GeospatialFeatureExtractor(BaseFeatureExtractor):
    """Extracts geospatial features for lead analysis using PostGIS."""

    def __init__(
        self,
        session: AsyncSession,
        cache_ttl: int = 3600,
        batch_size: int = 100
    ):
        """Initialize the GeospatialFeatureExtractor.

        Args:
            session: AsyncSession for database operations
            cache_ttl: Cache time-to-live in seconds
            batch_size: Size of batches for bulk operations
        """
        super().__init__(name="geospatial_features")
        self.session = session
        self.cache_ttl = cache_ttl
        self.batch_size = batch_size

    @redis_cache(ttl_seconds=3600, prefix="geo_features")
    async def extract_features(self, lead: Lead) -> Dict[str, float]:
        """Extract geospatial features for a lead.

        Features extracted:
        - distance_to_market_center: Distance to market center in km
        - nearby_leads_count: Number of leads within radius
        - area_density: Lead density per square km
        - market_coverage: Percentage of market area covered

        Args:
            lead: Lead object containing location data

        Returns:
            Dictionary of extracted features

        Raises:
            FeatureExtractionError: If feature extraction fails
        """
        try:
            context = await self._build_context(lead)
            features = {}

            # Extract core geospatial features
            features.update(await self._extract_distance_features(context))
            features.update(await self._extract_density_features(context))
            features.update(await self._extract_coverage_features(context))

            return features

        except Exception as e:
            raise FeatureExtractionError(
                f"Failed to extract geospatial features: {str(e)}"
            ) from e

    @track_timing("geo_context_build")
    async def _build_context(self, lead: Lead) -> GeospatialContext:
        """Build geospatial context for feature extraction."""
        return GeospatialContext(
            location=(lead.latitude, lead.longitude),
            market_id=lead.market_id,
            timestamp=lead.created_at
        )

    async def _extract_distance_features(
        self,
        context: GeospatialContext
    ) -> Dict[str, float]:
        """Extract distance-based features."""
        query = select([
            func.ST_Distance(
                ST_SetSRID(ST_MakePoint(context.location[1], context.location[0]), 4326),
                Market.center_point
            ).label('distance_to_center')
        ]).where(Market.id == context.market_id)

        result = await self.session.execute(query)
        row = result.fetchone()

        return {
            'distance_to_market_center': float(row.distance_to_center) if row else -1.0
        }

    async def _extract_density_features(
        self,
        context: GeospatialContext
    ) -> Dict[str, float]:
        """Extract density-based features."""
        point = ST_SetSRID(ST_MakePoint(context.location[1], context.location[0]), 4326)
        buffer = ST_Buffer(point, context.radius_km / 111.32)

        query = select([func.count().label("nearby_leads_count")]).where(
            func.ST_Within(
                ST_SetSRID(ST_MakePoint(Lead.longitude, Lead.latitude), 4326),
                buffer
            )
        )

        result = await self.session.execute(query)
        nearby_count = result.scalar()

        area = 3.14159 * (context.radius_km ** 2)  # Circle area formula: pi * r^2

        return {
            'nearby_leads_count': nearby_count,
            'area_density': nearby_count / area if area > 0 else 0.0
        }

    async def _extract_coverage_features(
        self,
        context: GeospatialContext
    ) -> Dict[str, float]:
        """Extract market coverage features."""
        query = select([Market.boundary]).where(Market.id == context.market_id)
        result = await self.session.execute(query)
        market = result.fetchone()

        if not market or not market.boundary:
            return {'market_coverage': 0.0}

        point = ST_SetSRID(ST_MakePoint(context.location[1], context.location[0]), 4326)
        buffer = ST_Buffer(point, context.radius_km / 111.32)

        coverage_query = select([
            ST_Area(ST_Intersection(buffer, market.boundary)) /
            ST_Area(market.boundary)
        ])

        result = await self.session.execute(coverage_query)
        coverage = result.scalar()

        return {'market_coverage': float(coverage) if coverage else 0.0}

    async def process_batch(
        self,
        leads: List[Lead]
    ) -> List[Dict[str, float]]:
        """Process a batch of leads concurrently."""
        tasks = [self.extract_features(lead) for lead in leads]
        return await asyncio.gather(*tasks)

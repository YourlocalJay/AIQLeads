from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from geoalchemy2 import Geography
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
import numpy as np
from prometheus_client import Histogram

from src.features.base import BaseFeatureExtractor
from src.models.lead import Lead
from src.cache import RedisCache
from src.monitoring import monitor
from src.config.visualization import (
    DEFAULT_CLUSTER_RADIUS,
    MIN_CLUSTER_SIZE,
    DEFAULT_CACHE_TTL,
    PERFORMANCE_THRESHOLDS
)

# Performance monitoring metrics
FEATURE_EXTRACTION_TIME = Histogram(
    'geospatial_feature_extraction_seconds',
    'Time spent extracting geospatial features',
    ['feature_type']
)

class GeospatialFeatureExtractor(BaseFeatureExtractor):
    """
    Enhanced geospatial feature extractor with optimized performance and additional features.
    
    Features extracted:
    - location_cluster: Assigned cluster based on DBSCAN
    - nearest_competitor_distance: Distance to nearest competitor
    - location_density: Number of leads within a dynamic radius
    - market_penetration: Market share within the region
    - geographic_spread: Standard deviation of distances
    - temporal_density: Time-based density patterns
    - price_density: Price distribution in the area
    - competitor_influence: Weighted competitor impact
    """
    
    def __init__(
        self,
        session: AsyncSession,
        cache: RedisCache,
        cluster_distance: float = DEFAULT_CLUSTER_RADIUS,
        min_cluster_size: int = MIN_CLUSTER_SIZE,
        density_radius: float = 5000,
        cache_ttl: int = DEFAULT_CACHE_TTL
    ):
        super().__init__(session, cache)
        self.cluster_distance = cluster_distance
        self.min_cluster_size = min_cluster_size
        self.density_radius = density_radius
        self.cache_ttl = cache_ttl

    @monitor(metric_name="geospatial_feature_extraction")
    async def extract_features(
        self,
        lead: Lead,
        feature_types: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Extract geospatial features with selective processing and batch optimization.
        
        Args:
            lead: Lead object to analyze
            feature_types: Optional list of specific features to extract
        """
        cache_key = f"geo_features:{lead.id}:{':'.join(feature_types or [])}"
        
        # Check cache with version control
        if cached := await self.cache.get(cache_key):
            if cached.get('version') == self.FEATURE_VERSION:
                return cached['features']

        # Define feature extraction mapping
        extractors = {
            'location_cluster': self._extract_location_cluster,
            'nearest_competitor': self._extract_nearest_competitor,
            'location_density': self._extract_location_density,
            'market_penetration': self._extract_market_penetration,
            'geographic_spread': self._extract_geographic_spread,
            'temporal_density': self._extract_temporal_density,
            'price_density': self._extract_price_density,
            'competitor_influence': self._extract_competitor_influence
        }

        # Select features to extract
        selected_extractors = {
            name: func for name, func in extractors.items()
            if not feature_types or name in feature_types
        }

        # Run extractions concurrently with timing
        tasks = []
        for name, func in selected_extractors.items():
            with FEATURE_EXTRACTION_TIME.labels(feature_type=name).time():
                tasks.append(func(lead))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results and handle errors
        features = {}
        for name, result in zip(selected_extractors.keys(), results):
            if isinstance(result, Exception):
                self.logger.warning(f"Feature extraction error for {name}: {result}")
                features[name] = -1.0  # Default value for failed extractions
            else:
                features.update(result)

        # Cache with version control
        await self.cache.set(
            cache_key,
            {
                'version': self.FEATURE_VERSION,
                'features': features,
                'generated_at': datetime.utcnow().isoformat()
            },
            expire=self.cache_ttl
        )

        return features

    async def _extract_location_cluster(self, lead: Lead) -> Dict[str, float]:
        """Extract location cluster using optimized DBSCAN."""
        query = select([
            func.ST_ClusterDBSCAN(
                Lead.location,
                eps=self.cluster_distance,
                minpoints=self.min_cluster_size
            ).label('cluster_id'),
            func.count().label('cluster_size')
        ]).where(
            Lead.location.ST_DWithin(
                lead.location,
                self.cluster_distance * 2
            )
        ).group_by('cluster_id')

        result = await self.session.execute(query)
        clusters = result.fetchall()

        if not clusters:
            return {
                "location_cluster": -1.0,
                "cluster_size": 0.0,
                "cluster_density": 0.0
            }

        # Find the cluster containing our lead
        lead_cluster = None
        for cluster in clusters:
            point_query = select(func.count()).where(and_(
                Lead.location.ST_DWithin(lead.location, self.cluster_distance),
                Lead.cluster_id == cluster.cluster_id
            ))
            point_result = await self.session.execute(point_query)
            if point_result.scalar():
                lead_cluster = cluster
                break

        if not lead_cluster:
            return {
                "location_cluster": -1.0,
                "cluster_size": 0.0,
                "cluster_density": 0.0
            }

        # Calculate cluster density
        cluster_area = np.pi * (self.cluster_distance ** 2)
        cluster_density = lead_cluster.cluster_size / cluster_area

        return {
            "location_cluster": float(lead_cluster.cluster_id),
            "cluster_size": float(lead_cluster.cluster_size),
            "cluster_density": float(cluster_density)
        }

    async def _extract_competitor_influence(self, lead: Lead) -> Dict[str, float]:
        """Calculate weighted competitor influence in the area."""
        query = select([
            Lead.id,
            Lead.revenue,
            func.ST_Distance(Lead.location, lead.location).label('distance')
        ]).where(
            Lead.is_competitor == True,
            Lead.location.ST_DWithin(lead.location, self.density_radius)
        )

        result = await self.session.execute(query)
        competitors = result.fetchall()

        if not competitors:
            return {
                "competitor_influence": 0.0,
                "weighted_influence": 0.0
            }

        # Calculate influence scores
        total_influence = 0.0
        weighted_influence = 0.0

        for comp in competitors:
            # Inverse distance weighting
            distance_weight = 1 / (1 + comp.distance / 1000)  # Normalize to km
            revenue_weight = comp.revenue / 100000 if comp.revenue else 1.0
            
            influence = distance_weight * revenue_weight
            total_influence += influence
            weighted_influence += influence * (1 / len(competitors))

        return {
            "competitor_influence": float(total_influence),
            "weighted_influence": float(weighted_influence)
        }

    async def _extract_temporal_density(self, lead: Lead) -> Dict[str, float]:
        """Analyze temporal lead density patterns."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        query = select([
            func.date_trunc('day', Lead.created_at).label('day'),
            func.count().label('count')
        ]).where(
            Lead.location.ST_DWithin(lead.location, self.density_radius),
            Lead.created_at.between(start_date, end_date)
        ).group_by('day').order_by('day')

        result = await self.session.execute(query)
        daily_counts = result.fetchall()

        if not daily_counts:
            return {
                "temporal_density": 0.0,
                "density_trend": 0.0
            }

        # Calculate trend using simple linear regression
        x = np.arange(len(daily_counts))
        y = np.array([count.count for count in daily_counts])
        
        coefficients = np.polyfit(x, y, 1)
        trend = coefficients[0]  # Slope indicates trend

        avg_density = np.mean(y)

        return {
            "temporal_density": float(avg_density),
            "density_trend": float(trend)
        }

    async def _extract_price_density(self, lead: Lead) -> Dict[str, float]:
        """Analyze price distribution in the area."""
        query = select([
            func.avg(Lead.price).label('avg_price'),
            func.stddev(Lead.price).label('price_std'),
            func.percentile_cont(0.5).within_group(
                Lead.price.asc()
            ).label('median_price')
        ]).where(
            Lead.location.ST_DWithin(lead.location, self.density_radius),
            Lead.price.isnot(None)
        )

        result = await self.session.execute(query)
        price_stats = result.fetchone()

        if not price_stats or price_stats.avg_price is None:
            return {
                "price_density": 0.0,
                "price_variation": 0.0,
                "price_centrality": 0.0
            }

        # Calculate price density metrics
        price_density = price_stats.avg_price / self.density_radius
        price_variation = price_stats.price_std / price_stats.avg_price if price_stats.avg_price else 0
        price_centrality = abs(lead.price - price_stats.median_price) / price_stats.median_price if price_stats.median_price else 0

        return {
            "price_density": float(price_density),
            "price_variation": float(price_variation),
            "price_centrality": float(price_centrality)
        }
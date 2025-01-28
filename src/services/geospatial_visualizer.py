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

from typing import Dict, Any, List, Optional, TypedDict, Union, Literal
from geoalchemy2 import Geography
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import json
import logging
from prometheus_client import Histogram

from src.models.lead import Lead
from src.models.region import Region
from src.cache import RedisCache
from src.core.monitoring import monitor
from src.core.config import settings

# Type definitions
GeometryType = Literal["Point", "MultiPoint", "Polygon", "MultiPolygon"]
SubdivisionLevel = Literal["district", "city", "state"]

class VisualizationConfig(TypedDict, total=False):
    """Configuration options for visualizations"""
    cache_ttl: int  # Cache time-to-live in seconds
    grid_size: float  # Size of grid cells in meters
    cluster_eps: float  # DBSCAN epsilon parameter
    cluster_min_points: int  # DBSCAN minimum points
    proximity_radius: float  # Competitor proximity radius
    subdivision_level: SubdivisionLevel  # Geographic subdivision level

# Metrics
QUERY_TIME = Histogram(
    "geospatial_query_seconds",
    "Time spent executing geospatial queries",
    ["visualization_type"]
)
CACHE_HIT_RATE = Histogram(
    "geospatial_cache_hit_rate",
    "Cache hit rate for geospatial visualizations",
    ["visualization_type"]
)

logger = logging.getLogger(__name__)

class GeospatialVisualizer:
    """
    Generates geospatial visualizations for lead data analysis with proper GeoJSON 
    formatting and optimized queries.
    """

    def __init__(
        self,
        session: AsyncSession,
        cache: RedisCache,
        config: Optional[VisualizationConfig] = None
    ):
        """
        Initialize visualizer with database session and cache.
        
        Args:
            session: SQLAlchemy async session
            cache: Redis cache instance
            config: Optional configuration dictionary
        """
        self.session = session
        self.cache = cache
        self.config = config or {}
        
        # Cache settings
        self.cache_ttl = self.config.get("cache_ttl", settings.CACHE_TTL)
        
        # Visualization parameters
        self.grid_size = self.config.get("grid_size", settings.DEFAULT_GRID_SIZE)
        self.cluster_eps = self.config.get("cluster_eps", settings.DEFAULT_CLUSTER_EPS)
        self.cluster_min_points = self.config.get(
            "cluster_min_points", 
            settings.DEFAULT_CLUSTER_MIN_POINTS
        )
        self.proximity_radius = self.config.get(
            "proximity_radius",
            settings.DEFAULT_PROXIMITY_RADIUS
        )
        self.subdivision_level = self.config.get(
            "subdivision_level",
            settings.DEFAULT_SUBDIVISION_LEVEL
        )

    def _format_geojson(
        self,
        features: List[Dict[str, Any]],
        geometry_type: GeometryType
    ) -> Dict[str, Any]:
        """
        Format features as valid GeoJSON.
        
        Args:
            features: List of feature dictionaries
            geometry_type: Type of geometry for validation
            
        Returns:
            GeoJSON feature collection
        """
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": geometry_type,
                        "coordinates": feature["coordinates"]
                    },
                    "properties": feature["properties"]
                }
                for feature in features
                if feature.get("coordinates")
            ]
        }
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from geoalchemy2 import Geography
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json
import numpy as np
from prometheus_client import Histogram
from src.models.lead import Lead
from src.cache import RedisCache
from src.monitoring import monitor
from src.config import TILE_SIZE, MAX_ZOOM_LEVEL

# Monitoring metrics
VISUALIZATION_GENERATION_TIME = Histogram(
    'geospatial_visualization_generation_seconds',
    'Time spent generating visualization data',
    ['visualization_type', 'region']
)

CACHE_HIT_RATE = Histogram(
    'geospatial_cache_hit_rate',
    'Cache hit rate for geospatial queries',
    ['query_type']
)

class GeospatialVisualizer:
    """
    AI-powered geospatial visualization generator with optimized performance,
    batch processing, and predictive heatmap capabilities.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        cache: RedisCache,
        cache_ttl: int = 3600,  # 1 hour
        tile_size: int = TILE_SIZE,
        max_zoom: int = MAX_ZOOM_LEVEL
    ):
        self.session = session
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.tile_size = tile_size
        self.max_zoom = max_zoom

    async def _get_cached_or_compute(
        self,
        cache_key: str,
        compute_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Generic cache wrapper with monitoring."""
        query_type = cache_key.split(':')[0]
        
        if cached := await self.cache.get(cache_key):
            CACHE_HIT_RATE.labels(query_type=query_type).observe(1)
            return cached
            
        CACHE_HIT_RATE.labels(query_type=query_type).observe(0)
        result = await compute_func(*args, **kwargs)
        await self.cache.set(cache_key, result, expire=self.cache_ttl)
        return result

    @monitor(metric_name="geospatial_multi_layer")
    async def generate_multi_layer_visualization(
        self,
        region: str,
        layers: Set[str] = {'density', 'clusters', 'competitors'},
        filters: Dict[str, Any] = None,
        zoom_level: int = 12
    ) -> Dict[str, Any]:
        """
        Generate a multi-layer visualization combining different data types.
        
        Args:
            region: Geographic region
            layers: Set of layers to include
            filters: Optional filters to apply
            zoom_level: Map zoom level
        """
        tasks = []
        if 'density' in layers:
            tasks.append(self.generate_density_heatmap(region, filters, zoom_level))
        if 'clusters' in layers:
            tasks.append(self.generate_cluster_visualization(region, filters))
        if 'competitors' in layers:
            tasks.append(self.generate_competitor_proximity_analysis(region, filters))

        # Execute all visualization tasks concurrently
        results = await asyncio.gather(*tasks)
        
        return {
            'type': 'FeatureCollection',
            'layers': {layer: result for layer, result in zip(layers, results)},
            'metadata': {
                'region': region,
                'zoom_level': zoom_level,
                'filters': filters,
                'generated_at': datetime.utcnow().isoformat()
            }
        }

    @monitor(metric_name="geospatial_predictive_heatmap")
    async def generate_predictive_heatmap(
        self,
        region: str,
        prediction_window: int = 30,  # days
        confidence_threshold: float = 0.7,
        zoom_level: int = 12
    ) -> Dict[str, Any]:
        """
        Generate a predictive heatmap showing expected future density changes.
        """
        cache_key = f"predictive_heatmap:{region}:{prediction_window}:{confidence_threshold}:{zoom_level}"
        
        return await self._get_cached_or_compute(
            cache_key,
            self._compute_predictive_heatmap,
            region,
            prediction_window,
            confidence_threshold,
            zoom_level
        )

    async def _compute_predictive_heatmap(
        self,
        region: str,
        prediction_window: int,
        confidence_threshold: float,
        zoom_level: int
    ) -> Dict[str, Any]:
        """Compute predictive heatmap data."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=prediction_window * 2)
        
        query = select([
            func.ST_SnapToGrid(Lead.location, 1000).label('cell'),
            func.time_bucket('1 day', Lead.created_at).label('bucket'),
            func.count().label('count')
        ]).where(
            Lead.region == region,
            Lead.created_at.between(start_date, end_date)
        ).group_by('cell', 'bucket')
        
        result = await self.session.execute(query)
        historical_data = result.fetchall()
        
        # Process historical data into time series by cell
        cell_series = {}
        for row in historical_data:
            cell = json.loads(row.cell)
            cell_key = f"{cell['coordinates'][0]}:{cell['coordinates'][1]}"
            if cell_key not in cell_series:
                cell_series[cell_key] = []
            cell_series[cell_key].append({'date': row.bucket, 'count': row.count})
        
        # Generate predictions for each cell
        predictions = []
        for cell_key, series in cell_series.items():
            if len(series) < prediction_window:
                continue
                
            # Simple linear regression for prediction
            x = np.array(range(len(series)))
            y = np.array([point['count'] for point in series])
            
            coefficients = np.polyfit(x, y, 1)
            predicted_change = coefficients[0] * prediction_window
            
            # Calculate confidence based on R-squared
            y_pred = np.polyval(coefficients, x)
            r_squared = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
            
            if r_squared >= confidence_threshold:
                lon, lat = map(float, cell_key.split(':'))
                predictions.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                    'properties': {
                        'predicted_change': float(predicted_change),
                        'confidence': float(r_squared),
                        'current_density': series[-1]['count']
                    }
                })
        
        return {
            'type': 'FeatureCollection',
            'features': predictions,
            'metadata': {
                'prediction_window': prediction_window,
                'confidence_threshold': confidence_threshold,
                'predictions_generated': len(predictions),
                'generated_at': datetime.utcnow().isoformat()
            }
        }

    def _get_tile_coordinates(
        self,
        point: Dict[str, Any],
        zoom: int
    ) -> Tuple[int, int]:
        """Convert geographic coordinates to tile coordinates."""
        lon = point['coordinates'][0]
        lat = point['coordinates'][1]
        
        lat_rad = np.radians(lat)
        n = 2.0 ** zoom
        tile_x = int((lon + 180.0) / 360.0 * n)
        tile_y = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)
        
        return tile_x, tile_y

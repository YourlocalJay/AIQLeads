import pytest
from unittest.mock import AsyncMock, Mock
import json
from geoalchemy2.elements import WKTElement

from src.features.geospatial.visualization import GeospatialVisualizer
from src.cache import RedisCache

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_cache():
    return AsyncMock(spec=RedisCache)

@pytest.fixture
def visualizer(mock_session, mock_cache):
    return GeospatialVisualizer(
        session=mock_session,
        cache=mock_cache,
        cache_ttl=3600
    )

@pytest.fixture
def sample_point():
    return WKTElement('POINT(-73.935242 40.730610)', srid=4326)

@pytest.mark.asyncio
async def test_density_heatmap_cached(visualizer, mock_cache):
    """Test heatmap generation with cached data."""
    cached_data = {
        'type': 'FeatureCollection',
        'features': []
    }
    mock_cache.get.return_value = cached_data
    
    result = await visualizer.generate_density_heatmap('NYC')
    
    assert result == cached_data
    mock_cache.get.assert_called_once_with('heatmap:NYC:1000')
    mock_cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_density_heatmap_generation(visualizer, mock_session, mock_cache):
    """Test heatmap generation from database."""
    mock_cache.get.return_value = None
    mock_session.execute.return_value.fetchall.return_value = [
        Mock(cell='{"type":"Point","coordinates":[-73.935242,40.730610]}', count=5),
        Mock(cell='{"type":"Point","coordinates":[-73.940000,40.735000]}', count=3)
    ]
    
    result = await visualizer.generate_density_heatmap('NYC')
    
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 2
    assert result['features'][0]['properties']['count'] == 5
    mock_session.execute.assert_called_once()
    mock_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_cluster_visualization_cached(visualizer, mock_cache):
    """Test cluster visualization with cached data."""
    cached_data = {
        'type': 'FeatureCollection',
        'features': []
    }
    mock_cache.get.return_value = cached_data
    
    result = await visualizer.generate_cluster_visualization('NYC')
    
    assert result == cached_data
    mock_cache.get.assert_called_once_with('clusters:NYC:5000:5')
    mock_cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_cluster_visualization_generation(visualizer, mock_session, mock_cache, sample_point):
    """Test cluster visualization generation from database."""
    mock_cache.get.return_value = None
    mock_session.execute.return_value.fetchall.return_value = [
        Mock(location=sample_point, cluster_id=1),
        Mock(location=sample_point, cluster_id=1),
        Mock(location=sample_point, cluster_id=2)
    ]
    
    result = await visualizer.generate_cluster_visualization('NYC')
    
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 2  # Two clusters
    mock_session.execute.assert_called_once()
    mock_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_market_penetration_cached(visualizer, mock_cache):
    """Test market penetration visualization with cached data."""
    cached_data = {
        'type': 'FeatureCollection',
        'features': []
    }
    mock_cache.get.return_value = cached_data
    
    result = await visualizer.generate_market_penetration_choropleth('NYC')
    
    assert result == cached_data
    mock_cache.get.assert_called_once_with('choropleth:NYC:district')
    mock_cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_market_penetration_generation(visualizer, mock_session, mock_cache):
    """Test market penetration visualization generation from database."""
    mock_cache.get.return_value = None
    mock_session.execute.return_value.fetchall.return_value = [
        Mock(area='District A', our_leads=30, total_leads=100),
        Mock(area='District B', our_leads=20, total_leads=80)
    ]
    
    result = await visualizer.generate_market_penetration_choropleth('NYC')
    
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 2
    assert result['features'][0]['properties']['penetration'] == 0.3
    mock_session.execute.assert_called_once()
    mock_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_competitor_proximity_cached(visualizer, mock_cache):
    """Test competitor proximity analysis with cached data."""
    cached_data = {
        'type': 'FeatureCollection',
        'features': []
    }
    mock_cache.get.return_value = cached_data
    
    result = await visualizer.generate_competitor_proximity_analysis('NYC')
    
    assert result == cached_data
    mock_cache.get.assert_called_once_with('competitor_proximity:NYC:5000')
    mock_cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_competitor_proximity_generation(visualizer, mock_session, mock_cache, sample_point):
    """Test competitor proximity analysis generation from database."""
    mock_cache.get.return_value = None
    
    # Mock our leads query
    mock_session.execute.side_effect = [
        AsyncMock(return_value=[
            Mock(id=1, location=sample_point)
        ])(),
        # Mock nearby competitors query
        AsyncMock(return_value=[
            Mock(location=sample_point, distance=1000),
            Mock(location=sample_point, distance=2000)
        ])()
    ]
    
    result = await visualizer.generate_competitor_proximity_analysis('NYC')
    
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 1
    assert result['features'][0]['properties']['competitor_count'] == 2
    assert result['features'][0]['properties']['nearest_distance'] == 1000
    assert mock_session.execute.call_count == 2
    mock_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling_database(visualizer, mock_session, mock_cache):
    """Test error handling for database errors."""
    mock_cache.get.return_value = None
    mock_session.execute.side_effect = Exception("Database error")
    
    with pytest.raises(Exception) as exc_info:
        await visualizer.generate_density_heatmap('NYC')
    assert str(exc_info.value) == "Database error"

@pytest.mark.asyncio
async def test_error_handling_cache(visualizer, mock_cache):
    """Test error handling for cache errors."""
    mock_cache.get.side_effect = Exception("Cache error")
    
    with pytest.raises(Exception) as exc_info:
        await visualizer.generate_density_heatmap('NYC')
    assert str(exc_info.value) == "Cache error"

@pytest.mark.asyncio
async def test_empty_results_handling(visualizer, mock_session, mock_cache):
    """Test handling of empty result sets."""
    mock_cache.get.return_value = None
    mock_session.execute.return_value.fetchall.return_value = []
    
    result = await visualizer.generate_density_heatmap('NYC')
    
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 0
    mock_session.execute.assert_called_once()
    mock_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_invalid_region_handling(visualizer, mock_session, mock_cache):
    """Test handling of invalid region queries."""
    mock_cache.get.return_value = None
    mock_session.execute.return_value.fetchall.return_value = []
    
    result = await visualizer.generate_density_heatmap('INVALID_REGION')
    
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 0
    mock_session.execute.assert_called_once()
    mock_cache.set.assert_called_once()

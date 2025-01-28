import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from src.features.geospatial.extractor import GeospatialFeatureExtractor
from src.models.lead import Lead
from src.cache import RedisCache

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_cache():
    return AsyncMock(spec=RedisCache)

@pytest.fixture
def mock_lead():
    return Mock(
        id=1,
        location=WKTElement('POINT(-73.935242 40.730610)', srid=4326),
        region="NYC",
        created_at=datetime.now(),
        is_competitor=False
    )

@pytest.fixture
def extractor(mock_session, mock_cache):
    return GeospatialFeatureExtractor(
        session=mock_session,
        cache=mock_cache,
        cluster_distance=5000,
        min_cluster_size=5
    )

@pytest.mark.asyncio
async def test_cached_features(extractor, mock_lead, mock_cache):
    """Test that cached features are returned when available."""
    cached_features = {
        "location_cluster": 1.0,
        "nearest_competitor_distance": 1000.0,
        "location_density": 15.0,
        "market_penetration": 0.45,
        "geographic_spread": 2500.0
    }
    mock_cache.get.return_value = cached_features
    
    result = await extractor.extract_features(mock_lead)
    
    assert result == cached_features
    mock_cache.get.assert_called_once_with(f"geo_features:{mock_lead.id}")
    mock_cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_location_cluster_extraction(extractor, mock_lead, mock_session):
    """Test location cluster extraction."""
    mock_session.execute.return_value.scalar.return_value = 2
    
    result = await extractor._extract_location_cluster(mock_lead)
    
    assert result == {"location_cluster": 2.0}
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_nearest_competitor_extraction(extractor, mock_lead, mock_session):
    """Test nearest competitor distance extraction."""
    mock_session.execute.return_value.scalar.return_value = 1500.0
    
    result = await extractor._extract_nearest_competitor(mock_lead)
    
    assert result == {"nearest_competitor_distance": 1500.0}
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_location_density_extraction(extractor, mock_lead, mock_session):
    """Test location density extraction."""
    mock_session.execute.return_value.scalar.return_value = 25
    
    result = await extractor._extract_location_density(mock_lead)
    
    assert result == {"location_density": 25.0}
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_market_penetration_extraction(extractor, mock_lead, mock_session):
    """Test market penetration extraction."""
    mock_session.execute.side_effect = [
        AsyncMock(scalar=lambda: 100)(),  # Total leads
        AsyncMock(scalar=lambda: 40)()    # Our leads
    ]
    
    result = await extractor._extract_market_penetration(mock_lead)
    
    assert result == {"market_penetration": 0.4}
    assert mock_session.execute.call_count == 2

@pytest.mark.asyncio
async def test_geographic_spread_extraction(extractor, mock_lead, mock_session):
    """Test geographic spread extraction."""
    mock_session.execute.return_value.scalar.return_value = 3000.0
    
    result = await extractor._extract_geographic_spread(mock_lead)
    
    assert result == {"geographic_spread": 3000.0}
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_full_feature_extraction(extractor, mock_lead, mock_cache, mock_session):
    """Test full feature extraction process."""
    mock_cache.get.return_value = None
    mock_session.execute.side_effect = [
        AsyncMock(scalar=lambda: 1)(),      # Cluster
        AsyncMock(scalar=lambda: 1200.0)(),  # Competitor
        AsyncMock(scalar=lambda: 30)(),      # Density
        AsyncMock(scalar=lambda: 100)(),     # Total leads
        AsyncMock(scalar=lambda: 35)(),      # Our leads
        AsyncMock(scalar=lambda: 2800.0)()   # Spread
    ]
    
    expected_features = {
        "location_cluster": 1.0,
        "nearest_competitor_distance": 1200.0,
        "location_density": 30.0,
        "market_penetration": 0.35,
        "geographic_spread": 2800.0
    }
    
    result = await extractor.extract_features(mock_lead)
    
    assert result == expected_features
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_called_once()
    assert mock_session.execute.call_count == 6

@pytest.mark.asyncio
async def test_null_handling(extractor, mock_lead, mock_session):
    """Test handling of null/None values from database."""
    mock_session.execute.return_value.scalar.return_value = None
    
    result = await extractor._extract_nearest_competitor(mock_lead)
    
    assert result == {"nearest_competitor_distance": -1.0}
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(extractor, mock_lead, mock_session):
    """Test error handling during feature extraction."""
    mock_session.execute.side_effect = Exception("Database error")
    
    with pytest.raises(Exception):
        await extractor._extract_location_cluster(mock_lead)
    
    mock_session.execute.assert_called_once()
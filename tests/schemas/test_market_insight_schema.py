import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from src.schemas.market_insight_schema import (
    LocationPoint,
    MetricsBase,
    AnalysisParameters,
    MarketInsightCreate,
    MarketInsightUpdate,
    MarketInsightInDB,
    AnalysisType
)

@pytest.fixture
def valid_location_data():
    return {
        'longitude': -73.935242,
        'latitude': 40.730610
    }

@pytest.fixture
def valid_metrics_data():
    return {
        'price_range': [500000, 1000000],
        'property_type': 'residential',
        'bedrooms': 3,
        'bathrooms': 2,
        'square_footage': 2000,
        'year_built': 2000
    }

@pytest.fixture
def valid_parameters_data():
    return {
        'radius_miles': 5.0,
        'min_confidence': 0.8,
        'include_pending': True,
        'time_window_days': 30,
        'grouping': 'monthly',
        'filters': {'property_type': ['house', 'condo']}
    }

@pytest.fixture
def valid_insight_data(valid_location_data, valid_metrics_data, valid_parameters_data):
    return {
        'location': valid_location_data,
        'date_range': [
            datetime.utcnow() - timedelta(days=30),
            datetime.utcnow()
        ],
        'metrics': valid_metrics_data,
        'analysis_type': AnalysisType.TREND,
        'parameters': valid_parameters_data,
        'tags': ['residential', 'trending', 'nyc']
    }

def test_valid_location_point(valid_location_data):
    """Test valid location point data"""
    location = LocationPoint(**valid_location_data)
    assert location.longitude == valid_location_data['longitude']
    assert location.latitude == valid_location_data['latitude']

def test_invalid_location_point():
    """Test invalid location coordinates"""
    invalid_data = [
        {'longitude': 181, 'latitude': 0},  # Invalid longitude
        {'longitude': 0, 'latitude': 91},    # Invalid latitude
        {'longitude': 'invalid', 'latitude': 0}  # Invalid type
    ]
    
    for data in invalid_data:
        with pytest.raises(ValidationError):
            LocationPoint(**data)

def test_valid_metrics_base(valid_metrics_data):
    """Test valid metrics data"""
    metrics = MetricsBase(**valid_metrics_data)
    assert metrics.price_range == valid_metrics_data['price_range']
    assert metrics.property_type == valid_metrics_data['property_type']
    assert metrics.bedrooms == valid_metrics_data['bedrooms']

def test_invalid_metrics_base():
    """Test invalid metrics data"""
    invalid_data = [
        {'price_range': [100000], 'property_type': 'residential'},  # Invalid price range length
        {'price_range': [-100, 100], 'property_type': 'residential'},  # Negative price
        {'price_range': [100, 200], 'property_type': '', 'bedrooms': -1}  # Invalid bedroom count
    ]
    
    for data in invalid_data:
        with pytest.raises(ValidationError):
            MetricsBase(**data)

def test_valid_analysis_parameters(valid_parameters_data):
    """Test valid analysis parameters"""
    params = AnalysisParameters(**valid_parameters_data)
    assert params.radius_miles == valid_parameters_data['radius_miles']
    assert params.min_confidence == valid_parameters_data['min_confidence']
    assert params.time_window_days == valid_parameters_data['time_window_days']

def test_invalid_analysis_parameters():
    """Test invalid analysis parameters"""
    invalid_data = [
        {'radius_miles': 0, 'min_confidence': 0.5, 'time_window_days': 30},  # Invalid radius
        {'radius_miles': 5, 'min_confidence': 1.5, 'time_window_days': 30},  # Invalid confidence
        {'radius_miles': 5, 'min_confidence': 0.5, 'time_window_days': 0}   # Invalid time window
    ]
    
    for data in invalid_data:
        with pytest.raises(ValidationError):
            AnalysisParameters(**data)

def test_valid_market_insight_create(valid_insight_data):
    """Test creating valid market insight"""
    insight = MarketInsightCreate(**valid_insight_data)
    assert insight.location.longitude == valid_insight_data['location']['longitude']
    assert insight.metrics.property_type == valid_insight_data['metrics']['property_type']
    assert insight.analysis_type == valid_insight_data['analysis_type']

def test_invalid_market_insight_create(valid_insight_data):
    """Test invalid market insight creation"""
    # Test invalid date range
    invalid_data = valid_insight_data.copy()
    invalid_data['date_range'] = [datetime.utcnow(), datetime.utcnow() - timedelta(days=1)]
    with pytest.raises(ValidationError):
        MarketInsightCreate(**invalid_data)
    
    # Test future start date
    invalid_data['date_range'] = [
        datetime.utcnow() + timedelta(days=1),
        datetime.utcnow() + timedelta(days=2)
    ]
    with pytest.raises(ValidationError):
        MarketInsightCreate(**invalid_data)

def test_market_insight_update():
    """Test market insight update validation"""
    valid_update = {
        'metrics': {'price_range': [600000, 1200000], 'property_type': 'residential'},
        'confidence_score': 0.95,
        'tags': ['updated', 'premium']
    }
    update = MarketInsightUpdate(**valid_update)
    assert update.confidence_score == valid_update['confidence_score']
    assert update.tags == valid_update['tags']

def test_market_insight_in_db(valid_insight_data):
    """Test market insight database model"""
    db_data = {
        **valid_insight_data,
        'id': 1,
        'user_id': 1,
        'results': {'avg_price': 750000},
        'confidence_score': 0.85,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    insight = MarketInsightInDB(**db_data)
    assert insight.id == db_data['id']
    assert insight.user_id == db_data['user_id']
    assert insight.results == db_data['results']
    assert insight.confidence_score == db_data['confidence_score']
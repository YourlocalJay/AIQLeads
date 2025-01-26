import pytest
from src.aggregator.parsers.facebook_parser import FacebookParser
from src.models.lead import Lead
from datetime import datetime

@pytest.fixture
def facebook_parser():
    return FacebookParser()

@pytest.fixture
def sample_facebook_data():
    return {
        "listing": {
            "location": {
                "address": "456 Market St, City, State 12345",
                "coordinates": {
                    "latitude": 37.7749,
                    "longitude": -122.4194
                }
            },
            "price": {
                "amount": 750000,
                "currency": "USD"
            },
            "propertyDetails": {
                "bedrooms": 4,
                "bathrooms": 3,
                "squareFeet": 2500,
                "yearBuilt": 1995
            },
            "listingDate": "2025-01-20T15:30:00Z"
        }
    }

def test_parse_valid_listing(facebook_parser, sample_facebook_data):
    """Test parsing of a valid Facebook Marketplace listing"""
    lead = facebook_parser.parse(sample_facebook_data)
    
    assert isinstance(lead, Lead)
    assert lead.address == "456 Market St, City, State 12345"
    assert lead.price == 750000
    assert lead.bedrooms == 4
    assert lead.bathrooms == 3
    assert lead.square_feet == 2500
    assert lead.year_built == 1995
    assert lead.source == "facebook"
    assert lead.latitude == 37.7749
    assert lead.longitude == -122.4194
    assert isinstance(lead.created_at, datetime)

def test_handle_nested_missing_fields(facebook_parser):
    """Test handling of missing nested fields"""
    partial_data = {
        "listing": {
            "location": {
                "address": "456 Market St"
            },
            "price": {
                "amount": 750000
            }
        }
    }
    
    lead = facebook_parser.parse(partial_data)
    assert lead.address == "456 Market St"
    assert lead.price == 750000
    assert lead.bedrooms is None
    assert lead.latitude is None

def test_handle_malformed_data(facebook_parser):
    """Test handling of malformed data structure"""
    invalid_data = {
        "listing": "malformed_string_instead_of_object"
    }
    
    with pytest.raises(ValueError):
        facebook_parser.parse(invalid_data)

def test_price_currency_conversion(facebook_parser):
    """Test handling of different currencies"""
    data_with_different_currency = {
        "listing": {
            "location": {"address": "Test Address"},
            "price": {
                "amount": 1000000,
                "currency": "CAD"
            }
        }
    }
    
    lead = facebook_parser.parse(data_with_different_currency)
    assert lead.price is not None
    assert isinstance(lead.price, (int, float))
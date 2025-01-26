"""
Test suite for the Facebook Marketplace parser implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.facebook_parser import FacebookParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate

@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return FacebookParser()

@pytest.fixture
def valid_listing_data():
    """Provide sample valid listing data."""
    return {
        "id": "fb-123456789",
        "listing": {
            "price": {
                "amount": 425000,
                "currency": "USD"
            },
            "propertyType": "House",
            "datePosted": "2025-01-20T15:30:00Z",
            "location": {
                "latitude": 33.4484,
                "longitude": -112.0740,
                "address": {
                    "city": "Phoenix",
                    "state": "AZ",
                    "zipCode": "85001"
                }
            },
            "seller": {
                "name": "Alice Johnson",
                "id": "fb-seller-123",
                "contactInfo": {
                    "phone": "555-0123",
                    "email": "alice.j@email.com"
                }
            }
        },
        "engagement": {
            "views": 150,
            "saves": 25,
            "inquiries": 10
        }
    }

@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid Facebook Marketplace listing."""
    result = await parser.parse_async(valid_listing_data)
    
    assert isinstance(result, LeadCreate)
    assert result.source_id == "fb-123456789"
    assert result.market == "facebook"
    assert result.contact_name == "Alice Johnson"
    assert result.email == "alice.j@email.com"
    assert result.phone == "555-0123"
    assert isinstance(result.metadata, dict)
    assert result.metadata["property_type"] == "House"
    assert result.metadata["price"] == 425000
    assert result.metadata["engagement_metrics"]["views"] == 150

@pytest.mark.asyncio
async def test_missing_price(parser, valid_listing_data):
    """Test handling of missing price information."""
    del valid_listing_data["listing"]["price"]
    
    with pytest.raises(ParseError, match="Missing or invalid price data"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_invalid_location(parser, valid_listing_data):
    """Test handling of invalid location data."""
    valid_listing_data["listing"]["location"]["latitude"] = None
    
    with pytest.raises(ParseError, match="Invalid location data"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_engagement_metrics(parser, valid_listing_data):
    """Test proper handling of engagement metrics."""
    result = await parser.parse_async(valid_listing_data)
    
    assert result.metadata["engagement_metrics"]["views"] == 150
    assert result.metadata["engagement_metrics"]["saves"] == 25
    assert result.metadata["engagement_metrics"]["inquiries"] == 10

@pytest.mark.asyncio
async def test_missing_seller_info(parser, valid_listing_data):
    """Test handling of missing seller information."""
    del valid_listing_data["listing"]["seller"]
    
    with pytest.raises(ParseError, match="Missing seller information"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_invalid_contact_info(parser, valid_listing_data):
    """Test handling of invalid contact information."""
    valid_listing_data["listing"]["seller"]["contactInfo"] = {
        "phone": "invalid-phone",
        "email": "invalid-email"
    }
    
    with pytest.raises(ParseError, match="No valid contact methods"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_location_extraction(parser):
    """Test proper extraction of location data."""
    location_data = {
        "listing": {
            "location": {
                "latitude": 33.4484,
                "longitude": -112.0740,
                "address": {
                    "city": "Phoenix",
                    "state": "AZ",
                    "zipCode": "85001"
                }
            }
        }
    }
    
    result = parser._extract_location(location_data["listing"])
    assert isinstance(result["coordinates"], WKTElement)
    assert result["coordinates"].data == "POINT(-112.0740 33.4484)"
    assert result["raw_data"]["city"] == "Phoenix"

@pytest.mark.asyncio
async def test_high_engagement_score(parser, valid_listing_data):
    """Test calculation of high engagement score."""
    valid_listing_data["engagement"] = {
        "views": 500,
        "saves": 100,
        "inquiries": 50
    }
    
    result = await parser.parse_async(valid_listing_data)
    assert result.metadata["engagement_score"] > 0.8

@pytest.mark.asyncio
async def test_low_engagement_score(parser, valid_listing_data):
    """Test calculation of low engagement score."""
    valid_listing_data["engagement"] = {
        "views": 10,
        "saves": 1,
        "inquiries": 0
    }
    
    result = await parser.parse_async(valid_listing_data)
    assert result.metadata["engagement_score"] < 0.3

@pytest.mark.asyncio
async def test_listing_age_calculation(parser, valid_listing_data):
    """Test calculation of listing age."""
    result = await parser.parse_async(valid_listing_data)
    assert "listing_age_days" in result.metadata
    assert isinstance(result.metadata["listing_age_days"], int)

def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "facebook"

@pytest.mark.asyncio
async def test_price_normalization(parser, valid_listing_data):
    """Test price normalization across different currencies."""
    valid_listing_data["listing"]["price"]["currency"] = "EUR"
    result = await parser.parse_async(valid_listing_data)
    assert "original_currency" in result.metadata
    assert result.metadata["original_currency"] == "EUR"
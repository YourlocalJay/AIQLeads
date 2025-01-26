"""
Test suite for the Dallas/Fort Worth MLS parser implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.dallas_ft_worth_parser import DallasFtWorthParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate

@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return DallasFtWorthParser()

@pytest.fixture
def valid_listing_data():
    """Provide sample valid DFW MLS listing data."""
    return {
        "mlsNumber": "NTREIS-78901",
        "listingDetails": {
            "price": 625000,
            "propertyType": "Residential",
            "status": "Active",
            "daysOnMarket": 12,
            "location": {
                "latitude": 32.7767,
                "longitude": -96.7970,
                "address": {
                    "street": "5678 Main Street",
                    "city": "Dallas",
                    "county": "Dallas",
                    "state": "TX",
                    "zipCode": "75201"
                }
            },
            "propertyDetails": {
                "bedrooms": 4,
                "bathrooms": 3,
                "squareFeet": 2800,
                "yearBuilt": 2010,
                "lotSize": "0.3 acres",
                "subdivision": "Downtown Dallas"
            }
        },
        "listingAgent": {
            "name": "Robert Miller",
            "license": "TX-456789",
            "contact": {
                "phone": "214-555-6789",
                "email": "robert.m@dfwrealty.com"
            },
            "brokerage": "DFW Premium Properties"
        },
        "compliance": {
            "ntreisCompliant": True,
            "lastVerified": "2025-01-20T11:30:00Z",
            "marketingRestrictions": [],
            "subdivisionRestrictions": None
        },
        "marketData": {
            "submarket": "Downtown Dallas",
            "priceHistory": [
                {"date": "2024-12-15", "price": 650000},
                {"date": "2025-01-10", "price": 625000}
            ],
            "comparables": 12
        }
    }

@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid DFW MLS listing."""
    result = await parser.parse_async(valid_listing_data)
    
    assert isinstance(result, LeadCreate)
    assert result.source_id == "NTREIS-78901"
    assert result.market == "dallas_ft_worth"
    assert result.contact_name == "Robert Miller"
    assert result.email == "robert.m@dfwrealty.com"
    assert result.phone == "214-555-6789"
    assert result.company_name == "DFW Premium Properties"
    
    assert result.metadata["property_type"] == "Residential"
    assert result.metadata["price"] == 625000
    assert result.metadata["submarket"] == "Downtown Dallas"

@pytest.mark.asyncio
async def test_ntreis_compliance(parser, valid_listing_data):
    """Test NTREIS compliance validation."""
    valid_listing_data["compliance"]["ntreisCompliant"] = False
    
    with pytest.raises(ParseError, match="Listing not NTREIS compliant"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_dfw_area_validation(parser, valid_listing_data):
    """Test DFW metropolitan area validation."""
    valid_listing_data["listingDetails"]["location"]["address"]["county"] = "Travis"
    
    with pytest.raises(ParseError, match="Location outside DFW service area"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_price_history(parser, valid_listing_data):
    """Test price history processing."""
    result = await parser.parse_async(valid_listing_data)
    
    price_history = result.metadata["price_history"]
    assert len(price_history) == 2
    assert price_history[0]["price"] == 650000
    assert "price_change_percentage" in result.metadata

@pytest.mark.asyncio
async def test_market_analysis(parser, valid_listing_data):
    """Test market analysis calculations."""
    result = await parser.parse_async(valid_listing_data)
    
    assert "comparable_count" in result.metadata
    assert result.metadata["comparable_count"] == 12
    assert "market_position_score" in result.metadata
    assert isinstance(result.metadata["market_position_score"], float)

@pytest.mark.asyncio
async def test_subdivision_restrictions(parser, valid_listing_data):
    """Test handling of subdivision restrictions."""
    valid_listing_data["compliance"]["subdivisionRestrictions"] = ["HOA approval required"]
    
    result = await parser.parse_async(valid_listing_data)
    assert "subdivision_restrictions" in result.metadata
    assert len(result.metadata["subdivision_restrictions"]) == 1

@pytest.mark.asyncio
async def test_location_coordinates(parser, valid_listing_data):
    """Test location coordinate processing."""
    result = await parser.parse_async(valid_listing_data)
    
    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-96.7970 32.7767)"
    assert location["raw_data"]["city"] == "Dallas"
    assert location["raw_data"]["county"] == "Dallas"

@pytest.mark.asyncio
async def test_license_validation(parser, valid_listing_data):
    """Test Texas license number validation."""
    valid_listing_data["listingAgent"]["license"] = "OK-123456"
    
    with pytest.raises(ParseError, match="Invalid Texas license format"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_submarkets(parser, valid_listing_data):
    """Test submarket categorization."""
    result = await parser.parse_async(valid_listing_data)
    
    assert result.metadata["submarket"] == "Downtown Dallas"
    assert "submarket_metrics" in result.metadata
    assert isinstance(result.metadata["submarket_metrics"], dict)

def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "dallas_ft_worth"

@pytest.mark.asyncio
async def test_property_valuation(parser, valid_listing_data):
    """Test property valuation calculations."""
    result = await parser.parse_async(valid_listing_data)
    
    assert "price_per_sqft" in result.metadata
    assert result.metadata["price_per_sqft"] == 625000 / 2800
    assert "valuation_confidence_score" in result.metadata
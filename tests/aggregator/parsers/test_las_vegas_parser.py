"""
Test suite for the Las Vegas MLS parser implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.las_vegas_parser import LasVegasParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate

@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return LasVegasParser()

@pytest.fixture
def valid_listing_data():
    """Provide sample valid Las Vegas MLS listing data."""
    return {
        "mlsNumber": "GLVAR-34567",
        "listingDetails": {
            "price": 475000,
            "propertyType": "Single Family",
            "status": "Active",
            "daysOnMarket": 15,
            "location": {
                "latitude": 36.1699,
                "longitude": -115.1398,
                "address": {
                    "street": "9876 Desert Way",
                    "city": "Las Vegas",
                    "county": "Clark",
                    "state": "NV",
                    "zipCode": "89101"
                },
                "submarket": "Downtown Las Vegas"
            },
            "propertyDetails": {
                "bedrooms": 4,
                "bathrooms": 3,
                "squareFeet": 2500,
                "yearBuilt": 2018,
                "lotSize": "0.2 acres",
                "communityName": "Desert Shores"
            },
            "zoning": {
                "code": "R1",
                "shortTermRental": False,
                "restrictions": []
            }
        },
        "listingAgent": {
            "name": "Jennifer Parker",
            "license": "NV-B.1234567",
            "contact": {
                "phone": "702-555-4321",
                "email": "jennifer.p@lvrealty.com"
            },
            "brokerage": "Las Vegas Elite Realty"
        },
        "compliance": {
            "glvarCompliant": True,
            "lastVerified": "2025-01-20T09:15:00Z",
            "disclaimers": ["HOA approval required"]
        }
    }

@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid Las Vegas MLS listing."""
    result = await parser.parse_async(valid_listing_data)
    
    assert isinstance(result, LeadCreate)
    assert result.source_id == "GLVAR-34567"
    assert result.market == "las_vegas"
    assert result.contact_name == "Jennifer Parker"
    assert result.email == "jennifer.p@lvrealty.com"
    assert result.phone == "702-555-4321"
    assert result.company_name == "Las Vegas Elite Realty"
    
    assert result.metadata["property_type"] == "Single Family"
    assert result.metadata["price"] == 475000
    assert result.metadata["community"] == "Desert Shores"

@pytest.mark.asyncio
async def test_license_validation(parser, valid_listing_data):
    """Test Nevada license number validation."""
    valid_listing_data["listingAgent"]["license"] = "CA-1234567"
    
    with pytest.raises(ParseError, match="Invalid Nevada license format"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_glvar_compliance(parser, valid_listing_data):
    """Test GLVAR compliance validation."""
    valid_listing_data["compliance"]["glvarCompliant"] = False
    
    with pytest.raises(ParseError, match="Listing not GLVAR compliant"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_location_validation(parser, valid_listing_data):
    """Test Las Vegas area location validation."""
    valid_listing_data["listingDetails"]["location"]["address"]["county"] = "Washoe"
    
    with pytest.raises(ParseError, match="Location outside Las Vegas service area"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_zoning_validation(parser, valid_listing_data):
    """Test zoning information processing."""
    result = await parser.parse_async(valid_listing_data)
    
    assert result.metadata["zoning"]["code"] == "R1"
    assert result.metadata["zoning"]["short_term_rental"] is False
    assert isinstance(result.metadata["zoning"]["restrictions"], list)

@pytest.mark.asyncio
async def test_community_analysis(parser, valid_listing_data):
    """Test community information processing."""
    result = await parser.parse_async(valid_listing_data)
    
    assert result.metadata["community"] == "Desert Shores"
    assert "community_metrics" in result.metadata
    assert isinstance(result.metadata["community_metrics"], dict)

@pytest.mark.asyncio
async def test_coordinates_validation(parser, valid_listing_data):
    """Test location coordinate processing."""
    result = await parser.parse_async(valid_listing_data)
    
    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-115.1398 36.1699)"
    assert location["raw_data"]["county"] == "Clark"
    assert location["raw_data"]["submarket"] == "Downtown Las Vegas"

@pytest.mark.asyncio
async def test_missing_agent_info(parser, valid_listing_data):
    """Test handling of missing agent information."""
    del valid_listing_data["listingAgent"]
    
    with pytest.raises(ParseError, match="Missing agent information"):
        await parser.parse_async(valid_listing_data)

def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "las_vegas"

@pytest.mark.asyncio
async def test_valuation_metrics(parser, valid_listing_data):
    """Test property valuation calculations."""
    result = await parser.parse_async(valid_listing_data)
    
    assert "price_per_sqft" in result.metadata
    assert result.metadata["price_per_sqft"] == 475000 / 2500
    assert "market_valuation_score" in result.metadata
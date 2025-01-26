"""
Test suite for the FSBO (For Sale By Owner) parser implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.fsbo_parser import FSBOParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate

@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return FSBOParser()

@pytest.fixture
def valid_listing_data():
    """Provide sample valid FSBO listing data."""
    return {
        "listingId": "fsbo-789012",
        "propertyDetails": {
            "price": 375000,
            "type": "Single Family Home",
            "status": "Active",
            "daysListed": 14,
            "location": {
                "latitude": 36.1699,
                "longitude": -115.1398,
                "address": {
                    "street": "123 Oak Street",
                    "city": "Las Vegas",
                    "state": "NV",
                    "zip": "89101"
                }
            }
        },
        "ownerInfo": {
            "name": "David Wilson",
            "contact": {
                "phone": "555-4567",
                "email": "david.w@email.com",
                "preferredMethod": "phone"
            },
            "availability": {
                "weekdays": "9AM-6PM",
                "weekends": "10AM-4PM"
            }
        },
        "verificationStatus": {
            "identityVerified": True,
            "ownershipVerified": True,
            "lastVerified": "2025-01-15T14:30:00Z"
        }
    }

@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid FSBO listing."""
    result = await parser.parse_async(valid_listing_data)
    
    assert isinstance(result, LeadCreate)
    assert result.source_id == "fsbo-789012"
    assert result.market == "fsbo"
    assert result.contact_name == "David Wilson"
    assert result.email == "david.w@email.com"
    assert result.phone == "555-4567"
    assert result.company_name == "FSBO"
    
    assert result.metadata["property_type"] == "Single Family Home"
    assert result.metadata["price"] == 375000
    assert result.metadata["verification"]["identity_verified"] is True

@pytest.mark.asyncio
async def test_verification_status(parser, valid_listing_data):
    """Test handling of verification status information."""
    result = await parser.parse_async(valid_listing_data)
    
    verification = result.metadata["verification"]
    assert verification["identity_verified"] is True
    assert verification["ownership_verified"] is True
    assert isinstance(verification["last_verified"], str)

@pytest.mark.asyncio
async def test_owner_availability(parser, valid_listing_data):
    """Test parsing of owner availability information."""
    result = await parser.parse_async(valid_listing_data)
    
    availability = result.metadata["availability"]
    assert availability["weekdays"] == "9AM-6PM"
    assert availability["weekends"] == "10AM-4PM"

@pytest.mark.asyncio
async def test_unverified_listing(parser, valid_listing_data):
    """Test handling of unverified listings."""
    valid_listing_data["verificationStatus"]["identityVerified"] = False
    valid_listing_data["verificationStatus"]["ownershipVerified"] = False
    
    result = await parser.parse_async(valid_listing_data)
    assert result.metadata["verification_score"] < 0.5

@pytest.mark.asyncio
async def test_missing_verification(parser, valid_listing_data):
    """Test handling of missing verification information."""
    del valid_listing_data["verificationStatus"]
    
    with pytest.raises(ParseError, match="Missing verification status"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_contact_preference(parser, valid_listing_data):
    """Test handling of contact preferences."""
    result = await parser.parse_async(valid_listing_data)
    
    assert result.metadata["contact_preference"] == "phone"
    assert result.metadata["has_alternate_contact"] is True

@pytest.mark.asyncio
async def test_invalid_price(parser, valid_listing_data):
    """Test handling of invalid price data."""
    valid_listing_data["propertyDetails"]["price"] = -1000
    
    with pytest.raises(ParseError, match="Invalid price"):
        await parser.parse_async(valid_listing_data)

@pytest.mark.asyncio
async def test_location_parsing(parser, valid_listing_data):
    """Test location data extraction and validation."""
    result = await parser.parse_async(valid_listing_data)
    
    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-115.1398 36.1699)"
    assert location["raw_data"]["city"] == "Las Vegas"
    assert location["raw_data"]["state"] == "NV"

@pytest.mark.asyncio
async def test_listing_duration(parser, valid_listing_data):
    """Test handling of listing duration information."""
    result = await parser.parse_async(valid_listing_data)
    
    assert result.metadata["days_listed"] == 14
    assert "listing_age_score" in result.metadata
    assert isinstance(result.metadata["listing_age_score"], float)

def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "fsbo"

@pytest.mark.asyncio
async def test_incomplete_contact(parser, valid_listing_data):
    """Test handling of incomplete contact information."""
    del valid_listing_data["ownerInfo"]["contact"]["phone"]
    del valid_listing_data["ownerInfo"]["contact"]["email"]
    
    with pytest.raises(ParseError, match="No valid contact methods"):
        await parser.parse_async(valid_listing_data)
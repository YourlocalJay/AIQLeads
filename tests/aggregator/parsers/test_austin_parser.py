"""
Test suite for the Austin MLS parser implementation.
"""

import pytest
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.austin_parser import AustinParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate


@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return AustinParser()


@pytest.fixture
def valid_listing_data():
    """Provide sample valid Austin MLS listing data."""
    return {
        "mlsNumber": "ABOR-12345",
        "listingDetails": {
            "price": 525000,
            "propertyType": "Single Family",
            "status": "Active",
            "daysOnMarket": 8,
            "location": {
                "latitude": 30.2672,
                "longitude": -97.7431,
                "address": {
                    "street": "1234 Congress Ave",
                    "city": "Austin",
                    "county": "Travis",
                    "state": "TX",
                    "zipCode": "78701",
                },
            },
            "propertyDetails": {
                "bedrooms": 3,
                "bathrooms": 2.5,
                "squareFeet": 2200,
                "yearBuilt": 2015,
                "lotSize": "0.25 acres",
            },
        },
        "listingAgent": {
            "name": "Sarah Anderson",
            "license": "TX-987654",
            "contact": {"phone": "512-555-0123", "email": "sarah.a@austinrealty.com"},
            "brokerage": "Austin Premium Realty",
        },
        "compliance": {
            "aborCompliant": True,
            "lastVerified": "2025-01-20T10:00:00Z",
            "restrictions": [],
        },
    }


@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid Austin MLS listing."""
    result = await parser.parse_async(valid_listing_data)

    assert isinstance(result, LeadCreate)
    assert result.source_id == "ABOR-12345"
    assert result.market == "austin"
    assert result.contact_name == "Sarah Anderson"
    assert result.email == "sarah.a@austinrealty.com"
    assert result.phone == "512-555-0123"
    assert result.company_name == "Austin Premium Realty"

    assert result.metadata["property_type"] == "Single Family"
    assert result.metadata["price"] == 525000
    assert result.metadata["county"] == "Travis"


@pytest.mark.asyncio
async def test_license_validation(parser, valid_listing_data):
    """Test Texas license number validation."""
    valid_listing_data["listingAgent"]["license"] = "CA-123456"

    with pytest.raises(ParseError, match="Invalid Texas license format"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_abor_compliance(parser, valid_listing_data):
    """Test ABOR compliance validation."""
    valid_listing_data["compliance"]["aborCompliant"] = False

    with pytest.raises(ParseError, match="Listing not ABOR compliant"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_location_validation(parser, valid_listing_data):
    """Test Austin area location validation."""
    valid_listing_data["listingDetails"]["location"]["address"]["county"] = "Dallas"

    with pytest.raises(ParseError, match="Location outside Austin service area"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_property_details(parser, valid_listing_data):
    """Test property details extraction and validation."""
    result = await parser.parse_async(valid_listing_data)

    details = result.metadata["property_details"]
    assert details["bedrooms"] == 3
    assert details["bathrooms"] == 2.5
    assert details["square_feet"] == 2200
    assert details["year_built"] == 2015
    assert details["lot_size"] == "0.25 acres"


@pytest.mark.asyncio
async def test_location_coordinates(parser, valid_listing_data):
    """Test location coordinate processing."""
    result = await parser.parse_async(valid_listing_data)

    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-97.7431 30.2672)"
    assert location["raw_data"]["county"] == "Travis"
    assert location["raw_data"]["city"] == "Austin"


@pytest.mark.asyncio
async def test_market_duration(parser, valid_listing_data):
    """Test market duration calculations."""
    result = await parser.parse_async(valid_listing_data)

    assert result.metadata["days_on_market"] == 8
    assert "market_velocity_score" in result.metadata
    assert isinstance(result.metadata["market_velocity_score"], float)


@pytest.mark.asyncio
async def test_missing_agent_info(parser, valid_listing_data):
    """Test handling of missing agent information."""
    del valid_listing_data["listingAgent"]

    with pytest.raises(ParseError, match="Missing agent information"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_compliance_verification(parser, valid_listing_data):
    """Test compliance verification date handling."""
    result = await parser.parse_async(valid_listing_data)

    assert "last_verified" in result.metadata["compliance"]
    assert isinstance(result.metadata["compliance"]["last_verified"], str)


def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "austin"


@pytest.mark.asyncio
async def test_price_per_sqft(parser, valid_listing_data):
    """Test price per square foot calculations."""
    result = await parser.parse_async(valid_listing_data)

    assert "price_per_sqft" in result.metadata
    assert result.metadata["price_per_sqft"] == 525000 / 2200

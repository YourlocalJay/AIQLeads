"""
Test suite for the Phoenix MLS parser implementation.
"""

import pytest
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.phoenix_parser import PhoenixParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate


@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return PhoenixParser()


@pytest.fixture
def valid_listing_data():
    """Provide sample valid Phoenix MLS listing data."""
    return {
        "mlsNumber": "ARMLS-56789",
        "listingDetails": {
            "price": 550000,
            "propertyType": "Single Family",
            "status": "Active",
            "daysOnMarket": 10,
            "location": {
                "latitude": 33.4484,
                "longitude": -112.0740,
                "address": {
                    "street": "4321 Desert Palm Drive",
                    "city": "Phoenix",
                    "county": "Maricopa",
                    "state": "AZ",
                    "zipCode": "85001",
                },
                "submarket": "North Phoenix",
            },
            "propertyDetails": {
                "bedrooms": 4,
                "bathrooms": 2.5,
                "squareFeet": 2600,
                "yearBuilt": 2019,
                "lotSize": "0.25 acres",
                "subdivision": "Desert Ridge",
            },
            "environmental": {
                "hasPool": True,
                "solarPanels": False,
                "xeriscaping": True,
            },
        },
        "listingAgent": {
            "name": "Thomas Wright",
            "license": "AZ-BR549321",
            "contact": {"phone": "480-555-8765", "email": "thomas.w@phxrealty.com"},
            "brokerage": "Phoenix Premier Properties",
        },
        "compliance": {
            "armlsCompliant": True,
            "lastVerified": "2025-01-20T08:45:00Z",
            "restrictions": ["HOA approval required"],
            "waterRights": "Yes",
        },
    }


@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid Phoenix MLS listing."""
    result = await parser.parse_async(valid_listing_data)

    assert isinstance(result, LeadCreate)
    assert result.source_id == "ARMLS-56789"
    assert result.market == "phoenix"
    assert result.contact_name == "Thomas Wright"
    assert result.email == "thomas.w@phxrealty.com"
    assert result.phone == "480-555-8765"
    assert result.company_name == "Phoenix Premier Properties"

    assert result.metadata["property_type"] == "Single Family"
    assert result.metadata["price"] == 550000
    assert result.metadata["subdivision"] == "Desert Ridge"


@pytest.mark.asyncio
async def test_license_validation(parser, valid_listing_data):
    """Test Arizona license number validation."""
    valid_listing_data["listingAgent"]["license"] = "CA-BR549321"

    with pytest.raises(ParseError, match="Invalid Arizona license format"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_armls_compliance(parser, valid_listing_data):
    """Test ARMLS compliance validation."""
    valid_listing_data["compliance"]["armlsCompliant"] = False

    with pytest.raises(ParseError, match="Listing not ARMLS compliant"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_location_validation(parser, valid_listing_data):
    """Test Phoenix metropolitan area validation."""
    valid_listing_data["listingDetails"]["location"]["address"]["county"] = "Pima"

    with pytest.raises(ParseError, match="Location outside Phoenix service area"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_environmental_features(parser, valid_listing_data):
    """Test environmental features processing."""
    result = await parser.parse_async(valid_listing_data)

    features = result.metadata["environmental_features"]
    assert features["has_pool"] is True
    assert features["solar_panels"] is False
    assert features["xeriscaping"] is True


@pytest.mark.asyncio
async def test_water_rights(parser, valid_listing_data):
    """Test water rights information processing."""
    result = await parser.parse_async(valid_listing_data)

    assert result.metadata["water_rights"] == "Yes"
    assert "water_features_score" in result.metadata
    assert isinstance(result.metadata["water_features_score"], float)


@pytest.mark.asyncio
async def test_coordinates_validation(parser, valid_listing_data):
    """Test location coordinate processing."""
    result = await parser.parse_async(valid_listing_data)

    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-112.0740 33.4484)"
    assert location["raw_data"]["county"] == "Maricopa"
    assert location["raw_data"]["submarket"] == "North Phoenix"


@pytest.mark.asyncio
async def test_missing_agent_info(parser, valid_listing_data):
    """Test handling of missing agent information."""
    del valid_listing_data["listingAgent"]

    with pytest.raises(ParseError, match="Missing agent information"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_property_features(parser, valid_listing_data):
    """Test property features validation."""
    result = await parser.parse_async(valid_listing_data)

    details = result.metadata["property_details"]
    assert details["bedrooms"] == 4
    assert details["bathrooms"] == 2.5
    assert details["square_feet"] == 2600
    assert details["year_built"] == 2019


def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "phoenix"


@pytest.mark.asyncio
async def test_market_metrics(parser, valid_listing_data):
    """Test market metrics calculations."""
    result = await parser.parse_async(valid_listing_data)

    assert "price_per_sqft" in result.metadata
    assert result.metadata["price_per_sqft"] == 550000 / 2600
    assert "submarket_score" in result.metadata

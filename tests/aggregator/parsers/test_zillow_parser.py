"""
Test suite for the Zillow parser implementation.
"""

import pytest
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.zillow_parser import ZillowParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate


@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return ZillowParser()


@pytest.fixture
def valid_listing_data():
    """Provide sample valid listing data."""
    return {
        "id": "test-123",
        "price": 450000,
        "propertyType": "SINGLE_FAMILY",
        "daysOnZillow": 14,
        "location": {"latitude": 34.0522, "longitude": -118.2437},
        "agent": {
            "name": "John Doe",
            "brokerName": "Real Estate Co",
            "phoneNumber": "555-0123",
            "email": "john.doe@realestate.com",
        },
        "isFSBO": False,
    }


@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid listing."""
    result = await parser.parse_async(valid_listing_data)

    assert isinstance(result, LeadCreate)
    assert result.source_id == "test-123"
    assert result.market == "zillow"
    assert result.contact_name == "John Doe"
    assert result.email == "john.doe@realestate.com"
    assert result.phone == "555-0123"
    assert result.company_name == "Real Estate Co"
    assert isinstance(result.metadata, dict)
    assert result.metadata["property_type"] == "SINGLE_FAMILY"
    assert result.metadata["price"] == 450000


@pytest.mark.asyncio
async def test_parse_fsbo_listing(parser):
    """Test parsing of a FSBO listing."""
    fsbo_data = {
        "id": "fsbo-123",
        "price": 350000,
        "propertyType": "CONDO",
        "daysOnZillow": 7,
        "location": {"latitude": 34.0522, "longitude": -118.2437},
        "isFSBO": True,
        "owner": {
            "name": "Jane Smith",
            "phoneNumber": "555-9876",
            "email": "jane.smith@email.com",
        },
    }

    result = await parser.parse_async(fsbo_data)

    assert result.source_id == "fsbo-123"
    assert result.contact_name == "Jane Smith"
    assert result.company_name == "FSBO"
    assert result.metadata["is_fsbo"] is True


@pytest.mark.asyncio
async def test_invalid_price(parser, valid_listing_data):
    """Test handling of invalid price data."""
    valid_listing_data["price"] = -1000

    with pytest.raises(ParseError, match="Invalid price format"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_missing_location(parser, valid_listing_data):
    """Test handling of missing location data."""
    valid_listing_data.pop("location")

    with pytest.raises(ParseError, match="Invalid location data"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_high_fraud_score(parser, valid_listing_data):
    """Test rejection of listings with high fraud scores."""
    valid_listing_data["price"] = 10000  # Triggers high fraud score
    valid_listing_data["agent"]["email"] = None
    valid_listing_data["agent"]["phoneNumber"] = None

    with pytest.raises(ParseError, match="Lead failed fraud detection checks"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_missing_contact_info(parser, valid_listing_data):
    """Test handling of missing contact information."""
    valid_listing_data["agent"]["email"] = None
    valid_listing_data["agent"]["phoneNumber"] = None

    with pytest.raises(ParseError, match="No valid contact information available"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_location_extraction(parser):
    """Test proper extraction of location data."""
    location_data = {"location": {"latitude": 34.0522, "longitude": -118.2437}}

    result = parser._extract_location(location_data)
    assert isinstance(result["coordinates"], WKTElement)
    assert result["coordinates"].data == "POINT(-118.2437 34.0522)"


@pytest.mark.asyncio
async def test_fraud_score_calculation(parser):
    """Test fraud score calculation logic."""
    score = parser._calculate_fraud_score(
        price=450000,
        property_type="SINGLE_FAMILY",
        days_on_market=14,
        contact={"email": "test@test.com", "phone": "555-1234"},
    )

    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.1"
    assert parser.MARKET_ID == "zillow"

"""
Test suite for the Craigslist parser implementation.
"""

import pytest
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.craigslist_parser import CraigslistParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate


@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return CraigslistParser()


@pytest.fixture
def valid_listing_data():
    """Provide sample valid Craigslist listing data."""
    return {
        "postId": "cl-456789",
        "listing": {
            "title": "Beautiful 3BR House for Sale",
            "price": 399000,
            "category": "real estate - by owner",
            "location": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "area": "san francisco",
                "address": {
                    "neighborhood": "Mission District",
                    "city": "San Francisco",
                    "state": "CA",
                },
            },
            "postingDate": "2025-01-20T08:15:00Z",
            "updateDate": "2025-01-21T14:30:00Z",
            "attributes": {
                "bedrooms": "3",
                "bathrooms": "2",
                "sqft": "1800",
                "availability": "immediate",
            },
        },
        "contact": {
            "name": "Michael Brown",
            "phone": "555-2345",
            "email": "michael.b@email.com",
            "preferredContact": "email",
        },
        "flags": {
            "isDeleted": False,
            "isSpam": False,
            "hasImages": True,
            "imageCount": 8,
        },
    }


@pytest.mark.asyncio
async def test_parse_valid_listing(parser, valid_listing_data):
    """Test parsing of a valid Craigslist listing."""
    result = await parser.parse_async(valid_listing_data)

    assert isinstance(result, LeadCreate)
    assert result.source_id == "cl-456789"
    assert result.market == "craigslist"
    assert result.contact_name == "Michael Brown"
    assert result.email == "michael.b@email.com"
    assert result.phone == "555-2345"
    assert result.company_name == "FSBO"

    assert result.metadata["price"] == 399000
    assert result.metadata["category"] == "real estate - by owner"
    assert result.metadata["attributes"]["bedrooms"] == "3"


@pytest.mark.asyncio
async def test_listing_flags(parser, valid_listing_data):
    """Test handling of listing flags."""
    result = await parser.parse_async(valid_listing_data)

    flags = result.metadata["flags"]
    assert flags["is_deleted"] is False
    assert flags["is_spam"] is False
    assert flags["has_images"] is True
    assert flags["image_count"] == 8


@pytest.mark.asyncio
async def test_posting_dates(parser, valid_listing_data):
    """Test handling of posting and update dates."""
    result = await parser.parse_async(valid_listing_data)

    assert "posting_date" in result.metadata
    assert "update_date" in result.metadata
    assert isinstance(result.metadata["posting_age_hours"], float)


@pytest.mark.asyncio
async def test_deleted_listing(parser, valid_listing_data):
    """Test handling of deleted listings."""
    valid_listing_data["flags"]["isDeleted"] = True

    with pytest.raises(ParseError, match="Listing has been deleted"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_spam_listing(parser, valid_listing_data):
    """Test handling of spam-flagged listings."""
    valid_listing_data["flags"]["isSpam"] = True

    with pytest.raises(ParseError, match="Listing marked as spam"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_location_parsing(parser, valid_listing_data):
    """Test location data extraction."""
    result = await parser.parse_async(valid_listing_data)

    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-122.4194 37.7749)"
    assert location["raw_data"]["city"] == "San Francisco"
    assert location["raw_data"]["neighborhood"] == "Mission District"


@pytest.mark.asyncio
async def test_attribute_validation(parser, valid_listing_data):
    """Test validation of listing attributes."""
    result = await parser.parse_async(valid_listing_data)

    attributes = result.metadata["attributes"]
    assert all(key in attributes for key in ["bedrooms", "bathrooms", "sqft"])
    assert attributes["availability"] == "immediate"


@pytest.mark.asyncio
async def test_missing_price(parser, valid_listing_data):
    """Test handling of missing price information."""
    del valid_listing_data["listing"]["price"]

    with pytest.raises(ParseError, match="Missing price information"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_invalid_contact(parser, valid_listing_data):
    """Test handling of invalid contact information."""
    valid_listing_data["contact"]["email"] = "invalid-email"
    valid_listing_data["contact"]["phone"] = "invalid-phone"

    with pytest.raises(ParseError, match="No valid contact methods"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_listing_quality_score(parser, valid_listing_data):
    """Test calculation of listing quality score."""
    result = await parser.parse_async(valid_listing_data)

    assert "quality_score" in result.metadata
    assert 0 <= result.metadata["quality_score"] <= 100
    assert isinstance(result.metadata["quality_score"], float)


def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "craigslist"


@pytest.mark.asyncio
async def test_category_validation(parser, valid_listing_data):
    """Test validation of listing category."""
    valid_listing_data["listing"]["category"] = "invalid category"

    with pytest.raises(ParseError, match="Invalid listing category"):
        await parser.parse_async(valid_listing_data)

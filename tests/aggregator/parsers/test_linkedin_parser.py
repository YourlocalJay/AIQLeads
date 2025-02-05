"""
Test suite for the LinkedIn parser implementation.
"""

import pytest
from geoalchemy2.elements import WKTElement
from src.aggregator.parsers.linkedin_parser import LinkedInParser
from src.aggregator.exceptions import ParseError
from src.schemas.lead_schema import LeadCreate


@pytest.fixture
def parser():
    """Provide a fresh parser instance for each test."""
    return LinkedInParser()


@pytest.fixture
def valid_listing_data():
    """Provide sample valid listing data."""
    return {
        "id": "li-123456",
        "profile": {
            "fullName": "Robert Smith",
            "title": "Real Estate Agent",
            "companyInfo": {
                "name": "Premium Real Estate Group",
                "location": {
                    "city": "Austin",
                    "state": "TX",
                    "country": "US",
                    "coordinates": {"latitude": 30.2672, "longitude": -97.7431},
                },
            },
            "contact": {
                "email": "robert.smith@premium-re.com",
                "phone": "555-7890",
                "website": "https://premium-re.com/robert-smith",
            },
        },
        "experience": [
            {
                "title": "Senior Real Estate Agent",
                "company": "Premium Real Estate Group",
                "duration": "5 years",
                "licenseInfo": "TX-12345",
            }
        ],
        "metrics": {
            "connections": 2500,
            "recommendations": 45,
            "endorsements": {"Real Estate": 78, "Property Management": 52},
        },
        "activity": {
            "lastActive": "2025-01-20T10:30:00Z",
            "postFrequency": "weekly",
            "responseRate": 0.92,
        },
    }


@pytest.mark.asyncio
async def test_parse_valid_profile(parser, valid_listing_data):
    """Test parsing of a valid LinkedIn profile."""
    result = await parser.parse_async(valid_listing_data)

    assert isinstance(result, LeadCreate)
    assert result.source_id == "li-123456"
    assert result.market == "linkedin"
    assert result.contact_name == "Robert Smith"
    assert result.email == "robert.smith@premium-re.com"
    assert result.phone == "555-7890"
    assert result.company_name == "Premium Real Estate Group"

    assert result.metadata["professional_info"]["title"] == "Real Estate Agent"
    assert result.metadata["experience"][0]["duration"] == "5 years"
    assert result.metadata["metrics"]["connections"] == 2500


@pytest.mark.asyncio
async def test_missing_contact_info(parser, valid_listing_data):
    """Test handling of missing contact information."""
    del valid_listing_data["profile"]["contact"]

    with pytest.raises(ParseError, match="No valid contact methods available"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_extract_location(parser, valid_listing_data):
    """Test location data extraction."""
    result = await parser.parse_async(valid_listing_data)

    location = result.location
    assert isinstance(location["coordinates"], WKTElement)
    assert location["coordinates"].data == "POINT(-97.7431 30.2672)"
    assert location["raw_data"]["city"] == "Austin"
    assert location["raw_data"]["state"] == "TX"


@pytest.mark.asyncio
async def test_professional_score_calculation(parser, valid_listing_data):
    """Test calculation of professional score."""
    result = await parser.parse_async(valid_listing_data)

    assert "professional_score" in result.metadata
    assert 0 <= result.metadata["professional_score"] <= 100
    assert result.metadata["professional_score"] > 80  # High score due to good metrics


@pytest.mark.asyncio
async def test_invalid_license_info(parser, valid_listing_data):
    """Test handling of invalid license information."""
    valid_listing_data["experience"][0]["licenseInfo"] = "INVALID-FORMAT"

    with pytest.raises(ParseError, match="Invalid license format"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_engagement_metrics(parser, valid_listing_data):
    """Test parsing of engagement metrics."""
    result = await parser.parse_async(valid_listing_data)

    assert result.metadata["engagement"]["response_rate"] == 0.92
    assert result.metadata["engagement"]["post_frequency"] == "weekly"
    assert isinstance(result.metadata["engagement"]["last_active"], str)


@pytest.mark.asyncio
async def test_expertise_validation(parser, valid_listing_data):
    """Test validation of expertise and endorsements."""
    result = await parser.parse_async(valid_listing_data)

    assert "endorsements" in result.metadata
    assert result.metadata["endorsements"]["Real Estate"] == 78
    assert result.metadata["endorsements"]["Property Management"] == 52


@pytest.mark.asyncio
async def test_missing_company_info(parser, valid_listing_data):
    """Test handling of missing company information."""
    del valid_listing_data["profile"]["companyInfo"]

    with pytest.raises(ParseError, match="Missing company information"):
        await parser.parse_async(valid_listing_data)


@pytest.mark.asyncio
async def test_activity_analysis(parser, valid_listing_data):
    """Test analysis of profile activity metrics."""
    result = await parser.parse_async(valid_listing_data)

    assert "activity_score" in result.metadata
    assert 0 <= result.metadata["activity_score"] <= 100
    assert isinstance(result.metadata["activity_score"], float)


def test_version_check(parser):
    """Verify parser version is correctly set."""
    assert parser.VERSION == "2.0"
    assert parser.MARKET_ID == "linkedin"


@pytest.mark.asyncio
async def test_connection_strength(parser, valid_listing_data):
    """Test calculation of network connection strength."""
    result = await parser.parse_async(valid_listing_data)

    assert "network_strength" in result.metadata
    assert result.metadata["network_strength"] > 0.8  # High due to 2500+ connections

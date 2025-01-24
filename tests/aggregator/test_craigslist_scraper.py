import pytest
import aiohttp
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from src.aggregator.scrapers.craigslist_scraper import CraigslistScraper
from src.aggregator.exceptions import ScraperError, ParseError, NetworkError
from src.schemas.lead_schema import LeadCreate

@pytest.fixture
async def scraper():
    scraper = CraigslistScraper(rate_limit=20, api_key="test_key")
    yield scraper
    await scraper.cleanup()

@pytest.fixture
def mock_response():
    return {
        "listings": [
            {
                "contact_name": "John Smith",
                "contact_email": "john@example.com",
                "contact_phone": "+1234567890",
                "location": {"city": "Austin", "state": "TX"},
                "posting_date": "2025-01-23T10:00:00Z",
                "price": 350000,
                "url": "https://craigslist.org/listing/123"
            }
        ]
    }

@pytest.mark.asyncio
async def test_initialization(scraper):
    """Test scraper initialization with default parameters."""
    assert scraper.rate_limit == 20
    assert scraper.api_key == "test_key"
    assert scraper.session is None

@pytest.mark.asyncio
async def test_search_successful(scraper, mock_response):
    """Test successful search operation."""
    mock_session = AsyncMock()
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json.return_value = mock_response
    mock_session.get.return_value.__aenter__.return_value = mock_response_obj
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        leads = await scraper.search("Austin, TX", 50.0)
        
        assert len(leads) == 1
        lead = leads[0]
        assert lead.name == "John Smith"
        assert lead.email == "john@example.com"
        assert lead.phone == "+1234567890"
        assert lead.source == "Craigslist"
        assert "location" in lead.metadata
        assert lead.metadata["price"] == 350000

@pytest.mark.asyncio
async def test_rate_limit_handling(scraper):
    """Test rate limit exceeded scenario."""
    mock_session = AsyncMock()
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 429
    mock_response_obj.headers = {"Retry-After": "5"}
    mock_session.get.return_value.__aenter__.return_value = mock_response_obj
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(ScraperError):
            await scraper.search("Austin, TX", 50.0)

@pytest.mark.asyncio
async def test_network_error_retry(scraper, mock_response):
    """Test network error retry mechanism."""
    mock_session = AsyncMock()
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json.return_value = mock_response
    
    # First call raises error, second succeeds
    mock_session.get.return_value.__aenter__.side_effect = [
        aiohttp.ClientError(),
        mock_response_obj
    ]
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        leads = await scraper.search("Austin, TX", 50.0)
        assert len(leads) == 1

@pytest.mark.asyncio
async def test_extract_contact_info_invalid(scraper):
    """Test contact info extraction with invalid data."""
    invalid_listing = {
        "contact_name": "John Smith",
        "location": {"city": "Austin", "state": "TX"}
    }
    
    with pytest.raises(ParseError):
        await scraper.extract_contact_info(invalid_listing)

@pytest.mark.asyncio
async def test_cleanup(scraper):
    """Test session cleanup."""
    await scraper.initialize()
    assert scraper.session is not None
    await scraper.cleanup()
    assert scraper.session is None

@pytest.mark.asyncio
async def test_processing_invalid_listing(scraper):
    """Test handling of invalid listing during processing."""
    invalid_listings = [
        {"contact_name": "John Smith"},  # Missing required fields
        {
            "contact_name": "Jane Doe",
            "contact_email": "jane@example.com",
            "contact_phone": "+1987654321",
            "location": {"city": "Austin", "state": "TX"}
        }
    ]
    
    leads = await scraper._process_listings(invalid_listings)
    assert len(leads) == 1  # Only valid listing processed
    assert leads[0].name == "Jane Doe"

@pytest.mark.asyncio
async def test_headers_with_api_key(scraper):
    """Test header generation with API key."""
    headers = scraper._get_headers()
    assert headers["Authorization"] == "Bearer test_key"
    assert headers["User-Agent"] == "AIQLeads/1.0"
    assert headers["Accept"] == "application/json"

@pytest.mark.asyncio
async def test_headers_without_api_key():
    """Test header generation without API key."""
    scraper = CraigslistScraper()
    headers = scraper._get_headers()
    assert "Authorization" not in headers
    assert headers["User-Agent"] == "AIQLeads/1.0"

@pytest.mark.asyncio
async def test_search_with_custom_parameters(scraper, mock_response):
    """Test search with custom parameters."""
    mock_session = AsyncMock()
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json.return_value = mock_response
    mock_session.get.return_value.__aenter__.return_value = mock_response_obj
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        leads = await scraper.search(
            location="Austin, TX",
            radius_km=75.0,
            category="real-estate-by-owner"
        )
        
        assert len(leads) == 1
        assert mock_session.get.call_count == 1
        called_params = mock_session.get.call_args[1]["params"]
        assert called_params["radius"] == 75.0
        assert called_params["category"] == "real-estate-by-owner"
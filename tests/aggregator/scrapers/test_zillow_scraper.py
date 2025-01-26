import pytest
import aiohttp
import asyncio
from unittest.mock import Mock, patch
from src.aggregator.scrapers.zillow_scraper import ZillowScraper
from src.config import settings

@pytest.fixture
def zillow_scraper():
    return ZillowScraper(
        api_key=settings.ZILLOW_API_KEY,
        rate_limit=100
    )

@pytest.fixture
def mock_response():
    return {
        "results": [
            {
                "zpid": "12345",
                "address": {
                    "streetAddress": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zipcode": "94105"
                },
                "price": 1200000,
                "bedrooms": 3,
                "bathrooms": 2,
                "livingArea": 2000,
                "lotSize": 4000,
                "yearBuilt": 1985,
                "latitude": 37.7749,
                "longitude": -122.4194
            }
        ],
        "pagination": {
            "totalPages": 2,
            "currentPage": 1
        }
    }

@pytest.mark.asyncio
async def test_fetch_listings(zillow_scraper, mock_response):
    """Test successful fetching of listings"""
    async with aiohttp.ClientSession() as session:
        with patch.object(session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = Mock(
                return_value=mock_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            results = await zillow_scraper.fetch_listings(
                session=session,
                location="San Francisco, CA",
                max_price=2000000
            )
            
            assert len(results) == 1
            assert results[0]["zpid"] == "12345"
            assert results[0]["price"] == 1200000

@pytest.mark.asyncio
async def test_handle_rate_limit(zillow_scraper):
    """Test rate limit handling"""
    async with aiohttp.ClientSession() as session:
        with patch.object(session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 429
            
            with pytest.raises(Exception) as exc_info:
                await zillow_scraper.fetch_listings(
                    session=session,
                    location="San Francisco, CA"
                )
            assert "Rate limit exceeded" in str(exc_info.value)

@pytest.mark.asyncio
async def test_pagination(zillow_scraper, mock_response):
    """Test pagination handling"""
    async with aiohttp.ClientSession() as session:
        with patch.object(session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = Mock(
                return_value=mock_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            results = await zillow_scraper.fetch_listings(
                session=session,
                location="San Francisco, CA",
                page=2
            )
            
            assert mock_get.call_count == 1
            call_kwargs = mock_get.call_args[1]
            assert "page=2" in call_kwargs["url"]

@pytest.mark.asyncio
async def test_retry_mechanism(zillow_scraper):
    """Test retry mechanism for failed requests"""
    async with aiohttp.ClientSession() as session:
        with patch.object(session, 'get') as mock_get:
            mock_get.side_effect = [
                Mock(status=500),
                Mock(
                    status=200,
                    json=Mock(return_value=mock_response)
                )
            ]
            
            results = await zillow_scraper.fetch_listings(
                session=session,
                location="San Francisco, CA"
            )
            
            assert mock_get.call_count == 2
            assert len(results) > 0
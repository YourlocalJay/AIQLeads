import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.aggregator.base_scraper import BaseScraper
from src.aggregator.exceptions import NetworkError, ScraperError
from src.aggregator.components.proxy_manager import ProxyManager
from src.aggregator.components.rate_limiter import RateLimiter

class TestScraper(BaseScraper):
    """Test implementation of BaseScraper"""
    async def scrape(self, query=None):
        return await self._safe_fetch("https://test.com/api")

@pytest.fixture
def scraper():
    return TestScraper(base_url="https://test.com")

@pytest.fixture
def mock_proxy():
    return "http://proxy.example.com:8080"

@pytest.fixture
def mock_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"data": "test"}
    return response

@pytest.mark.asyncio
async def test_safe_fetch_success(scraper, mock_response):
    """Test successful fetch operation"""
    with patch("httpx.AsyncClient.request", AsyncMock(return_value=mock_response)):
        result = await scraper._safe_fetch("https://test.com/api")
        assert result == {"data": "test"}

@pytest.mark.asyncio
async def test_rate_limit_handling(scraper):
    """Test rate limit handling"""
    # Configure rate limiter for test
    scraper.rate_limiter = RateLimiter(default_rate_limit=1)
    
    # First request should succeed
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    
    with patch("httpx.AsyncClient.request", AsyncMock(return_value=mock_response)):
        result1 = await scraper._safe_fetch("https://test.com/api")
        assert result1 == {"data": "test"}
        
        # Second request should be rate limited
        with pytest.raises(NetworkError):
            await scraper._safe_fetch("https://test.com/api")

@pytest.mark.asyncio
async def test_proxy_rotation(scraper, mock_proxy):
    """Test proxy rotation functionality"""
    # Configure proxy manager
    scraper.proxy_manager = ProxyManager(proxies=[mock_proxy])
    
    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {"data": "test"}
    
    with patch("httpx.AsyncClient.request", AsyncMock(return_value=success_response)):
        result = await scraper._safe_fetch("https://test.com/api")
        assert result == {"data": "test"}
        
        # Verify proxy was used
        proxy_score = scraper.proxy_manager._proxy_performance["test.com"][mock_proxy]
        assert proxy_score > 0

@pytest.mark.asyncio
async def test_error_handling(scraper):
    """Test error handling for various scenarios"""
    # Test network error
    with patch("httpx.AsyncClient.request", AsyncMock(side_effect=httpx.NetworkError("Connection failed"))):
        with pytest.raises(NetworkError):
            await scraper._safe_fetch("https://test.com/api")

    # Test timeout error
    with patch("httpx.AsyncClient.request", AsyncMock(side_effect=httpx.TimeoutException("Timeout"))):
        with pytest.raises(NetworkError):
            await scraper._safe_fetch("https://test.com/api")

    # Test 429 response
    rate_limit_response = Mock()
    rate_limit_response.status_code = 429
    with patch("httpx.AsyncClient.request", AsyncMock(return_value=rate_limit_response)):
        result = await scraper._safe_fetch("https://test.com/api")
        assert result is None

@pytest.mark.asyncio
async def test_browser_fallback(scraper):
    """Test fallback to browser-based scraping"""
    # Mock network error to trigger fallback
    with patch("httpx.AsyncClient.request", AsyncMock(side_effect=httpx.NetworkError("Connection failed"))):
        # Mock browser content
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>Test</html>")
        
        # Mock browser manager
        mock_browser_manager = AsyncMock()
        mock_browser_manager.get_session = AsyncMock(return_value=mock_page)
        
        with patch("src.aggregator.components.browser_manager.PersistentBrowserManager.get_instance", 
                  AsyncMock(return_value=mock_browser_manager)):
            result = await scraper._safe_fetch("https://test.com/api")
            assert result == {"html_content": "<html>Test</html>"}

@pytest.mark.asyncio
async def test_cleanup(scraper):
    """Test cleanup functionality"""
    mock_browser_manager = AsyncMock()
    scraper._browser_manager = mock_browser_manager
    
    await scraper.close()
    mock_browser_manager.close_sessions.assert_called_once()

@pytest.mark.asyncio
async def test_metrics_tracking(scraper, mock_response):
    """Test metrics collection"""
    with patch("httpx.AsyncClient.request", AsyncMock(return_value=mock_response)):
        await scraper._safe_fetch("https://test.com/api")
        
        # Verify metrics were recorded
        stats = scraper.metrics.get_domain_stats("test.com")
        assert stats["success_rate"] > 0
        assert stats["error_count"] == 0

@pytest.mark.asyncio
async def test_request_headers(scraper, mock_response):
    """Test request header generation"""
    with patch("httpx.AsyncClient.request", AsyncMock(return_value=mock_response)) as mock_request:
        await scraper._safe_fetch("https://test.com/api")
        
        # Verify headers were set
        call_kwargs = mock_request.call_args[1]
        headers = call_kwargs["headers"]
        assert "User-Agent" in headers
        assert "Accept-Language" in headers
        assert "Referer" in headers
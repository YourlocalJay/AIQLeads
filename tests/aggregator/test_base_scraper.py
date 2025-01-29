"""
Test suite for the enhanced BaseScraper implementation.
Validates retry mechanisms, circuit breakers, and reliability features.
"""

import pytest
import asyncio
import httpx
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import random

from src.aggregator.base_scraper import BaseScraper, with_retry
from src.aggregator.exceptions import NetworkError, ScraperError
from src.aggregator.components.circuit_breaker import CircuitBreaker

class TestScraper(BaseScraper):
    """Test implementation of BaseScraper"""
    def __init__(self, base_url="http://test.com", **kwargs):
        super().__init__(base_url, **kwargs)
        
    async def scrape(self, query=None):
        return await self._safe_fetch(f"{self.base_url}/test")

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing"""
    with patch('httpx.AsyncClient') as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        yield client

@pytest.fixture
async def scraper():
    """Create test scraper instance"""
    scraper = TestScraper(
        base_url="http://test.com",
        default_rate_limit=10,
        circuit_breaker_threshold=3
    )
    return scraper

class TestBaseScraper:
    """Test cases for enhanced BaseScraper functionality"""

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, scraper, mock_httpx_client):
        """Test retry mechanism with exponential backoff"""
        # Fail twice, succeed on third try
        responses = [
            AsyncMock(status_code=500),
            AsyncMock(status_code=500),
            AsyncMock(status_code=200, json=AsyncMock(return_value={"data": "success"}))
        ]
        mock_httpx_client.request.side_effect = responses
        
        result = await scraper._safe_fetch("http://test.com/api")
        
        assert result == {"data": "success"}
        assert mock_httpx_client.request.call_count == 3
        
        # Verify increasing delays between retries
        calls = mock_httpx_client.request.call_args_list
        timestamps = [call[1].get('timestamp', datetime.now()) for call in calls]
        delays = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
        assert all(d2 > d1 for d1, d2 in zip(delays[:-1], delays[1:]))

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, scraper, mock_httpx_client):
        """Test circuit breaker activation and recovery"""
        domain = "test.com"
        circuit_breaker = scraper.get_circuit_breaker(domain)
        
        # Simulate consistent failures
        mock_httpx_client.request.side_effect = NetworkError("Connection failed")
        
        # Should fail after circuit_breaker_threshold attempts
        with pytest.raises(NetworkError):
            for _ in range(circuit_breaker.failure_threshold + 1):
                await scraper._safe_fetch("http://test.com/api")
        
        # Verify circuit breaker is open
        assert not circuit_breaker.can_execute()
        
        # Wait for circuit breaker timeout
        await asyncio.sleep(circuit_breaker.recovery_timeout)
        
        # Should allow requests again
        mock_httpx_client.request.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value={"data": "success"})
        )
        result = await scraper._safe_fetch("http://test.com/api")
        assert result == {"data": "success"}

    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraper, mock_httpx_client):
        """Test rate limiting behavior and auto-adjustment"""
        domain = "test.com"
        
        # Set up successful response with rate limit headers
        mock_httpx_client.request.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value={"data": "success"}),
            headers={"X-RateLimit-Limit": "2"}
        )
        
        # Make requests in quick succession
        results = []
        for _ in range(3):
            result = await scraper._safe_fetch("http://test.com/api")
            results.append(result is not None)
        
        # Verify rate limit was updated from headers
        assert scraper.rate_limiter.get_limit(domain) == 2
        
        # First two should succeed, third should be rate limited
        assert results == [True, True, False]
        
        # Wait for rate limit reset
        await asyncio.sleep(60/2)  # Wait for rate limit window
        result = await scraper._safe_fetch("http://test.com/api")
        assert result == {"data": "success"}

    @pytest.mark.asyncio
    async def test_browser_fallback(self, scraper):
        """Test browser fallback mechanism with timeouts"""
        with patch('httpx.AsyncClient') as http_mock:
            # Make HTTP request fail
            http_mock.return_value.__aenter__.return_value.request.side_effect = \
                NetworkError("Connection failed")
            
            with patch.object(scraper, '_get_browser_manager') as browser_mock:
                # Set up successful browser response
                page_mock = AsyncMock()
                page_mock.goto = AsyncMock()
                page_mock.content = AsyncMock(return_value="<html>Success</html>")
                
                browser_manager = AsyncMock()
                browser_manager.get_session.return_value = page_mock
                browser_mock.return_value = browser_manager
                
                # Test successful browser fallback
                result = await scraper._safe_fetch("http://test.com/api")
                assert result == {"html_content": "<html>Success</html>"}
                
                # Verify timeout was set
                page_mock.goto.assert_called_with("http://test.com/api", timeout=15000)
                
                # Test browser timeout
                page_mock.goto.side_effect = asyncio.TimeoutError()
                with pytest.raises(NetworkError) as exc_info:
                    await scraper._safe_fetch("http://test.com/api")
                assert "Browser fallback timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check(self, scraper):
        """Test comprehensive health check system"""
        # Test all components healthy
        assert await scraper._health_check() == True
        
        # Test component failures
        async def test_component_failure(component, method):
            with patch.object(component, method, return_value=False):
                assert await scraper._health_check() == False
        
        await test_component_failure(scraper.rate_limiter, 'is_healthy')
        await test_component_failure(scraper.proxy_manager, 'is_healthy')
        
        # Test circuit breaker status check
        domain = "test.com"
        circuit_breaker = scraper.get_circuit_breaker(domain)
        for _ in range(circuit_breaker.failure_threshold):
            circuit_breaker.record_failure()
        assert await scraper._health_check() == False

    @pytest.mark.asyncio
    async def test_metrics_collection(self, scraper, mock_httpx_client):
        """Test comprehensive metrics collection"""
        domain = "test.com"
        
        # Test successful request metrics
        mock_httpx_client.request.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value={"data": "success"})
        )
        
        await scraper._safe_fetch("http://test.com/api")
        metrics = scraper.metrics.get_stats()
        
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 0
        
        # Test retry metrics
        mock_httpx_client.request.side_effect = [
            NetworkError("Connection failed"),
            AsyncMock(status_code=200, json=AsyncMock(return_value={"data": "success"}))
        ]
        
        await scraper._safe_fetch("http://test.com/api")
        metrics = scraper.metrics.get_stats()
        
        assert metrics["retry_attempts"] == 1
        assert metrics["retry_success"] == 1
        
        # Test circuit breaker metrics
        mock_httpx_client.request.side_effect = NetworkError("Connection failed")
        with pytest.raises(NetworkError):
            for _ in range(scraper.circuit_breaker_threshold + 1):
                await scraper._safe_fetch("http://test.com/api")
        
        metrics = scraper.metrics.get_stats()
        assert metrics["circuit_breaker_trips"] > 0
        
        # Test browser fallback metrics
        with patch.object(scraper, '_get_browser_manager') as browser_mock:
            page_mock = AsyncMock()
            page_mock.goto = AsyncMock()
            page_mock.content = AsyncMock(return_value="<html>Success</html>")
            
            browser_manager = AsyncMock()
            browser_manager.get_session.return_value = page_mock
            browser_mock.return_value = browser_manager
            
            await scraper._safe_fetch("http://test.com/api")
            
        metrics = scraper.metrics.get_stats()
        assert metrics["browser_fallback_success"] > 0

    @pytest.mark.asyncio
    async def test_cleanup(self, scraper):
        """Test resource cleanup"""
        # Initialize browser manager
        with patch.object(scraper, '_get_browser_manager') as browser_mock:
            browser_manager = AsyncMock()
            browser_mock.return_value = browser_manager
            
            # Test cleanup
            await scraper.close()
            
            # Verify browser sessions were closed
            browser_manager.close_sessions.assert_called_once()
            
            # Verify metrics were recorded
            metrics = scraper.metrics.get_stats()
            assert metrics["cleanup_success"] == 1

if __name__ == "__main__":
    pytest.main(["-v", __file__])
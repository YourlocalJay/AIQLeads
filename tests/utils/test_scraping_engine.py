"""Tests for scraping engine with resilience and error handling"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.utils.scraping_engine import (
    ScrapingEngine,
    CacheManager,
    ProxyManager,
    RateLimiter,
    MetricsCollector,
)


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.status = 200
    response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
    return response


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.get = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_proxy_manager():
    manager = ProxyManager()
    manager.get_proxy = AsyncMock(return_value="http://proxy:8080")
    manager.mark_failed = AsyncMock()
    manager.mark_successful = AsyncMock()
    return manager


@pytest.fixture
def mock_cache():
    cache = CacheManager()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_rate_limiter():
    limiter = RateLimiter(requests_per_minute=60)
    limiter.acquire = AsyncMock()
    return limiter


@pytest.fixture
def mock_metrics():
    metrics = MetricsCollector()
    metrics.record_timing = AsyncMock()
    metrics.increment_counter = AsyncMock()
    return metrics


@pytest.fixture
def scraping_engine(
    mock_session, mock_proxy_manager, mock_cache, mock_rate_limiter, mock_metrics
):
    return ScrapingEngine(
        session=mock_session,
        proxy_manager=mock_proxy_manager,
        cache_manager=mock_cache,
        rate_limiter=mock_rate_limiter,
        metrics_collector=mock_metrics,
    )


@pytest.mark.asyncio
async def test_successful_scrape(scraping_engine, mock_response):
    """Test successful web scraping"""
    scraping_engine.session.get.return_value = mock_response

    url = "http://example.com"
    content = await scraping_engine.scrape(url)

    assert "Test content" in content
    await scraping_engine.metrics_collector.increment_counter.assert_called_with(
        "successful_scrapes"
    )


@pytest.mark.asyncio
async def test_cache_hit(scraping_engine):
    """Test cache hit scenario"""
    cached_content = "<html>Cached content</html>"
    scraping_engine.cache_manager.get.return_value = cached_content

    content = await scraping_engine.scrape("http://example.com")

    assert content == cached_content
    scraping_engine.session.get.assert_not_called()


@pytest.mark.asyncio
async def test_proxy_rotation(scraping_engine, mock_response):
    """Test proxy rotation on failure"""
    responses = [
        AsyncMock(status=503),  # First proxy fails
        mock_response,  # Second proxy succeeds
    ]
    scraping_engine.session.get.side_effect = responses

    await scraping_engine.scrape("http://example.com")

    assert scraping_engine.proxy_manager.mark_failed.call_count == 1
    assert scraping_engine.proxy_manager.mark_successful.call_count == 1


@pytest.mark.asyncio
async def test_rate_limiting(scraping_engine, mock_response):
    """Test rate limiting functionality"""
    scraping_engine.session.get.return_value = mock_response

    await asyncio.gather(
        scraping_engine.scrape("http://example.com/1"),
        scraping_engine.scrape("http://example.com/2"),
    )

    assert scraping_engine.rate_limiter.acquire.call_count == 2


@pytest.mark.asyncio
async def test_retry_behavior(scraping_engine, mock_response):
    """Test retry behavior on temporary failures"""
    responses = [AsyncMock(status=500), AsyncMock(status=503), mock_response]
    scraping_engine.session.get.side_effect = responses

    content = await scraping_engine.scrape("http://example.com")

    assert "Test content" in content
    assert scraping_engine.session.get.call_count == 3


@pytest.mark.asyncio
async def test_metrics_collection(scraping_engine, mock_response):
    """Test metrics collection during scraping"""
    scraping_engine.session.get.return_value = mock_response

    await scraping_engine.scrape("http://example.com")

    # Should record timing and increment counters
    assert scraping_engine.metrics_collector.record_timing.called
    assert scraping_engine.metrics_collector.increment_counter.called


@pytest.mark.asyncio
async def test_error_handling(scraping_engine):
    """Test error handling and logging"""
    scraping_engine.session.get.side_effect = Exception("Network error")

    with pytest.raises(Exception):
        await scraping_engine.scrape("http://example.com")

    await scraping_engine.metrics_collector.increment_counter.assert_called_with(
        "scraping_errors"
    )


@pytest.mark.asyncio
async def test_concurrent_scraping(scraping_engine, mock_response):
    """Test concurrent scraping operations"""
    scraping_engine.session.get.return_value = mock_response

    urls = [f"http://example.com/{i}" for i in range(5)]
    tasks = [scraping_engine.scrape(url) for url in urls]

    results = await asyncio.gather(*tasks)
    assert len(results) == 5
    assert all("Test content" in result for result in results)


@pytest.mark.asyncio
async def test_proxy_blacklisting(scraping_engine):
    """Test proxy blacklisting on repeated failures"""
    scraping_engine.session.get.side_effect = Exception("Proxy error")

    with pytest.raises(Exception):
        await scraping_engine.scrape("http://example.com")

    assert scraping_engine.proxy_manager.mark_failed.called


@pytest.mark.asyncio
async def test_cache_expiration(scraping_engine, mock_response):
    """Test cache expiration handling"""
    scraping_engine.session.get.return_value = mock_response

    # First request - should cache
    await scraping_engine.scrape("http://example.com")

    # Simulate cache expiration
    scraping_engine.cache_manager.get.return_value = None

    # Second request - should fetch fresh
    await scraping_engine.scrape("http://example.com")

    assert scraping_engine.session.get.call_count == 2


@pytest.mark.asyncio
async def test_custom_parser(scraping_engine, mock_response):
    """Test custom content parser"""
    scraping_engine.session.get.return_value = mock_response

    async def custom_parser(content):
        return content.upper()

    result = await scraping_engine.scrape("http://example.com", parser=custom_parser)

    assert result == mock_response.text.return_value.upper()


@pytest.mark.asyncio
async def test_cleanup(scraping_engine):
    """Test resource cleanup"""
    await scraping_engine.cleanup()

    scraping_engine.session.close.assert_called_once()
    # Additional cleanup verifications can be added here

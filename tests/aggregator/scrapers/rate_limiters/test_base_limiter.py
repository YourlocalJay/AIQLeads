import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import aioredis
from src.aggregator.scrapers.rate_limiters.base_limiter import BaseRateLimiter, RateLimitState

class TestLimiter(BaseRateLimiter):
    async def acquire(self, endpoint: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        return await super().acquire(endpoint, max_retries, retry_delay)

@pytest.fixture
async def redis_mock():
    with patch('aioredis.Redis') as mock:
        yield mock

@pytest.fixture
async def limiter(redis_mock):
    limiter = TestLimiter(requests_per_minute=60, burst_limit=10, redis_url="redis://test")
    await limiter.initialize()
    yield limiter
    await limiter.shutdown()

@pytest.mark.asyncio
async def test_acquire_within_limits(limiter):
    assert await limiter.acquire("test_endpoint")
    metrics = await limiter.get_metrics("test_endpoint")
    assert metrics["current_requests"] == 1
    assert metrics["remaining"] == 9

@pytest.mark.asyncio
async def test_exceeds_burst_limit(limiter):
    for _ in range(10):
        assert await limiter.acquire("test_endpoint")
    assert not await limiter.acquire("test_endpoint")
    metrics = await limiter.get_metrics("test_endpoint")
    assert metrics["remaining"] == 0

@pytest.mark.asyncio
async def test_concurrent_access(limiter):
    results = await asyncio.gather(
        *[limiter.acquire("test_endpoint") for _ in range(12)]
    )
    assert sum(results) == 10

@pytest.mark.asyncio
async def test_cleanup_old_requests():
    with patch('src.aggregator.scrapers.rate_limiters.base_limiter.datetime') as mock_datetime:
        limiter = TestLimiter(requests_per_minute=60, burst_limit=5)
        await limiter.initialize()
        
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0)
        assert await limiter.acquire("test_endpoint")
        
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 2)
        await limiter._cleanup_endpoint("test_endpoint")
        metrics = await limiter.get_metrics("test_endpoint")
        assert metrics["current_requests"] == 0
        
        await limiter.shutdown()

@pytest.mark.asyncio
async def test_redis_persistence(redis_mock):
    redis_instance = AsyncMock()
    redis_mock.from_url.return_value = redis_instance
    
    # Test save state
    limiter = TestLimiter(requests_per_minute=60, burst_limit=10, redis_url="redis://test")
    await limiter.initialize()
    assert await limiter.acquire("test_endpoint")
    await limiter.shutdown()
    
    assert redis_instance.set.called
    saved_state = redis_instance.set.call_args[0][1]
    assert "test_endpoint" in saved_state
    
    # Test load state
    redis_instance.get.return_value = saved_state
    new_limiter = TestLimiter(requests_per_minute=60, burst_limit=10, redis_url="redis://test")
    await new_limiter.initialize()
    metrics = await new_limiter.get_metrics("test_endpoint")
    assert metrics["current_requests"] == 1
    await new_limiter.shutdown()

@pytest.mark.asyncio
async def test_exponential_backoff(limiter):
    with patch('asyncio.sleep') as sleep_mock:
        # Fill up the rate limit
        for _ in range(10):
            assert await limiter.acquire("test_endpoint")
            
        # Test backoff retry
        result = await limiter.acquire("test_endpoint", max_retries=3, retry_delay=1.0)
        assert not result
        
        # Verify exponential delays
        assert sleep_mock.call_count == 2
        assert sleep_mock.call_args_list[0][0][0] == 1.0
        assert sleep_mock.call_args_list[1][0][0] == 2.0

@pytest.mark.asyncio
async def test_graceful_shutdown(limiter):
    shutdown_task = asyncio.create_task(limiter.shutdown())
    await shutdown_task
    assert limiter._cleanup_task.done()

@pytest.mark.asyncio
async def test_metrics(limiter):
    assert await limiter.acquire("test_endpoint")
    metrics = await limiter.get_metrics("test_endpoint")
    assert metrics["requests_per_minute"] == 60
    assert metrics["burst_limit"] == 10
    assert metrics["current_requests"] == 1
    assert metrics["remaining"] == 9

@pytest.mark.asyncio
async def test_release(limiter):
    assert await limiter.acquire("test_endpoint")
    metrics_before = await limiter.get_metrics("test_endpoint")
    await limiter.release("test_endpoint")
    metrics_after = await limiter.get_metrics("test_endpoint")
    assert metrics_before["current_requests"] > metrics_after["current_requests"]
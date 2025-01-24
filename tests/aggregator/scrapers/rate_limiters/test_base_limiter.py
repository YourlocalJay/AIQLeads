import pytest
import asyncio
import signal
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
import aioredis
from src.aggregator.scrapers.rate_limiters.base_limiter import (
    BaseRateLimiter,
    RateLimitState,
    RedisConnection,
    RateLimitMetrics
)

class TestLimiter(BaseRateLimiter):
    async def acquire(self, endpoint: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        return await super().acquire(endpoint, max_retries, retry_delay)

@pytest.fixture
async def redis_mock():
    with patch('aioredis.Redis') as mock:
        yield mock

@pytest.fixture
async def limiter(redis_mock):
    limiter = TestLimiter(
        requests_per_minute=60,
        burst_limit=10,
        redis_url="redis://test",
        cleanup_interval=1
    )
    await limiter.initialize()
    yield limiter
    await limiter.shutdown()

@pytest.mark.asyncio
async def test_redis_connection_health_check():
    redis_conn = RedisConnection("redis://test")
    with patch('aioredis.Redis') as mock_redis:
        instance = AsyncMock()
        mock_redis.from_url.return_value = instance
        
        await redis_conn.initialize()
        await asyncio.sleep(0.1)  # Allow health check to run
        
        instance.ping.assert_called()
        await redis_conn.close()

@pytest.mark.asyncio
async def test_redis_connection_recovery():
    redis_conn = RedisConnection("redis://test")
    with patch('aioredis.Redis') as mock_redis:
        instance = AsyncMock()
        instance.ping.side_effect = [Exception("Connection lost"), None]
        mock_redis.from_url.return_value = instance
        
        await redis_conn.initialize()
        await asyncio.sleep(0.1)
        
        assert mock_redis.from_url.call_count == 2
        await redis_conn.close()

@pytest.mark.asyncio
async def test_state_persistence(redis_mock):
    redis_instance = AsyncMock()
    redis_mock.from_url.return_value = redis_instance
    
    limiter = TestLimiter(
        requests_per_minute=60,
        burst_limit=10,
        redis_url="redis://test"
    )
    await limiter.initialize()
    
    # Acquire some tokens
    assert await limiter.acquire("test_endpoint")
    assert await limiter.acquire("test_endpoint")
    
    # Verify state is saved
    await limiter.shutdown()
    assert redis_instance.set.called
    
    # Load state in new limiter
    saved_state = redis_instance.set.call_args[0][1]
    redis_instance.get.return_value = saved_state.encode()
    
    new_limiter = TestLimiter(
        requests_per_minute=60,
        burst_limit=10,
        redis_url="redis://test"
    )
    await new_limiter.initialize()
    
    metrics = await new_limiter.get_metrics("test_endpoint")
    assert metrics.current_requests == 2
    assert metrics.total_acquired == 2
    
    await new_limiter.shutdown()

@pytest.mark.asyncio
async def test_metrics_tracking(limiter):
    # Acquire tokens successfully
    assert await limiter.acquire("test_endpoint")
    assert await limiter.acquire("test_endpoint")
    
    # Exceed limit
    for _ in range(10):
        await limiter.acquire("test_endpoint")
    
    metrics = await limiter.get_metrics("test_endpoint")
    assert metrics.total_acquired == 10
    assert metrics.total_rejected > 0
    assert metrics.avg_request_rate > 0

@pytest.mark.asyncio
async def test_concurrent_access(limiter):
    async def acquire_token():
        return await limiter.acquire("test_endpoint")
    
    tasks = [acquire_token() for _ in range(15)]
    results = await asyncio.gather(*tasks)
    assert sum(results) == 10  # burst_limit

@pytest.mark.asyncio
async def test_graceful_shutdown(limiter):
    assert await limiter.acquire("test_endpoint")
    
    # Simulate long-running cleanup
    with patch('asyncio.sleep', side_effect=asyncio.TimeoutError):
        await limiter.shutdown(timeout=1)
    
    assert limiter._cleanup_task.done()

@pytest.mark.asyncio
async def test_cleanup_interval():
    with patch('src.aggregator.scrapers.rate_limiters.base_limiter.datetime') as mock_datetime:
        limiter = TestLimiter(
            requests_per_minute=60,
            burst_limit=5,
            cleanup_interval=1
        )
        await limiter.initialize()
        
        # Set initial time
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0)
        assert await limiter.acquire("test_endpoint")
        
        # Advance time past cleanup interval
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 2)
        await asyncio.sleep(1.1)  # Wait for cleanup
        
        metrics = await limiter.get_metrics("test_endpoint")
        assert metrics.current_requests == 0
        
        await limiter.shutdown()

@pytest.mark.asyncio
async def test_signal_handling():
    limiter = TestLimiter(requests_per_minute=60, burst_limit=5)
    await limiter.initialize()
    
    # Simulate SIGTERM
    with patch('asyncio.Event.set') as mock_set:
        limiter._signal_handler(signal.SIGTERM, None)
        mock_set.assert_called_once()
    
    await limiter.shutdown()
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.aggregator.scrapers.rate_limiters.base_limiter import BaseRateLimiter

class TestLimiter(BaseRateLimiter):
    async def acquire(self, endpoint: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        return await self._try_acquire(endpoint)

@pytest.mark.asyncio
async def test_acquire_within_limits():
    limiter = TestLimiter(requests_per_minute=60, burst_limit=10)
    assert await limiter.acquire("test_endpoint")
    
@pytest.mark.asyncio
async def test_exceeds_burst_limit():
    limiter = TestLimiter(requests_per_minute=60, burst_limit=2)
    assert await limiter.acquire("test_endpoint")
    assert await limiter.acquire("test_endpoint")
    assert not await limiter.acquire("test_endpoint")

@pytest.mark.asyncio
async def test_concurrent_access():
    limiter = TestLimiter(requests_per_minute=60, burst_limit=5)
    results = await asyncio.gather(
        *[limiter.acquire("test_endpoint") for _ in range(6)]
    )
    assert sum(results) == 5  # Only 5 should succeed

@pytest.mark.asyncio
async def test_cleanup_old_requests():
    with patch('src.aggregator.scrapers.rate_limiters.base_limiter.datetime') as mock_datetime:
        limiter = TestLimiter(requests_per_minute=60, burst_limit=5)
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0)
        assert await limiter.acquire("test_endpoint")
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 2)
        await limiter._cleanup_endpoint("test_endpoint")
        assert len(limiter._request_times["test_endpoint"]) == 0
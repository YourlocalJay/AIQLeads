import pytest
import asyncio
from datetime import datetime
from src.aggregator.scrapers.rate_limiters.facebook_limiter import FacebookRateLimiter

@pytest.mark.asyncio
async def test_facebook_retry_mechanism():
    limiter = FacebookRateLimiter()
    for _ in range(10):
        assert await limiter.acquire("test_endpoint")
    assert not await limiter.acquire("test_endpoint", max_retries=2, retry_delay=0.1)

@pytest.mark.asyncio
async def test_facebook_rate_limits():
    limiter = FacebookRateLimiter()
    assert await limiter.acquire("test_endpoint")
    assert len(limiter._request_times["test_endpoint"]) == 1
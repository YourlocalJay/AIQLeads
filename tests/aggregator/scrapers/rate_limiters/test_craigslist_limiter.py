import pytest
import asyncio
from datetime import datetime
from src.aggregator.scrapers.rate_limiters.craigslist_limiter import CraigslistRateLimiter

@pytest.mark.asyncio
async def test_craigslist_retry_mechanism():
    limiter = CraigslistRateLimiter()
    for _ in range(5):
        assert await limiter.acquire("test_endpoint")
    assert not await limiter.acquire("test_endpoint", max_retries=2, retry_delay=0.1)

@pytest.mark.asyncio
async def test_craigslist_rate_limits():
    limiter = CraigslistRateLimiter()
    assert await limiter.acquire("test_endpoint")
    assert len(limiter._request_times["test_endpoint"]) == 1
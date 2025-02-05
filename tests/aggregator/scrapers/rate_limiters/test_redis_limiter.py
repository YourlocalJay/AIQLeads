"""Tests for Redis-backed rate limiter with AI-driven batching"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from redis.exceptions import RedisError
from src.aggregator.scrapers.rate_limiters.redis_limiter import RateLimiter


@pytest.fixture
def redis_urls():
    return ["redis://primary:6379", "redis://secondary:6379", "redis://tertiary:6379"]


@pytest.fixture
def mock_redis():
    with patch("redis.asyncio.Redis.from_url") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def rate_limiter(redis_urls, mock_redis):
    return RateLimiter(
        requests_per_minute=100, redis_urls=redis_urls, key_prefix="test", batch_size=10
    )


@pytest.mark.asyncio
async def test_key_prefix_validation():
    """Test key prefix validation rules"""
    with pytest.raises(ValueError):
        RateLimiter(
            requests_per_minute=100,
            redis_urls=["redis://localhost"],
            key_prefix="invalid:prefix",
        )

    with pytest.raises(ValueError):
        RateLimiter(
            requests_per_minute=100,
            redis_urls=["redis://localhost"],
            key_prefix="a" * 33,  # Too long
        )


@pytest.mark.asyncio
async def test_batch_size_validation():
    """Test batch size validation"""
    with pytest.raises(ValueError):
        RateLimiter(
            requests_per_minute=100, redis_urls=["redis://localhost"], batch_size=0
        )

    with pytest.raises(ValueError):
        RateLimiter(
            requests_per_minute=100, redis_urls=["redis://localhost"], batch_size=-1
        )


@pytest.mark.asyncio
async def test_acquire_batch_success(rate_limiter, mock_redis):
    """Test successful batch acquisition"""
    mock_redis.execute.return_value = 5  # Allow 5 requests

    items = list(range(10))
    result = await rate_limiter.acquire_batch("test_endpoint", items)

    assert len(result) == 5
    assert result == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_acquire_batch_redis_failure(rate_limiter, mock_redis):
    """Test fallback behavior on Redis failure"""
    mock_redis.execute.side_effect = RedisError("Connection failed")

    items = list(range(5))
    result = await rate_limiter.acquire_batch("test_endpoint", items)

    # Should fall back to local limiter
    assert len(result) > 0
    assert rate_limiter._local_limiter is not None


@pytest.mark.asyncio
async def test_acquire_batch_retry(rate_limiter, mock_redis):
    """Test retry behavior on temporary failures"""
    mock_redis.execute.side_effect = [
        RedisError("Temporary failure"),
        5,  # Succeed on second attempt
    ]

    items = list(range(10))
    result = await rate_limiter.acquire_batch("test_endpoint", items)

    assert len(result) == 5
    assert rate_limiter._local_limiter is None  # Shouldn't use fallback


@pytest.mark.asyncio
async def test_metrics_tracking(rate_limiter):
    """Test metrics collection and reporting"""
    # Simulate some activity
    await rate_limiter._update_metrics(5, 2)
    await rate_limiter._update_metrics(3, 0)

    metrics = await rate_limiter.get_enhanced_metrics("test_endpoint")

    assert metrics["total_processed_items"] == 10
    assert metrics["batch_success_rate"] > 0
    assert "redis_failures" in metrics


@pytest.mark.asyncio
async def test_adaptive_batch_sizing(rate_limiter):
    """Test AI-driven batch size adaptation"""
    # Simulate high success rate
    rate_limiter._rolling_buffer.extend([1.0] * 10)

    initial_size = rate_limiter.batch_size
    adapted_size = rate_limiter._adaptive_batch_size()

    assert adapted_size > initial_size
    assert adapted_size <= 100  # Should respect max limit


@pytest.mark.asyncio
async def test_redis_failover(rate_limiter, redis_urls):
    """Test Redis instance failover"""
    original_url = rate_limiter.redis_url
    await rate_limiter.switch_redis_instance()

    assert rate_limiter.redis_url != original_url
    assert rate_limiter.redis_url in redis_urls


@pytest.mark.asyncio
async def test_concurrent_access(rate_limiter, mock_redis):
    """Test concurrent batch processing"""
    mock_redis.execute.return_value = 3  # Allow 3 requests per batch

    async def process_batch(items):
        return await rate_limiter.acquire_batch("test_endpoint", items)

    # Launch concurrent batch processes
    tasks = []
    for i in range(3):
        items = list(range(i * 5, (i + 1) * 5))
        tasks.append(asyncio.create_task(process_batch(items)))

    results = await asyncio.gather(*tasks)

    # Verify results
    for batch in results:
        assert len(batch) <= 3  # Should respect rate limit

    # Check metrics
    metrics = await rate_limiter.get_enhanced_metrics("test_endpoint")
    assert metrics["total_processed_items"] > 0


@pytest.mark.asyncio
async def test_fallback_disabled(mock_redis):
    """Test behavior when fallback is disabled"""
    limiter = RateLimiter(
        requests_per_minute=100,
        redis_urls=["redis://localhost"],
        fallback_enabled=False,
    )

    mock_redis.execute.side_effect = RedisError("Connection failed")

    with pytest.raises(RedisError):
        await limiter.acquire_batch("test_endpoint", [1, 2, 3])


@pytest.mark.asyncio
async def test_metrics_initialization(rate_limiter):
    """Test metrics are properly initialized"""
    metrics = rate_limiter._metrics

    assert metrics["total_requests"] == 0
    assert metrics["successful_batches"] == 0
    assert metrics["partial_batches"] == 0
    assert metrics["failed_batches"] == 0
    assert metrics["redis_failures"] == 0


@pytest.mark.asyncio
async def test_redis_key_generation(rate_limiter):
    """Test Redis key generation and format"""
    endpoint = "user_api"
    key = rate_limiter._get_redis_key(endpoint)

    assert key.startswith(rate_limiter.key_prefix)
    assert endpoint in key
    assert ":" in key  # Should use proper separator


@pytest.mark.asyncio
async def test_batch_partial_success(rate_limiter, mock_redis):
    """Test handling of partially successful batches"""
    mock_redis.execute.side_effect = [2, 1]  # Two separate partial successes

    items = list(range(5))
    result = await rate_limiter.acquire_batch("test_endpoint", items)

    assert len(result) == 3  # Should get both partial results
    metrics = await rate_limiter.get_enhanced_metrics("test_endpoint")
    assert metrics["partial_batches"] > 0

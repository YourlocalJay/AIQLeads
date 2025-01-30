"""Tests for advanced processing utilities"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.utils.advanced_processing import (
    ProcessingPipeline,
    CacheManager,
    BatchProcessor,
    RateLimiter,
    MetricsCollector,
    DataProcessor
)

@pytest.fixture
def sample_data():
    return [
        {"id": i, "value": f"test_{i}"}
        for i in range(10)
    ]

@pytest.fixture
def mock_cache():
    return CacheManager(max_size=100, ttl=300)

@pytest.fixture
def mock_rate_limiter():
    return RateLimiter(requests_per_minute=60)

@pytest.fixture
def mock_metrics():
    return MetricsCollector()

@pytest.fixture
def pipeline(mock_cache, mock_rate_limiter, mock_metrics):
    return ProcessingPipeline(
        cache_manager=mock_cache,
        rate_limiter=mock_rate_limiter,
        metrics_collector=mock_metrics
    )

@pytest.mark.asyncio
async def test_batch_processor_chunking():
    """Test batch processor chunk management"""
    processor = BatchProcessor(chunk_size=3)
    data = list(range(10))
    
    chunks = [chunk async for chunk in processor.process(data)]
    
    assert len(chunks) == 4
    assert chunks[0] == [0, 1, 2]
    assert chunks[-1] == [9]

@pytest.mark.asyncio
async def test_cache_manager():
    """Test cache operations"""
    cache = CacheManager(max_size=2, ttl=0.1)
    
    # Test basic set/get
    await cache.set("key1", "value1")
    value = await cache.get("key1")
    assert value == "value1"
    
    # Test expiration
    await asyncio.sleep(0.2)
    value = await cache.get("key1")
    assert value is None
    
    # Test size limit
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    
    assert await cache.get("key1") is None
    assert await cache.get("key3") == "value3"

@pytest.mark.asyncio
async def test_rate_limiter_throttling():
    """Test rate limiter throttling"""
    limiter = RateLimiter(requests_per_minute=60)
    start_time = asyncio.get_event_loop().time()
    
    for _ in range(5):
        await limiter.acquire()
    
    duration = asyncio.get_event_loop().time() - start_time
    assert duration >= 0.2  # Should take at least 200ms for 5 requests

@pytest.mark.asyncio
async def test_metrics_collector():
    """Test metrics collection and aggregation"""
    collector = MetricsCollector()
    
    await collector.record_timing("process", 0.1)
    await collector.record_timing("process", 0.2)
    
    metrics = await collector.get_metrics()
    assert metrics["process"]["avg"] == pytest.approx(0.15)
    assert metrics["process"]["count"] == 2

@pytest.mark.asyncio
async def test_pipeline_processing(pipeline, sample_data):
    """Test end-to-end pipeline processing"""
    result = await pipeline.process_batch(sample_data)
    
    assert len(result) == len(sample_data)
    metrics = await pipeline.metrics_collector.get_metrics()
    assert metrics["batch_processing"]["count"] > 0

@pytest.mark.asyncio
async def test_cache_hit_ratio(pipeline, sample_data):
    """Test cache effectiveness"""
    # First run - should miss cache
    await pipeline.process_batch(sample_data)
    
    # Second run - should hit cache
    await pipeline.process_batch(sample_data)
    
    metrics = await pipeline.metrics_collector.get_metrics()
    assert metrics["cache_hits"]["count"] > 0

@pytest.mark.asyncio
async def test_data_processor_validation():
    """Test data validation and processing"""
    processor = DataProcessor()
    
    valid_data = {"id": 1, "name": "test"}
    invalid_data = {"id": "not_a_number", "name": 123}
    
    processed = await processor.process(valid_data)
    assert processed["id"] == 1
    
    with pytest.raises(ValueError):
        await processor.process(invalid_data)

@pytest.mark.asyncio
async def test_pipeline_error_handling(pipeline):
    """Test pipeline error handling"""
    invalid_data = [{"id": "invalid"}]
    
    with pytest.raises(ValueError):
        await pipeline.process_batch(invalid_data)
    
    metrics = await pipeline.metrics_collector.get_metrics()
    assert metrics["errors"]["count"] > 0

@pytest.mark.asyncio
async def test_concurrent_processing(pipeline, sample_data):
    """Test concurrent batch processing"""
    tasks = [
        pipeline.process_batch(sample_data)
        for _ in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    assert all(len(r) == len(sample_data) for r in results)

@pytest.mark.asyncio
async def test_metrics_aggregation(pipeline, sample_data):
    """Test metrics aggregation over time"""
    for _ in range(3):
        await pipeline.process_batch(sample_data)
        
    metrics = await pipeline.metrics_collector.get_metrics()
    
    assert "batch_processing" in metrics
    assert "latency" in metrics
    assert metrics["batch_processing"]["count"] == 3

@pytest.mark.asyncio
async def test_rate_limiter_backpressure():
    """Test rate limiter backpressure handling"""
    limiter = RateLimiter(requests_per_minute=30)
    start_time = asyncio.get_event_loop().time()
    
    async def worker():
        for _ in range(10):
            await limiter.acquire()
    
    await asyncio.gather(worker(), worker())
    
    duration = asyncio.get_event_loop().time() - start_time
    assert duration >= 0.8  # Should take time due to rate limiting

@pytest.mark.asyncio
async def test_cache_eviction(mock_cache):
    """Test cache eviction policies"""
    # Fill cache
    for i in range(150):
        await mock_cache.set(f"key_{i}", f"value_{i}")
    
    # Check size maintained
    size = await mock_cache.get_size()
    assert size <= 100
    
    # Check oldest entries evicted
    assert await mock_cache.get("key_0") is None
    assert await mock_cache.get("key_149") is not None
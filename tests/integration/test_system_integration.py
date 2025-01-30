"""Integration tests for AIQLeads system components"""

import pytest
import asyncio
import time
import logging
from unittest.mock import AsyncMock
from src.utils.performance_optimizer import AIQOptimizer, AIQResourcePool
from src.utils.retry import RetryStrategy, AsyncRetryStrategy
from src.utils.advanced_processing import ProcessingPipeline, BatchProcessor
from src.utils.scraping_engine import ScrapingEngine
from src.aggregator.scrapers.rate_limiters.redis_limiter import RateLimiter

@pytest.fixture
async def system_components():
    """Initialize all system components with real connections"""
    optimizer = AIQOptimizer()
    retry_strategy = AsyncRetryStrategy(max_retries=3)
    processor = ProcessingPipeline()
    rate_limiter = RateLimiter(
        requests_per_minute=100,
        redis_urls=["redis://localhost:6379"]
    )
    
    yield {
        'optimizer': optimizer,
        'retry_strategy': retry_strategy,
        'processor': processor,
        'rate_limiter': rate_limiter
    }
    
    # Cleanup
    await optimizer.cleanup()
    await processor.cleanup()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_processing(system_components):
    """Test complete data processing pipeline"""
    test_data = [{"id": i, "value": f"test_{i}"} for i in range(100)]
    
    # Process through optimizer with rate limiting
    async def process_batch(batch):
        await system_components['rate_limiter'].acquire_batch("test", batch)
        return await system_components['processor'].process_batch(batch)
    
    results = await system_components['optimizer'].optimize_pipeline(process_batch(test_data))
    
    assert len(results) == len(test_data)
    metrics = await system_components['optimizer'].telemetry.get_realtime_stats()
    assert metrics['throughput_1m'] > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_with_rate_limiting(system_components):
    """Test retry mechanism with rate limiting"""
    failure_count = 0
    
    @system_components['retry_strategy'].retry
    async def flaky_operation():
        nonlocal failure_count
        await system_components['rate_limiter'].acquire_batch("test", ["data"])
        
        if failure_count < 2:
            failure_count += 1
            raise ConnectionError("Simulated failure")
        return "success"
    
    result = await flaky_operation()
    assert result == "success"
    assert failure_count == 2

@pytest.mark.integration
@pytest.mark.asyncio
async def test_resource_pool_with_processing(system_components):
    """Test resource pool with batch processing"""
    pool = AIQResourcePool(
        factory=lambda: BatchProcessor(chunk_size=10),
        cleanup=lambda x: x.cleanup()
    )
    
    data = list(range(100))
    results = []
    
    async with pool.acquire() as processor:
        async for chunk in processor.process(data):
            results.extend(await system_components['processor'].process_batch(chunk))
    
    assert len(results) == len(data)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scraping_with_optimization(system_components):
    """Test scraping engine with performance optimization"""
    scraper = ScrapingEngine()
    urls = [f"http://example.com/{i}" for i in range(5)]
    
    async def scrape_batch(batch):
        results = []
        for url in batch:
            try:
                content = await scraper.scrape(url)
                results.append(content)
            except Exception as e:
                results.append(None)
        return results
    
    # Process through optimizer
    results = await system_components['optimizer'].optimize_pipeline(scrape_batch(urls))
    
    metrics = await system_components['optimizer'].telemetry.get_realtime_stats()
    assert 'scraping_latency' in metrics

@pytest.mark.integration
@pytest.mark.asyncio
async def test_system_backpressure(system_components):
    """Test system behavior under pressure"""
    async def heavy_workload():
        data = [{"id": i, "value": "test"} for i in range(1000)]
        return await system_components['processor'].process_batch(data)
    
    # Launch concurrent workloads
    tasks = [heavy_workload() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # Verify system handled backpressure
    metrics = await system_components['optimizer'].telemetry.get_realtime_stats()
    assert metrics['cpu'] < 95  # System shouldn't be overwhelmed

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_propagation(system_components):
    """Test error handling across components"""
    error_count = 0
    
    @system_components['retry_strategy'].retry
    async def failing_operation():
        nonlocal error_count
        error_count += 1
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await failing_operation()
    
    metrics = await system_components['optimizer'].telemetry.get_realtime_stats()
    assert metrics['error_rate_1m'] > 0
    assert error_count > 1  # Should have retried

@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_aggregation(system_components):
    """Test metrics collection across components"""
    # Generate some activity
    data = [{"id": i} for i in range(50)]
    await system_components['processor'].process_batch(data)
    await asyncio.sleep(1)  # Allow metrics to update
    
    # Collect metrics from different components
    optimizer_metrics = await system_components['optimizer'].telemetry.get_realtime_stats()
    processor_metrics = await system_components['processor'].get_metrics()
    
    assert optimizer_metrics['throughput_1m'] > 0
    assert processor_metrics['processed_items'] == 50
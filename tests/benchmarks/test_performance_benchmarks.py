"""Performance benchmarks for AIQLeads components"""

import pytest
import asyncio
import time
import statistics
import logging
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from src.utils.performance_optimizer import AIQOptimizer
from src.utils.advanced_processing import ProcessingPipeline, BatchProcessor
from src.utils.scraping_engine import ScrapingEngine
from src.aggregator.scrapers.rate_limiters.redis_limiter import RateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def benchmark_data():
    """Generate test data for benchmarks"""
    return [{"id": i, "value": f"test_{i}"} for i in range(10000)]

@pytest.fixture
def large_benchmark_data():
    """Generate large test data set"""
    return [{"id": i, "value": f"test_{i}"} for i in range(100000)]

@asynccontextmanager
async def measure_time():
    """Context manager for timing operations"""
    start = time.monotonic()
    try:
        yield
    finally:
        duration = time.monotonic() - start
        logger.info(f"Operation took: {duration:.2f} seconds")
        return duration

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_batch_processing_throughput(benchmark_data):
    """Benchmark batch processing throughput"""
    processor = BatchProcessor(chunk_size=100)
    pipeline = ProcessingPipeline()
    
    durations = []
    batch_sizes = [50, 100, 200, 500]
    
    for batch_size in batch_sizes:
        processor.chunk_size = batch_size
        start = time.monotonic()
        
        async for chunk in processor.process(benchmark_data):
            await pipeline.process_batch(chunk)
            
        duration = time.monotonic() - start
        throughput = len(benchmark_data) / duration
        durations.append(duration)
        
        logger.info(f"Batch size {batch_size}: {throughput:.2f} items/second")
    
    assert statistics.mean(durations) < 10.0  # Expected performance threshold

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_optimization_engine_scaling(large_benchmark_data):
    """Benchmark optimization engine under load"""
    optimizer = AIQOptimizer()
    concurrency_levels = [5, 10, 20]
    
    for concurrency in concurrency_levels:
        start = time.monotonic()
        chunks = [large_benchmark_data[i::concurrency] for i in range(concurrency)]
        
        async def process_chunk(chunk):
            return await optimizer.optimize_pipeline(chunk)
        
        tasks = [process_chunk(chunk) for chunk in chunks]
        await asyncio.gather(*tasks)
        
        duration = time.monotonic() - start
        throughput = len(large_benchmark_data) / duration
        
        logger.info(f"Concurrency {concurrency}: {throughput:.2f} items/second")
        metrics = await optimizer.telemetry.get_realtime_stats()
        logger.info(f"System metrics: {metrics}")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_rate_limiter_performance():
    """Benchmark rate limiter under various loads"""
    limits = [100, 500, 1000]
    request_counts = [1000, 5000, 10000]
    
    for rpm in limits:
        limiter = RateLimiter(
            requests_per_minute=rpm,
            redis_urls=["redis://localhost:6379"]
        )
        
        for count in request_counts:
            start = time.monotonic()
            tasks = [limiter.acquire() for _ in range(count)]
            await asyncio.gather(*tasks)
            duration = time.monotonic() - start
            
            actual_rate = count / duration * 60
            logger.info(f"Target RPM: {rpm}, Actual RPM: {actual_rate:.2f}")
            assert actual_rate <= rpm * 1.1  # Allow 10% margin

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_scraping_engine_performance():
    """Benchmark scraping engine throughput"""
    scraper = ScrapingEngine()
    url_counts = [10, 50, 100]
    
    for count in url_counts:
        urls = [f"http://example.com/{i}" for i in range(count)]
        
        start = time.monotonic()
        tasks = [scraper.scrape(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.monotonic() - start
        
        success_rate = len([r for r in results if not isinstance(r, Exception)]) / len(urls)
        throughput = count / duration
        
        logger.info(f"URLs: {count}, Throughput: {throughput:.2f}/s, Success Rate: {success_rate:.2%}")

@pytest.mark.benchmark
def test_cpu_intensive_processing(benchmark_data):
    """Benchmark CPU-intensive operations"""
    def process_chunk(chunk):
        # Simulate CPU-intensive work
        result = []
        for item in chunk:
            processed = {
                "id": item["id"] ** 2,
                "value": "".join(sorted(item["value"] * 2)),
                "computed": sum(ord(c) for c in item["value"])
            }
            result.append(processed)
        return result
    
    chunk_sizes = [100, 500, 1000]
    
    for size in chunk_sizes:
        chunks = [benchmark_data[i:i + size] for i in range(0, len(benchmark_data), size)]
        
        start = time.monotonic()
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(process_chunk, chunks))
        duration = time.monotonic() - start
        
        items_per_second = len(benchmark_data) / duration
        logger.info(f"Chunk size {size}: {items_per_second:.2f} items/second")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_memory_usage_under_load(large_benchmark_data):
    """Benchmark memory usage patterns"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    pipeline = ProcessingPipeline()
    chunk_sizes = [100, 1000, 5000]
    
    for size in chunk_sizes:
        processor = BatchProcessor(chunk_size=size)
        
        # Process data and measure memory
        start_memory = process.memory_info().rss / 1024 / 1024
        async for chunk in processor.process(large_benchmark_data):
            await pipeline.process_batch(chunk)
        end_memory = process.memory_info().rss / 1024 / 1024
        
        logger.info(
            f"Chunk size {size}: Memory usage - "
            f"Start: {start_memory:.1f}MB, "
            f"End: {end_memory:.1f}MB, "
            f"Diff: {end_memory - start_memory:.1f}MB"
        )

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_system_recovery_time():
    """Benchmark system recovery after stress"""
    optimizer = AIQOptimizer()
    
    # Generate high load
    async def stress_test():
        data = list(range(1000))
        return await optimizer.optimize_pipeline(data)
    
    # Measure recovery time
    recovery_times = []
    for _ in range(3):
        # Generate stress
        tasks = [stress_test() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # Measure time to return to normal load
        start = time.monotonic()
        while True:
            metrics = await optimizer.telemetry.get_realtime_stats()
            if metrics['cpu'] < 50:  # System recovered
                break
            await asyncio.sleep(0.1)
            
        recovery_time = time.monotonic() - start
        recovery_times.append(recovery_time)
        logger.info(f"Recovery time: {recovery_time:.2f}s")
    
    avg_recovery = statistics.mean(recovery_times)
    assert avg_recovery < 5.0  # Expected recovery threshold
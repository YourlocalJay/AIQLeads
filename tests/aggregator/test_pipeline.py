"""
Test suite for the AIQLeads Aggregation Pipeline.
Validates core functionality, reliability features, and error handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import httpx
import redis.asyncio as redis

from src.aggregator.pipeline import AggregationPipeline
from src.aggregator.base_scraper import BaseScraper
from src.aggregator.exceptions import NetworkError, ParseError, PipelineError
from src.schemas.lead_schema import LeadCreate
from src.cache import RedisCache

# Test Data
SAMPLE_LEAD = {
    "source": "test_source",
    "name": "Test Lead",
    "email": "test@example.com",
    "phone": "123-456-7890"
}

class MockScraper(BaseScraper):
    """Mock scraper for testing"""
    def __init__(self, name="mock_scraper", should_fail=False):
        self.name = name
        self.should_fail = should_fail
        self.scrape_count = 0
        
    async def scrape(self):
        self.scrape_count += 1
        if self.should_fail:
            raise NetworkError("Simulated network failure")
        return [SAMPLE_LEAD]

class MockParser:
    """Mock parser for testing"""
    def __init__(self, name="mock_parser", should_fail=False):
        self.name = name
        self.should_fail = should_fail
        
    def parse(self, data):
        if self.should_fail:
            raise ParseError("Simulated parse failure")
        return LeadCreate(**data)

@pytest.fixture
async def pipeline():
    """Create test pipeline with mock components"""
    scraper = MockScraper()
    parser = MockParser()
    cache = RedisCache()
    pipeline = AggregationPipeline(
        scrapers=[scraper],
        parsers=[parser],
        cache=cache
    )
    return pipeline

@pytest.mark.asyncio
async def test_pipeline_basic_operation(pipeline):
    """Test basic pipeline functionality"""
    results = await pipeline.run_pipeline()
    assert len(results) == 1
    assert results[0].name == "Test Lead"

@pytest.mark.asyncio
async def test_circuit_breaker_activation():
    """Verify circuit breaker prevents excessive retries"""
    failing_scraper = MockScraper(should_fail=True)
    pipeline = AggregationPipeline(
        scrapers=[failing_scraper],
        parsers=[MockParser()],
        cache=RedisCache(),
        circuit_breaker_threshold=3
    )
    
    with pytest.raises(PipelineError) as exc_info:
        await pipeline.run_pipeline()
    
    assert "Circuit breaker triggered" in str(exc_info.value)
    assert failing_scraper.scrape_count <= 3

@pytest.mark.asyncio
async def test_exponential_backoff():
    """Verify retry delays follow exponential pattern"""
    start_times = []
    
    class TimingFailScraper(BaseScraper):
        async def scrape(self):
            start_times.append(datetime.now())
            raise NetworkError("Simulated failure")
    
    pipeline = AggregationPipeline(
        scrapers=[TimingFailScraper()],
        parsers=[MockParser()],
        cache=RedisCache()
    )
    
    with pytest.raises(PipelineError):
        await pipeline.run_pipeline()
    
    # Verify delays between attempts increase
    delays = [(t2 - t1).total_seconds() 
             for t1, t2 in zip(start_times[:-1], start_times[1:])]
    assert all(d2 > d1 for d1, d2 in zip(delays[:-1], delays[1:]))

@pytest.mark.asyncio
async def test_concurrent_processing():
    """Verify parallel processing of multiple scrapers"""
    class SlowScraper(BaseScraper):
        async def scrape(self):
            await asyncio.sleep(0.1)
            return [SAMPLE_LEAD]
    
    # Create multiple slow scrapers
    scrapers = [SlowScraper(f"slow_{i}") for i in range(5)]
    
    pipeline = AggregationPipeline(
        scrapers=scrapers,
        parsers=[MockParser()],
        cache=RedisCache()
    )
    
    start_time = datetime.now()
    results = await pipeline.run_pipeline()
    duration = (datetime.now() - start_time).total_seconds()
    
    # Should take ~0.1s, not 0.5s (if sequential)
    assert duration < 0.2
    assert len(results) == 5

@pytest.mark.asyncio
async def test_deduplication():
    """Verify duplicate leads are filtered"""
    class DupeScraper(BaseScraper):
        async def scrape(self):
            return [SAMPLE_LEAD, SAMPLE_LEAD.copy()]
    
    pipeline = AggregationPipeline(
        scrapers=[DupeScraper()],
        parsers=[MockParser()],
        cache=RedisCache()
    )
    
    results = await pipeline.run_pipeline()
    assert len(results) == 1  # Second lead should be filtered

@pytest.mark.asyncio
async def test_metrics_collection():
    """Verify metrics are properly collected"""
    pipeline = AggregationPipeline(
        scrapers=[MockScraper()],
        parsers=[MockParser()],
        cache=RedisCache()
    )
    
    await pipeline.run_pipeline()
    metrics = pipeline.metrics.get_stats()
    
    assert metrics["scraper_success"] == 1
    assert metrics["total_leads_processed"] == 1
    assert "processing_time" in metrics

@pytest.mark.asyncio
async def test_error_handling():
    """Verify proper handling of various error scenarios"""
    scenarios = [
        (MockScraper(should_fail=True), MockParser(), "NetworkError"),
        (MockScraper(), MockParser(should_fail=True), "ParseError"),
    ]
    
    for scraper, parser, expected_error in scenarios:
        pipeline = AggregationPipeline(
            scrapers=[scraper],
            parsers=[parser],
            cache=RedisCache()
        )
        
        with pytest.raises(Exception) as exc_info:
            await pipeline.run_pipeline()
        assert expected_error in str(exc_info.value)

@pytest.mark.asyncio
async def test_cache_failure_handling():
    """Verify graceful handling of cache failures"""
    class FailingCache(RedisCache):
        async def get(self, key):
            raise redis.RedisError("Simulated cache failure")
    
    pipeline = AggregationPipeline(
        scrapers=[MockScraper()],
        parsers=[MockParser()],
        cache=FailingCache()
    )
    
    # Should still work, just won't deduplicate
    results = await pipeline.run_pipeline()
    assert len(results) == 1

if __name__ == "__main__":
    pytest.main(["-v", __file__])
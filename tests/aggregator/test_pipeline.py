import pytest
from unittest.mock import AsyncMock

from src.aggregator.pipeline import AggregationPipeline
from src.aggregator.base_scraper import BaseScraper
from src.aggregator.base_parser import BaseParser
from src.aggregator.exceptions import (
    NetworkError,
)
from src.config import Settings


class MockScraper(BaseScraper):
    """Mock scraper for testing"""

    async def search(self, location, radius_km, **kwargs):
        return [{"id": 1, "raw": "data"}]


class MockParser(BaseParser):
    """Mock parser for testing"""

    async def parse_async(self, raw_data):
        return {"id": raw_data["id"], "processed": True}

    async def enhance_lead(self, lead):
        lead["enhanced"] = True
        return lead


@pytest.fixture
def mock_settings():
    return Settings(
        ZILLOW_API_KEY="test-key",
        ZILLOW_BASE_URL="https://api.zillow.com",
        FACEBOOK_API_KEY="test-key",
        FACEBOOK_BASE_URL="https://graph.facebook.com",
        LINKEDIN_API_KEY="test-key",
        LINKEDIN_BASE_URL="https://api.linkedin.com",
        FSBO_BASE_URL="https://fsbo.com",
    )


@pytest.fixture
def pipeline(mock_settings):
    return AggregationPipeline(settings=mock_settings)


@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline):
    """Test pipeline initialization"""
    await pipeline.initialize_components()
    assert pipeline._initialized
    assert len(pipeline.scrapers) > 0
    assert len(pipeline.parsers) > 0


@pytest.mark.asyncio
async def test_scraper_registration(pipeline):
    """Test scraper registration"""
    mock_scraper = MockScraper(base_url="https://test.com")
    await pipeline.register_scraper("test", mock_scraper)
    assert "test" in pipeline.scrapers
    assert pipeline.scrapers["test"] == mock_scraper


@pytest.mark.asyncio
async def test_parser_registration(pipeline):
    """Test parser registration"""
    mock_parser = MockParser()
    await pipeline.register_parser("test", mock_parser)
    assert "test" in pipeline.parsers
    assert pipeline.parsers["test"] == mock_parser


@pytest.mark.asyncio
async def test_aggregate_leads_success(pipeline):
    """Test successful lead aggregation"""
    # Register mock components
    mock_scraper = MockScraper(base_url="https://test.com")
    mock_parser = MockParser()
    await pipeline.register_scraper("test", mock_scraper)
    await pipeline.register_parser("test", mock_parser)

    # Run aggregation
    leads = await pipeline.aggregate_leads(
        location="Test Location", radius_km=50, sources=["test"]
    )

    assert len(leads) == 1
    assert leads[0]["processed"] is True
    assert leads[0]["enhanced"] is True


@pytest.mark.asyncio
async def test_aggregate_leads_with_batch_processing(pipeline):
    """Test lead aggregation with batch processing"""
    # Register multiple mock components
    for i in range(5):
        await pipeline.register_scraper(
            f"test{i}", MockScraper(base_url=f"https://test{i}.com")
        )
        await pipeline.register_parser(f"test{i}", MockParser())

    # Run aggregation with batch size
    leads = await pipeline.aggregate_leads(
        location="Test Location", radius_km=50, batch_size=2
    )

    assert len(leads) == 5
    assert all(lead["processed"] for lead in leads)
    assert all(lead["enhanced"] for lead in leads)


@pytest.mark.asyncio
async def test_error_handling(pipeline):
    """Test error handling in pipeline"""

    class ErrorScraper(BaseScraper):
        async def search(self, *args, **kwargs):
            raise NetworkError("Connection failed")

    # Register error-producing scraper
    await pipeline.register_scraper("error", ErrorScraper(base_url="https://test.com"))
    await pipeline.register_parser("error", MockParser())

    # Run aggregation
    leads = await pipeline.aggregate_leads(
        location="Test Location", radius_km=50, sources=["error"]
    )

    assert len(leads) == 0
    stats = await pipeline.get_pipeline_stats()
    assert stats["sources_failed"] > 0


@pytest.mark.asyncio
async def test_validation_handling(pipeline):
    """Test validation handling"""

    class InvalidLeadScraper(BaseScraper):
        async def search(self, *args, **kwargs):
            return [{"id": 1, "invalid": True}]

    # Register components
    await pipeline.register_scraper(
        "invalid", InvalidLeadScraper(base_url="https://test.com")
    )
    await pipeline.register_parser("invalid", MockParser())

    # Run aggregation
    leads = await pipeline.aggregate_leads(
        location="Test Location", radius_km=50, sources=["invalid"]
    )

    assert len(leads) == 0
    stats = await pipeline.get_pipeline_stats()
    assert stats["error_rates"]["validation"] > 0


@pytest.mark.asyncio
async def test_metrics_collection(pipeline):
    """Test metrics collection"""
    # Register mock components
    await pipeline.register_scraper("test", MockScraper(base_url="https://test.com"))
    await pipeline.register_parser("test", MockParser())

    # Run aggregation
    await pipeline.aggregate_leads(
        location="Test Location", radius_km=50, sources=["test"]
    )

    # Verify metrics
    stats = await pipeline.get_pipeline_stats()
    assert stats["total_leads_processed"] > 0
    assert stats["success_rate"] > 0
    assert "test" in stats["source_stats"]
    assert stats["source_stats"]["test"]["leads_found"] > 0


@pytest.mark.asyncio
async def test_cleanup(pipeline):
    """Test pipeline cleanup"""
    # Create mock scraper with cleanup
    mock_scraper = MockScraper(base_url="https://test.com")
    mock_scraper.cleanup = AsyncMock()

    # Register and run
    await pipeline.register_scraper("test", mock_scraper)
    async with pipeline.managed_session():
        pass

    # Verify cleanup was called
    mock_scraper.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_source_filtering(pipeline):
    """Test source filtering"""
    # Register multiple sources
    await pipeline.register_scraper("test1", MockScraper(base_url="https://test1.com"))
    await pipeline.register_scraper("test2", MockScraper(base_url="https://test2.com"))
    await pipeline.register_parser("test1", MockParser())
    await pipeline.register_parser("test2", MockParser())

    # Run with specific source
    leads = await pipeline.aggregate_leads(
        location="Test Location", radius_km=50, sources=["test1"]
    )

    assert len(leads) == 1
    stats = await pipeline.get_pipeline_stats()
    assert "test1" in stats["source_stats"]
    assert "test2" not in stats["source_stats"]

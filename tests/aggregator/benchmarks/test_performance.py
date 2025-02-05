import pytest
import asyncio
import time
import statistics
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from src.aggregator.scrapers import ZillowScraper, FacebookScraper
from src.aggregator.parsers import ZillowParser, FacebookParser
from src.config import settings


class TestAggregatorPerformance:
    @pytest.fixture
    def performance_metrics(self):
        """Fixture for collecting performance metrics"""
        return {
            "response_times": [],
            "memory_usage": [],
            "throughput": [],
            "error_rates": [],
        }

    @pytest.fixture
    def large_dataset(self):
        """Generate a large dataset for performance testing"""
        return [self._generate_mock_listing(i) for i in range(1000)]

    def _generate_mock_listing(self, index: int) -> Dict[str, Any]:
        """Generate mock listing data"""
        return {
            "zpid": f"{index}",
            "address": {
                "streetAddress": f"{index} Test St",
                "city": "San Francisco",
                "state": "CA",
                "zipcode": "94105",
            },
            "price": 1000000 + (index * 1000),
            "bedrooms": 3,
            "bathrooms": 2,
            "livingArea": 2000,
            "yearBuilt": 1985,
            "latitude": 37.7749 + (index * 0.0001),
            "longitude": -122.4194 + (index * 0.0001),
        }

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_parser_performance(self, large_dataset, performance_metrics):
        """Benchmark parser performance under load"""
        parser = ZillowParser()
        batch_sizes = [10, 50, 100, 500, 1000]
        results = {}

        for batch_size in batch_sizes:
            start_time = time.time()
            test_data = large_dataset[:batch_size]

            with ThreadPoolExecutor(max_workers=4) as executor:
                leads = list(executor.map(parser.parse, test_data))

            duration = time.time() - start_time
            throughput = batch_size / duration

            results[batch_size] = {
                "duration": duration,
                "throughput": throughput,
                "leads_processed": len(leads),
            }

            performance_metrics["throughput"].append(throughput)

        assert all(
            result["leads_processed"] == size for size, result in results.items()
        )
        assert (
            statistics.mean(performance_metrics["throughput"]) > 100
        )  # Min 100 leads/second

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_scraper_performance(self, performance_metrics):
        """Benchmark scraper performance with concurrent requests"""
        scraper = ZillowScraper(api_key=settings.ZILLOW_API_KEY, rate_limit=100)
        concurrent_requests = [5, 10, 20, 50]
        results = {}

        for num_requests in concurrent_requests:
            start_time = time.time()

            with patch.object(scraper, "_make_request") as mock_request:
                mock_request.return_value = self._generate_mock_listing(0)

                tasks = [
                    scraper.fetch_listings(
                        location="San Francisco, CA", max_price=1000000
                    )
                    for _ in range(num_requests)
                ]

                responses = await asyncio.gather(*tasks)

            duration = time.time() - start_time
            throughput = num_requests / duration

            results[num_requests] = {
                "duration": duration,
                "throughput": throughput,
                "success_rate": len([r for r in responses if r]) / num_requests,
            }

            performance_metrics["response_times"].append(duration / num_requests)

        assert all(result["success_rate"] > 0.95 for result in results.values())
        assert (
            statistics.mean(performance_metrics["response_times"]) < 0.1
        )  # Max 100ms per request

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_performance(self, large_dataset, performance_metrics):
        """Benchmark complete pipeline performance"""
        scraper = ZillowScraper(api_key=settings.ZILLOW_API_KEY, rate_limit=100)
        parser = ZillowParser()
        batch_sizes = [10, 50, 100]
        results = {}

        for batch_size in batch_sizes:
            start_time = time.time()
            test_data = large_dataset[:batch_size]

            with patch.object(scraper, "fetch_listings") as mock_fetch:
                mock_fetch.return_value = test_data

                # Pipeline execution
                raw_listings = await scraper.fetch_listings(
                    location="San Francisco, CA", max_price=2000000
                )

                with ThreadPoolExecutor(max_workers=4) as executor:
                    leads = list(executor.map(parser.parse, raw_listings))

            duration = time.time() - start_time
            throughput = batch_size / duration

            results[batch_size] = {
                "duration": duration,
                "throughput": throughput,
                "leads_processed": len(leads),
            }

            performance_metrics["throughput"].append(throughput)

        # Performance assertions
        assert all(
            result["leads_processed"] == size for size, result in results.items()
        )
        assert (
            statistics.mean(performance_metrics["throughput"]) > 50
        )  # Min 50 leads/second
        assert (
            max(results.values(), key=lambda x: x["duration"])["duration"] < 30
        )  # Max 30 seconds

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_source_performance(self, performance_metrics):
        """Benchmark performance when fetching from multiple sources concurrently"""
        zillow_scraper = ZillowScraper(api_key=settings.ZILLOW_API_KEY, rate_limit=100)
        facebook_scraper = FacebookScraper(
            api_key=settings.FACEBOOK_API_KEY, rate_limit=100
        )
        zillow_parser = ZillowParser()
        facebook_parser = FacebookParser()

        sources = [(zillow_scraper, zillow_parser), (facebook_scraper, facebook_parser)]

        start_time = time.time()
        results = []

        for scraper, parser in sources:
            with patch.object(scraper, "fetch_listings") as mock_fetch:
                mock_fetch.return_value = [
                    self._generate_mock_listing(i) for i in range(50)
                ]

                raw_listings = await scraper.fetch_listings(
                    location="San Francisco, CA", max_price=2000000
                )

                with ThreadPoolExecutor(max_workers=2) as executor:
                    leads = list(executor.map(parser.parse, raw_listings))
                    results.extend(leads)

        duration = time.time() - start_time
        throughput = len(results) / duration
        performance_metrics["throughput"].append(throughput)

        # Performance assertions
        assert len(results) == 100  # Expected total leads
        assert duration < 10  # Max 10 seconds for multi-source fetching

"""
Aggregation Pipeline for AIQLeads.

This module implements a high-performance pipeline that coordinates 
scrapers and parsers to collect, process, and validate lead data.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

from src.schemas.lead_schema import LeadCreate, LeadValidationError
from src.aggregator.base_scraper import BaseScraper
from src.aggregator.base_parser import BaseParser
from src.aggregator.exceptions import (
    PipelineError, 
    NetworkError, 
    ParseError,
    ValidationError
)
from src.aggregator.components.metrics import PerformanceMetricsAggregator
from src.cache import RedisCache
from src.monitoring import monitor

logger = logging.getLogger(__name__)

class AggregationPipeline:
    """
    Main aggregation pipeline for collecting, processing, and validating lead data.
    
    Implements:
    - Scraper execution with retry and error handling
    - Parser validation with structured exception management
    - Circuit breaker to prevent excessive failures
    - Performance tracking for monitoring pipeline efficiency
    """

    def __init__(
        self,
        scrapers: List[BaseScraper],
        parsers: List[BaseParser],
        cache: RedisCache,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5
    ):
        """
        Initialize the aggregation pipeline.

        Args:
            scrapers (List[BaseScraper]): List of scrapers to fetch lead data.
            parsers (List[BaseParser]): List of parsers to process raw data.
            cache (RedisCache): Caching mechanism for deduplication.
            max_retries (int): Maximum retries for failed scrapers.
            circuit_breaker_threshold (int): Number of consecutive failures before halting retries.
        """
        self.scrapers = scrapers
        self.parsers = parsers
        self.cache = cache
        self.max_retries = max_retries
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.metrics = PerformanceMetricsAggregator()
        self.failure_counts = {scraper.name: 0 for scraper in self.scrapers}

    @monitor.time_execution("pipeline_run_duration")
    async def run_pipeline(self) -> List[LeadCreate]:
        """
        Execute the full aggregation pipeline asynchronously.
        
        - Runs all scrapers in parallel
        - Processes and validates leads
        - Handles errors with retries and monitoring
        
        Returns:
            List[LeadCreate]: List of validated leads
            
        Raises:
            PipelineError: If critical pipeline components fail
        """
        start_time = time.time()
        try:
            tasks = [self._run_scraper(scraper) for scraper in self.scrapers]
            raw_data_batches = await asyncio.gather(*tasks, return_exceptions=True)

            # Track scraper performance
            failures = sum(1 for batch in raw_data_batches if isinstance(batch, Exception))
            self.metrics.record_scraper_completion(
                total=len(self.scrapers),
                successful=len(self.scrapers) - failures,
                duration=time.time() - start_time
            )

            # Flatten results and filter out failures
            raw_data = []
            for batch in raw_data_batches:
                if isinstance(batch, list):
                    raw_data.extend(batch)
                else:
                    logger.error(f"Scraper batch failed: {batch}")
            
            if not raw_data:
                logger.warning("No data collected from scrapers")
                return []

            # Process raw leads through parsers
            processed_leads = await self._process_raw_leads(raw_data)
            
            # Track overall pipeline metrics
            self.metrics.record_pipeline_completion(
                total_leads=len(processed_leads),
                processing_time=time.time() - start_time
            )
            
            return processed_leads

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            self.metrics.record_pipeline_failure(str(e))
            raise PipelineError(f"Pipeline execution failed: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(NetworkError),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying scraper due to network issue: {retry_state.outcome.exception()}"
        )
    )
    @monitor.time_execution("scraper_execution_time")
    async def _run_scraper(self, scraper: BaseScraper) -> List[Dict[str, Any]]:
        """
        Execute a scraper with retry and error handling.

        Args:
            scraper (BaseScraper): The scraper instance.

        Returns:
            List[Dict[str, Any]]: Raw data from the scraper.

        Raises:
            PipelineError: If the scraper repeatedly fails.
        """
        start_time = time.time()
        try:
            logger.info(f"Running scraper: {scraper.name}")
            raw_data = await scraper.scrape()
            
            if not raw_data:
                logger.warning(f"Scraper {scraper.name} returned no data")
                self.metrics.record_scraper_empty_result(scraper.name)
                return []
            
            # Reset failure counter on success
            self.failure_counts[scraper.name] = 0
            
            # Track success metrics
            self.metrics.record_scraper_success(
                scraper=scraper.name,
                leads_found=len(raw_data),
                duration=time.time() - start_time
            )
            return raw_data

        except NetworkError as e:
            self.failure_counts[scraper.name] += 1
            if self.failure_counts[scraper.name] >= self.circuit_breaker_threshold:
                logger.error(f"Circuit breaker activated for {scraper.name}. Skipping further attempts.")
                self.metrics.record_circuit_breaker_trip(scraper.name)
                raise PipelineError(f"Circuit breaker triggered for {scraper.name}")
            
            self.metrics.record_scraper_network_error(scraper.name)
            raise

        except Exception as e:
            logger.error(f"Scraper {scraper.name} failed: {e}", exc_info=True)
            self.metrics.record_scraper_error(scraper.name, str(e))
            raise PipelineError(f"Scraper {scraper.name} encountered an error: {str(e)}")

    @monitor.time_execution("lead_processing_time")
    async def _process_raw_leads(self, raw_leads: List[Dict[str, Any]]) -> List[LeadCreate]:
        """
        Process raw lead data through parsers and validation.

        Args:
            raw_leads (List[Dict[str, Any]]): Raw data collected from scrapers.

        Returns:
            List[LeadCreate]: Validated leads ready for storage.
        """
        processed_leads = []
        tasks = [self._parse_and_validate(lead) for lead in raw_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, LeadCreate):
                processed_leads.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Lead processing failed: {result}")
                self.metrics.record_lead_processing_error(str(result))

        # Track processing metrics
        self.metrics.record_lead_processing_completion(
            total=len(raw_leads),
            successful=len(processed_leads)
        )

        return processed_leads

    async def _parse_and_validate(self, raw_lead: Dict[str, Any]) -> Optional[LeadCreate]:
        """
        Parse and validate a single lead.

        Args:
            raw_lead (Dict[str, Any]): Raw lead data.

        Returns:
            Optional[LeadCreate]: Processed lead if valid, else None.
        """
        for parser in self.parsers:
            try:
                lead = parser.parse(raw_lead)
                
                # Check for duplicates
                if not await self._is_duplicate(lead):
                    self.metrics.track_lead_ingestion()
                    return lead
                else:
                    logger.info(f"Duplicate lead detected: {lead.id}")
                    self.metrics.record_duplicate_lead()
                    return None
                    
            except ParseError as e:
                logger.warning(f"Parsing failed for parser {parser.name}: {e}")
                self.metrics.record_parsing_error(parser.name, str(e))
                continue
            except ValidationError as e:
                logger.warning(f"Validation failed for parser {parser.name}: {e}")
                self.metrics.record_validation_error(parser.name, str(e))
                continue
            except Exception as e:
                logger.error(f"Unexpected error in parser {parser.name}: {e}")
                self.metrics.record_parser_error(parser.name, str(e))
                continue
                
        return None

    async def _is_duplicate(self, lead: LeadCreate) -> bool:
        """
        Check if a lead already exists in the cache.

        Args:
            lead (LeadCreate): The lead to check.

        Returns:
            bool: True if the lead is a duplicate, False otherwise.
        """
        try:
            cache_key = f"lead:{lead.source}:{lead.id}"
            exists = await self.cache.get(cache_key)
            
            if exists:
                return True
                
            await self.cache.set(cache_key, "1", expire=86400)  # Store for 1 day
            return False
            
        except Exception as e:
            logger.error(f"Cache operation failed: {e}")
            self.metrics.record_cache_error(str(e))
            return False  # Fail open on cache errors

    @monitor.time_execution("lead_storage_time")
    async def store_results(self, leads: List[LeadCreate]) -> None:
        """
        Store processed leads in the database.

        Args:
            leads (List[LeadCreate]): Leads ready for storage.
        """
        if not leads:
            logger.info("No leads to store")
            return
            
        try:
            logger.info(f"Storing {len(leads)} leads in the database")
            # Implement database insertion logic here
            
            self.metrics.record_storage_success(len(leads))
            
        except Exception as e:
            logger.error(f"Failed to store leads: {e}", exc_info=True)
            self.metrics.record_storage_error(str(e))
            raise PipelineError(f"Failed to store leads: {str(e)}")

if __name__ == "__main__":
    from src.aggregator.scrapers import craigslist_scraper, zillow_scraper
    from src.aggregator.parsers import craigslist_parser, zillow_parser
    from src.cache import RedisCache

    # Initialize and run pipeline
    pipeline = AggregationPipeline(
        scrapers=[craigslist_scraper, zillow_scraper],
        parsers=[craigslist_parser, zillow_parser],
        cache=RedisCache()
    )

    asyncio.run(pipeline.run_pipeline())
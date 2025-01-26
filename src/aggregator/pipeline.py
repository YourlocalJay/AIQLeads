"""
Aggregation Pipeline for AIQLeads.

This module implements a high-performance pipeline that coordinates 
scrapers and parsers to collect, process, and validate lead data.
"""

import asyncio
from typing import Dict, List, Type, Optional, Any
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from src.schemas.lead_schema import LeadCreate, LeadValidationError
from src.aggregator.base_scraper import BaseScraper
from src.aggregator.base_parser import BaseParser
from src.aggregator.exceptions import PipelineError, NetworkError, ParseError
from src.utils.metrics import MetricsCollector
from src.utils.validators import validate_lead_data
from src.config import Settings

# Import all scrapers
from src.aggregator.scrapers.zillow_scraper import ZillowScraper
from src.aggregator.scrapers.craigslist_scraper import CraigslistScraper
from src.aggregator.scrapers.facebook_scraper import FacebookScraper
from src.aggregator.scrapers.linkedin_scraper import LinkedInScraper
from src.aggregator.scrapers.fsbo_scraper import FSBOScraper

# Import all parsers
from src.aggregator.parsers.zillow_parser import ZillowParser
from src.aggregator.parsers.craigslist_parser import CraigslistParser
from src.aggregator.parsers.facebook_parser import FacebookParser
from src.aggregator.parsers.linkedin_parser import LinkedInParser
from src.aggregator.parsers.fsbo_parser import FSBOParser

logger = logging.getLogger(__name__)

class AggregationPipeline:
    """
    Manages the end-to-end process of lead aggregation, including:
    - Coordinating multiple scrapers
    - Parsing and validating data
    - Error handling and retry logic
    - Metrics collection
    - Rate limiting
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.metrics = MetricsCollector()
        self.scrapers: Dict[str, BaseScraper] = {}
        self.parsers: Dict[str, BaseParser] = {}
        self.initialize_components()
        
    def initialize_components(self) -> None:
        """Initialize and register all scraper and parser components."""
        # Register scrapers with configuration
        self.register_scraper("zillow", ZillowScraper(api_key=self.settings.ZILLOW_API_KEY))
        self.register_scraper("craigslist", CraigslistScraper())
        self.register_scraper("facebook", FacebookScraper(api_key=self.settings.FACEBOOK_API_KEY))
        self.register_scraper("linkedin", LinkedInScraper(api_key=self.settings.LINKEDIN_API_KEY))
        self.register_scraper("fsbo", FSBOScraper())
        
        # Register corresponding parsers
        self.register_parser("zillow", ZillowParser())
        self.register_parser("craigslist", CraigslistParser())
        self.register_parser("facebook", FacebookParser())
        self.register_parser("linkedin", LinkedInParser())
        self.register_parser("fsbo", FSBOParser())
        
    def register_scraper(self, name: str, scraper: BaseScraper) -> None:
        """Register a scraper instance with the pipeline."""
        self.scrapers[name] = scraper
        logger.info(f"Registered scraper: {name}")
        
    def register_parser(self, name: str, parser: BaseParser) -> None:
        """Register a parser instance with the pipeline."""
        self.parsers[name] = parser
        logger.info(f"Registered parser: {name}")

    @asynccontextmanager
    async def managed_session(self):
        """Context manager for handling pipeline session lifecycle."""
        try:
            # Initialize all scrapers
            initialization_tasks = [
                scraper.initialize() for scraper in self.scrapers.values()
            ]
            await asyncio.gather(*initialization_tasks)
            yield
        finally:
            # Cleanup
            cleanup_tasks = [
                scraper.cleanup() for scraper in self.scrapers.values()
                if hasattr(scraper, 'cleanup')
            ]
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks)

    async def aggregate_leads(
        self,
        location: str,
        radius_km: float = 50.0,
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> List[LeadCreate]:
        """
        Aggregate leads from multiple sources with parallel processing.
        
        Args:
            location: Geographic location to search
            radius_km: Search radius in kilometers
            sources: Optional list of specific sources to query
            **kwargs: Additional filtering parameters
            
        Returns:
            List[LeadCreate]: Aggregated and validated leads
        """
        async with self.managed_session():
            try:
                start_time = datetime.utcnow()
                sources = sources or list(self.scrapers.keys())
                
                # Create tasks for each source
                tasks = []
                for source in sources:
                    if source not in self.scrapers:
                        logger.warning(f"Unknown source: {source}")
                        continue
                        
                    task = self._process_source(
                        source=source,
                        location=location,
                        radius_km=radius_km,
                        **kwargs
                    )
                    tasks.append(task)
                
                # Process all sources in parallel
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Aggregate and filter results
                leads = []
                for source_results in results:
                    if isinstance(source_results, Exception):
                        logger.error(f"Source processing failed: {source_results}")
                        continue
                    leads.extend(source_results)
                
                # Update metrics
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self.metrics.record_pipeline_run(
                    total_leads=len(leads),
                    processing_time=processing_time,
                    success_rate=len(leads) / len(tasks) if tasks else 0
                )
                
                return leads
                
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}", exc_info=True)
                raise PipelineError(f"Pipeline execution failed: {str(e)}")

    async def _process_source(
        self,
        source: str,
        location: str,
        radius_km: float,
        **kwargs
    ) -> List[LeadCreate]:
        """Process a single source with error handling and validation."""
        try:
            scraper = self.scrapers[source]
            parser = self.parsers[source]
            
            # Collect raw data
            raw_leads = await scraper.search(
                location=location,
                radius_km=radius_km,
                **kwargs
            )
            
            # Parse and validate leads
            validated_leads = []
            for raw_lead in raw_leads:
                try:
                    # Parse the lead
                    lead = await self._parse_lead(raw_lead, parser)
                    
                    # Validate the lead
                    if validate_lead_data(lead):
                        validated_leads.append(lead)
                    
                except (ParseError, LeadValidationError) as e:
                    logger.warning(f"Lead processing failed: {e}")
                    self.metrics.record_lead_failure(source, str(e))
                    continue
            
            # Update metrics
            self.metrics.record_source_success(
                source=source,
                leads_found=len(raw_leads),
                leads_valid=len(validated_leads)
            )
            
            return validated_leads
            
        except Exception as e:
            logger.error(f"Source {source} processing failed: {e}", exc_info=True)
            self.metrics.record_source_failure(source, str(e))
            raise

    async def _parse_lead(self, raw_lead: Dict[str, Any], parser: BaseParser) -> LeadCreate:
        """Parse and enhance a single lead."""
        try:
            # Parse the lead
            lead = await parser.parse_async(raw_lead)
            
            # Enhance with additional data if available
            if hasattr(parser, 'enhance_lead'):
                lead = await parser.enhance_lead(lead)
            
            return lead
            
        except Exception as e:
            logger.error(f"Lead parsing failed: {e}", exc_info=True)
            raise ParseError(f"Lead parsing failed: {str(e)}")

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get current pipeline statistics and metrics."""
        return {
            "total_leads_processed": self.metrics.total_leads_processed,
            "success_rate": self.metrics.success_rate,
            "average_processing_time": self.metrics.average_processing_time,
            "source_stats": self.metrics.get_source_stats(),
            "error_rates": self.metrics.get_error_rates()
        }
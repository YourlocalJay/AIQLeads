"""
Aggregation Pipeline for AIQLeads.

This module implements a high-performance pipeline that coordinates 
scrapers and parsers to collect, process, and validate lead data.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

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
from src.utils.validators import validate_lead_data
from src.config import Settings

# Import all scrapers
from src.aggregator.scrapers import (
    ZillowScraper,
    CraigslistScraper,
    FacebookScraper,
    LinkedInScraper,
    FSBOScraper
)

# Import all parsers
from src.aggregator.parsers import (
    ZillowParser,
    CraigslistParser,
    FacebookParser,
    LinkedInParser,
    FSBOParser
)

from app.services.logging import logger

class AggregationPipeline:
    """
    Manages the end-to-end process of lead aggregation, including:
    - Coordinating multiple scrapers
    - Parsing and validating data
    - Error handling and retry logic
    - Metrics collection
    - Rate limiting
    
    Attributes:
        settings: Application configuration settings
        metrics: Pipeline metrics collector
        scrapers: Dictionary of registered scrapers
        parsers: Dictionary of registered parsers
        _initialized: Whether pipeline is initialized
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize pipeline
        
        Args:
            settings: Application configuration settings
        """
        self.settings = settings
        self.metrics = PerformanceMetricsAggregator()
        self.scrapers: Dict[str, BaseScraper] = {}
        self.parsers: Dict[str, BaseParser] = {}
        self._initialized = False
        
    async def initialize_components(self) -> None:
        """
        Initialize and register all scraper and parser components
        
        Raises:
            PipelineError: If component initialization fails
        """
        if self._initialized:
            return
            
        try:
            # Register scrapers with configuration
            scraper_configs = {
                "zillow": ZillowScraper(
                    api_key=self.settings.ZILLOW_API_KEY,
                    base_url=self.settings.ZILLOW_BASE_URL
                ),
                "craigslist": CraigslistScraper(
                    base_url=self.settings.CRAIGSLIST_BASE_URL
                ),
                "facebook": FacebookScraper(
                    api_key=self.settings.FACEBOOK_API_KEY,
                    base_url=self.settings.FACEBOOK_BASE_URL
                ),
                "linkedin": LinkedInScraper(
                    api_key=self.settings.LINKEDIN_API_KEY,
                    base_url=self.settings.LINKEDIN_BASE_URL
                ),
                "fsbo": FSBOScraper(
                    base_url=self.settings.FSBO_BASE_URL
                )
            }
            
            for name, scraper in scraper_configs.items():
                await self.register_scraper(name, scraper)
            
            # Register corresponding parsers
            parser_configs = {
                "zillow": ZillowParser(),
                "craigslist": CraigslistParser(),
                "facebook": FacebookParser(),
                "linkedin": LinkedInParser(),
                "fsbo": FSBOParser()
            }
            
            for name, parser in parser_configs.items():
                await self.register_parser(name, parser)
                
            self._initialized = True
            
        except Exception as e:
            error_msg = f"Pipeline initialization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg)
        
    async def register_scraper(self, name: str, scraper: BaseScraper) -> None:
        """
        Register a scraper instance with the pipeline
        
        Args:
            name: Scraper identifier
            scraper: Scraper instance
        """
        try:
            if hasattr(scraper, 'initialize'):
                await scraper.initialize()
            self.scrapers[name] = scraper
            logger.info(f"Registered scraper: {name}")
            
        except Exception as e:
            error_msg = f"Failed to register scraper {name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg)
        
    async def register_parser(self, name: str, parser: BaseParser) -> None:
        """
        Register a parser instance with the pipeline
        
        Args:
            name: Parser identifier
            parser: Parser instance
        """
        try:
            if hasattr(parser, 'initialize'):
                await parser.initialize()
            self.parsers[name] = parser
            logger.info(f"Registered parser: {name}")
            
        except Exception as e:
            error_msg = f"Failed to register parser {name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg)

    @asynccontextmanager
    async def managed_session(self):
        """
        Context manager for handling pipeline session lifecycle
        
        Raises:
            PipelineError: If session management fails
        """
        if not self._initialized:
            await self.initialize_components()
            
        try:
            # Initialize session-specific resources
            session_tasks = [
                scraper.start_session() for scraper in self.scrapers.values()
                if hasattr(scraper, 'start_session')
            ]
            if session_tasks:
                await asyncio.gather(*session_tasks)
                
            yield
            
        except Exception as e:
            error_msg = f"Session management failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg)
            
        finally:
            # Cleanup session resources
            cleanup_tasks = [
                scraper.cleanup() for scraper in self.scrapers.values()
                if hasattr(scraper, 'cleanup')
            ]
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    async def aggregate_leads(
        self,
        location: str,
        radius_km: float = 50.0,
        sources: Optional[List[str]] = None,
        batch_size: int = 100,
        **kwargs
    ) -> List[LeadCreate]:
        """
        Aggregate leads from multiple sources with parallel processing
        
        Args:
            location: Geographic location to search
            radius_km: Search radius in kilometers
            sources: Optional list of specific sources to query
            batch_size: Number of leads to process in parallel
            **kwargs: Additional filtering parameters
            
        Returns:
            List[LeadCreate]: Aggregated and validated leads
            
        Raises:
            PipelineError: If aggregation fails
        """
        async with self.managed_session():
            try:
                start_time = datetime.utcnow()
                sources = sources or list(self.scrapers.keys())
                
                # Process sources in batches
                all_leads = []
                for i in range(0, len(sources), batch_size):
                    batch_sources = sources[i:i + batch_size]
                    
                    # Create tasks for batch
                    tasks = []
                    for source in batch_sources:
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
                    
                    # Process batch in parallel
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Aggregate batch results
                    for source, results in zip(batch_sources, batch_results):
                        if isinstance(results, Exception):
                            logger.error(f"Source {source} failed: {results}")
                            self.metrics.record_source_failure(source, str(results))
                            continue
                        all_leads.extend(results)
                
                # Update metrics
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self.metrics.record_pipeline_run(
                    total_leads=len(all_leads),
                    processing_time=processing_time,
                    sources_total=len(sources),
                    sources_failed=sum(
                        1 for r in batch_results if isinstance(r, Exception)
                    )
                )
                
                return all_leads
                
            except Exception as e:
                error_msg = f"Pipeline execution failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise PipelineError(error_msg)

    async def _process_source(
        self,
        source: str,
        location: str,
        radius_km: float,
        **kwargs
    ) -> List[LeadCreate]:
        """
        Process a single source with error handling and validation
        
        Args:
            source: Source identifier
            location: Geographic location
            radius_km: Search radius
            **kwargs: Additional parameters
            
        Returns:
            List[LeadCreate]: Processed leads
            
        Raises:
            NetworkError: If data collection fails
            ParseError: If data parsing fails
            ValidationError: If data validation fails
        """
        start_time = datetime.utcnow()
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
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_source_success(
                source=source,
                leads_found=len(raw_leads),
                leads_valid=len(validated_leads),
                processing_time=processing_time
            )
            
            return validated_leads
            
        except Exception as e:
            logger.error(f"Source {source} processing failed: {e}", exc_info=True)
            self.metrics.record_source_failure(source, str(e))
            raise

    async def _parse_lead(self, raw_lead: Dict[str, Any], parser: BaseParser) -> LeadCreate:
        """
        Parse and enhance a single lead
        
        Args:
            raw_lead: Raw lead data
            parser: Parser instance
            
        Returns:
            LeadCreate: Parsed lead
            
        Raises:
            ParseError: If parsing fails
            ValidationError: If validation fails
        """
        try:
            # Parse the lead
            lead = await parser.parse_async(raw_lead)
            
            # Enhance with additional data if available
            if hasattr(parser, 'enhance_lead'):
                lead = await parser.enhance_lead(lead)
            
            # Validate the lead
            if not validate_lead_data(lead):
                raise ValidationError("Lead failed validation")
            
            return lead
            
        except Exception as e:
            error_msg = f"Lead parsing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ParseError(error_msg)

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get current pipeline statistics and metrics
        
        Returns:
            Dict[str, Any]: Pipeline statistics
        """
        return await self.metrics.get_stats()
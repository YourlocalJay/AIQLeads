"""
Aggregation Pipeline for AIQLeads.

This module implements a high-performance pipeline that coordinates 
scrapers, parsers, pricing, and recommendations for lead data.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from src.schemas.lead_schema import LeadCreate, LeadValidationError
from src.aggregator.base_scraper import BaseScraper
from src.aggregator.base_parser import BaseParser
from src.aggregator.components.pricing_engine import PricingEngine
from src.aggregator.components.recommendation_engine import RecommendationEngine
from src.aggregator.exceptions import (
    PipelineError, 
    NetworkError, 
    ParseError,
    ValidationError,
    PricingError
)
from src.aggregator.components.metrics import PerformanceMetricsAggregator
from src.utils.validators import validate_lead_data, validate_pricing_data
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
    - Price calculation
    - Lead recommendations
    - Error handling and retry logic
    - Metrics collection
    - Rate limiting
    
    Attributes:
        settings: Application configuration settings
        metrics: Pipeline metrics collector
        scrapers: Dictionary of registered scrapers
        parsers: Dictionary of registered parsers
        pricing_engine: Dynamic pricing engine
        recommendation_engine: AI-powered recommendation engine
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
        self.pricing_engine = PricingEngine(settings)
        self.recommendation_engine = RecommendationEngine(settings)
        self._initialized = False
        
    async def initialize_components(self) -> None:
        """
        Initialize and register all pipeline components
        
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

    async def _process_source(self, source: str, location: str, radius_km: float, **kwargs) -> List[LeadCreate]:
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
            PricingError: If price calculation fails
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
            
            # Process leads
            processed_leads = []
            for raw_lead in raw_leads:
                try:
                    # Parse and validate lead
                    lead = await self._parse_lead(raw_lead, parser)
                    if validate_lead_data(lead):
                        # Calculate price
                        lead['price'] = await self.pricing_engine.calculate_price(lead)
                        processed_leads.append(lead)
                    
                except (ParseError, LeadValidationError, PricingError) as e:
                    logger.warning(f"Lead processing failed: {e}")
                    self.metrics.record_lead_failure(source, str(e))
                    continue
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_source_success(
                source=source,
                leads_found=len(raw_leads),
                leads_valid=len(processed_leads),
                processing_time=processing_time
            )
            
            return processed_leads
            
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

    async def get_recommendations(
        self,
        user_id: str,
        leads: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get personalized lead recommendations
        
        Args:
            user_id: User identifier
            leads: Available leads to recommend from
            limit: Maximum number of recommendations
            
        Returns:
            List[Dict[str, Any]]: Recommended leads
        """
        try:
            return await self.recommendation_engine.get_recommendations(
                user_id=user_id,
                available_leads=leads,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return leads[:limit]  # Return first N leads as fallback

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> None:
        """
        Update user preferences for recommendations
        
        Args:
            user_id: User identifier
            preferences: Updated preferences
        """
        await self.recommendation_engine.update_user_preferences(
            user_id=user_id,
            preferences=preferences
        )

    async def track_user_behavior(
        self,
        user_id: str,
        action: str,
        lead_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track user interaction with leads
        
        Args:
            user_id: User identifier
            action: Type of interaction
            lead_id: Lead identifier
            metadata: Additional interaction data
        """
        await self.recommendation_engine.track_user_behavior(
            user_id=user_id,
            action=action,
            lead_id=lead_id,
            metadata=metadata
        )

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get current pipeline statistics and metrics
        
        Returns:
            Dict[str, Any]: Pipeline statistics
        """
        return await self.metrics.get_stats()
# Add to imports
from src.aggregator.components.pricing_engine import PricingEngine
from src.aggregator.components.recommendation_engine import RecommendationEngine

class AggregationPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.metrics = PerformanceMetricsAggregator()
        self.scrapers: Dict[str, BaseScraper] = {}
        self.parsers: Dict[str, BaseParser] = {}
        self.pricing_engine = PricingEngine(settings)
        self.recommendation_engine = RecommendationEngine(settings)
        self._initialized = False

    async def _process_source(self, source: str, location: str, radius_km: float, **kwargs) -> List[LeadCreate]:
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
                    # Parse and validate
                    lead = await self._parse_lead(raw_lead, parser)
                    if validate_lead_data(lead):
                        # Calculate price
                        lead['price'] = await self.pricing_engine.calculate_price(lead)
                        processed_leads.append(lead)
                    
                except (ParseError, LeadValidationError) as e:
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

    async def get_recommendations(self, user_id: str, leads: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized lead recommendations."""
        return await self.recommendation_engine.get_recommendations(
            user_id=user_id,
            available_leads=leads,
            limit=limit
        )
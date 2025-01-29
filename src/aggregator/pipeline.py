"""
Aggregation Pipeline for AIQLeads.

This module implements a high-performance pipeline that coordinates 
scrapers, parsers, pricing, and recommendations for lead data.
"""

[Previous content remains the same until store_results method...]

    @monitor.time_execution("lead_storage_time")
    async def store_results(self, leads: List[LeadCreate]) -> None:
        """Store processed leads in the database"""
        if not leads:
            logger.info("No leads to store")
            return
            
        try:
            logger.info(f"Storing {len(leads)} leads")
            # Implement storage logic here
            self.metrics.record_storage_success(len(leads))
            
        except Exception as e:
            logger.error(f"Failed to store leads: {e}", exc_info=True)
            self.metrics.record_storage_error(str(e))
            raise PipelineError(f"Storage failed: {str(e)}")

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get current pipeline statistics and metrics"""
        return await self.metrics.get_stats()

if __name__ == "__main__":
    # Example usage
    from src.aggregator.scrapers import craigslist_scraper, zillow_scraper
    from src.aggregator.parsers import craigslist_parser, zillow_parser
    
    settings = Settings()
    pipeline = AggregationPipeline(
        settings=settings,
        scrapers=[craigslist_scraper, zillow_scraper],
        parsers=[craigslist_parser, zillow_parser],
        cache=RedisCache()
    )

    asyncio.run(pipeline.run_pipeline())
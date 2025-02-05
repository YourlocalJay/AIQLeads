from app.services.monitoring import prometheus_metrics

class PerformanceMetricsAggregator:
    """Tracks system performance, scrape success rates, and errors."""

    def __init__(self):
        self.domain_errors = prometheus_metrics.Counter(
            "domain_scrape_errors", "Scraping errors per domain", ["domain", "error_type"]
        )
        self.scrape_success_rate = prometheus_metrics.Histogram(
            "scrape_success_rate", "Success rate of scraping attempts", ["domain"]
        )

    def record_scrape_success(self, domain: str, success: bool):
        """Logs successful or failed scrapes."""
        self.scrape_success_rate.labels(domain=domain).observe(1.0 if success else 0.0)

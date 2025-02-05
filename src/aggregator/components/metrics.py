from typing import Optional
from app.services.logging import logger
from app.services.monitoring import prometheus_metrics


class PerformanceMetricsAggregator:
    """
    Aggregates performance metrics for scraping operations
    """

    def __init__(self):
        """Initialize metrics collectors"""
        # Error tracking
        self.domain_errors = prometheus_metrics.Counter(
            "scraper_domain_errors_total",
            "Total number of scraping errors per domain",
            ["domain", "error_type"],
        )

        # Proxy performance
        self.proxy_performance = prometheus_metrics.Gauge(
            "scraper_proxy_performance_score",
            "Performance score for each proxy per domain",
            ["domain", "proxy"],
        )

        # Success rate tracking
        self.scrape_success_rate = prometheus_metrics.Histogram(
            "scraper_success_rate",
            "Success rate of scraping attempts",
            ["domain"],
            buckets=[0.1, 0.5, 0.9, 0.95, 0.99, 1.0],
        )

        # Response time tracking
        self.response_time = prometheus_metrics.Histogram(
            "scraper_response_time_seconds",
            "Response time for scraping requests",
            ["domain"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
        )

        # Data size tracking
        self.data_size = prometheus_metrics.Histogram(
            "scraper_data_size_bytes",
            "Size of scraped data in bytes",
            ["domain"],
            buckets=[1000, 10000, 100000, 1000000],
        )

        # Rate limit tracking
        self.rate_limit_remaining = prometheus_metrics.Gauge(
            "scraper_rate_limit_remaining",
            "Remaining rate limit per domain",
            ["domain"],
        )

    def record_domain_error(
        self, domain: str, error_type: str, details: Optional[str] = None
    ):
        """
        Record domain-specific error

        Args:
            domain: Target domain
            error_type: Type of error
            details: Optional error details
        """
        self.domain_errors.labels(domain=domain, error_type=error_type).inc()

        if details:
            logger.error(f"Error on {domain}: {error_type} - {details}")

    def update_proxy_performance(self, domain: str, proxy: str, score: float):
        """
        Update proxy performance score

        Args:
            domain: Target domain
            proxy: Proxy URL
            score: Performance score (0.0-1.0)
        """
        self.proxy_performance.labels(domain=domain, proxy=proxy).set(score)

    def record_scrape_attempt(
        self,
        domain: str,
        success: bool,
        response_time: Optional[float] = None,
        data_size: Optional[int] = None,
    ):
        """
        Record scraping attempt results

        Args:
            domain: Target domain
            success: Whether attempt was successful
            response_time: Optional response time in seconds
            data_size: Optional data size in bytes
        """
        # Record success/failure
        self.scrape_success_rate.labels(domain=domain).observe(1.0 if success else 0.0)

        # Record response time if available
        if response_time is not None:
            self.response_time.labels(domain=domain).observe(response_time)

        # Record data size if available
        if data_size is not None:
            self.data_size.labels(domain=domain).observe(data_size)

    def update_rate_limit(self, domain: str, remaining: int):
        """
        Update remaining rate limit

        Args:
            domain: Target domain
            remaining: Remaining requests allowed
        """
        self.rate_limit_remaining.labels(domain=domain).set(remaining)

    def get_domain_stats(self, domain: str) -> dict:
        """
        Get current statistics for domain

        Args:
            domain: Target domain

        Returns:
            dict: Domain statistics
        """
        return {
            "error_count": self.domain_errors.labels(
                domain=domain, error_type="total"
            )._value.get(),
            "success_rate": self.scrape_success_rate.labels(domain=domain)._sum.get()
            / max(1, self.scrape_success_rate.labels(domain=domain)._count.get()),
            "avg_response_time": self.response_time.labels(domain=domain)._sum.get()
            / max(1, self.response_time.labels(domain=domain)._count.get()),
            "rate_limit_remaining": self.rate_limit_remaining.labels(
                domain=domain
            )._value.get(),
        }

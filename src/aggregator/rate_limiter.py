import asyncio
import random
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page

from app.core.config import settings
from app.services.logging import logger
from app.services.monitoring import prometheus_metrics
from app.services.cache.redis_service import AIQRedisCache
from src.aggregator.exceptions import RateLimitExceeded
from src.aggregator.scrapers.rate_limiters.base_limiter import BaseRateLimiter


class ScraperError(Exception):
    """Base exception for scraper-related errors."""

    def __init__(self, message: str, **kwargs):
        """
        Args:
            message (str): Error message describing the exception.
            kwargs: Additional context or details about the error.
        """
        super().__init__(message)
        self.details = kwargs

    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0]} | Details: {self.details}"


class RateLimitExceeded(ScraperError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message="Rate limit exceeded", **kwargs):
        super().__init__(message, **kwargs)


class InvalidCredentials(ScraperError):
    """Raised when API credentials are invalid."""

    def __init__(self, message="Invalid API credentials", **kwargs):
        super().__init__(message, **kwargs)


class ParseError(ScraperError):
    """Raised when data parsing fails."""

    def __init__(self, message="Data parsing failed", **kwargs):
        super().__init__(message, **kwargs)


class LocationError(ScraperError):
    """Raised when location parsing or geocoding fails."""

    def __init__(self, message="Location parsing or geocoding failed", **kwargs):
        super().__init__(message, **kwargs)


class NetworkError(ScraperError):
    """Raised when network requests fail."""

    def __init__(self, message="Network request failed", **kwargs):
        super().__init__(message, **kwargs)


class PersistentBrowserManager:
    """
    Manages persistent browser sessions per domain
    """

    _instance = None
    _browser = None
    _sessions = {}

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            cls._instance = PersistentBrowserManager()
            await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

    async def get_session(self, domain: str) -> Page:
        if len(self._sessions) >= settings.MAX_BROWSER_SESSIONS:
            # Reuse least-recently-used session
            oldest_domain = next(iter(self._sessions))
            await self._sessions[oldest_domain].close()
            del self._sessions[oldest_domain]

        if domain not in self._sessions:
            self._sessions[domain] = await self._browser.new_page()
            await self._sessions[domain].set_extra_http_headers(
                {"User-Agent": random.choice(RequestFingerprinter.USER_AGENTS)}
            )
        return self._sessions[domain]

    async def close_sessions(self):
        for session in self._sessions.values():
            await session.close()

        if self._browser:
            await self._browser.close()

        self._sessions.clear()
        self._browser = None


class CaptchaExtractor:
    @staticmethod
    async def extract_captcha_image(response) -> Optional[str]:
        try:
            if isinstance(response, str):
                html_content = response
            else:
                html_content = (
                    response.text
                    if hasattr(response, "text")
                    else await response.content()
                )

            soup = BeautifulSoup(html_content, "html.parser")
            recaptcha_img = soup.find("img", {"class": "rc-image-tile-wrapper"})
            if recaptcha_img and "src" in recaptcha_img.attrs:
                return recaptcha_img["src"]

            hcaptcha_img = soup.find("img", {"class": "hcaptcha-challenge-image"})
            if hcaptcha_img and "src" in hcaptcha_img.attrs:
                return hcaptcha_img["src"]

            traditional_captchas = ["captcha", "verification-image", "challenge-image"]
            for class_name in traditional_captchas:
                img = soup.find("img", {"class": class_name})
                if img and "src" in img.attrs:
                    return img["src"]
        except Exception as e:
            logger.error(f"CAPTCHA extraction failed: {e}")
        return None


class PerformanceMetricsAggregator:
    def __init__(self):
        self.domain_errors = prometheus_metrics.Counter(
            "domain_scrape_errors",
            "Scraping errors per domain",
            ["domain", "error_type"],
        )
        self.proxy_performance = prometheus_metrics.Gauge(
            "proxy_performance_score",
            "Performance score for each proxy per domain",
            ["domain", "proxy"],
        )
        self.scrape_success_rate = prometheus_metrics.Histogram(
            "scrape_success_rate", "Success rate of scraping attempts", ["domain"]
        )

    def record_domain_error(
        self, domain: str, error_type: str, details: Optional[str] = None
    ):
        self.domain_errors.labels(domain=domain, error_type=error_type).inc()
        if details:
            logger.error(f"Error on {domain}: {error_type} - {details}")

    def update_proxy_performance(self, domain: str, proxy: str, score: float):
        self.proxy_performance.labels(domain=domain, proxy=proxy).set(score)

    def record_scrape_success(self, domain: str, success: bool):
        self.scrape_success_rate.labels(domain=domain).observe(1.0 if success else 0.0)


class PaginationHandler:
    @staticmethod
    async def handle_pagination(
        scraper,
        base_url: str,
        max_pages: int = 10,
        pagination_selector: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        current_url = base_url
        current_page = 1

        while current_page <= max_pages:
            try:
                page_data = await scraper._safe_fetch(current_url)
                if not page_data:
                    break
                yield page_data
                next_url = await scraper._find_next_page_url(
                    current_url, page_data, pagination_selector
                )
                if not next_url:
                    break
                current_url = next_url
                current_page += 1
            except Exception as e:
                logger.error(f"Pagination error: {e}")
                current_page += 1


class RateLimiter(BaseRateLimiter):
    """Token bucket rate limiter for API request management.

    Extends BaseRateLimiter with:
    - Token bucket algorithm
    - Request queueing
    - Enhanced metrics
    """

    def __init__(
        self,
        rate_limit: int,
        window_size: int,
        redis_url: Optional[str] = None,
        max_queue_size: int = 1000,
    ):
        super().__init__(
            requests_per_minute=rate_limit, burst_limit=rate_limit, redis_url=redis_url
        )
        self.window_size = window_size
        self._request_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._consumer_task: Optional[asyncio.Task] = None

    async def initialize(self):
        await super().initialize()
        self._consumer_task = asyncio.create_task(self._request_consumer())

    async def shutdown(self):
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        await super().shutdown()

    async def acquire(self, endpoint: str, tokens: int = 1) -> bool:
        """Try to acquire tokens, optionally queueing request."""
        if await super().acquire(endpoint, tokens):
            return True

        try:
            await self._request_queue.put((endpoint, tokens))
            return True
        except asyncio.QueueFull:
            return False

    async def _request_consumer(self):
        """Process queued requests."""
        while True:
            try:
                endpoint, tokens = await self._request_queue.get()
                if await super().acquire(endpoint, tokens):
                    self._request_queue.task_done()
                else:
                    # Re-queue if still can't acquire
                    await asyncio.sleep(1)
                    await self._request_queue.put((endpoint, tokens))
            except Exception:
                self._record_error()

    async def get_enhanced_metrics(self, endpoint: str) -> dict:
        """Get detailed metrics including queue stats."""
        base_metrics = await self.get_metrics(endpoint)
        return {
            **base_metrics,
            "window_size": self.window_size,
            "queue_size": self._request_queue.qsize(),
            "queue_remaining": self._request_queue.maxsize
            - self._request_queue.qsize(),
        }


class BaseScraper(ABC):
    def __init__(
        self,
        base_url: str,
        default_rate_limit: int = 10,
        timeout: float = 30.0,
        proxies: Optional[List[str]] = None,
        cache: Optional[AIQRedisCache] = None,
    ):
        self.base_url = base_url
        self.timeout = timeout

        self.browser_manager = None
        self.metrics_aggregator = PerformanceMetricsAggregator()

    async def _find_next_page_url(
        self,
        current_url: str,
        page_data: Dict[str, Any],
        pagination_selector: Optional[str] = None,
    ) -> Optional[str]:
        if "next_page_token" in page_data:
            return f"{current_url}?page_token={page_data['next_page_token']}"

        if pagination_selector:
            try:
                soup = BeautifulSoup(page_data.get("html_content", ""), "html.parser")
                next_link = soup.select_one(pagination_selector)
                if next_link and "href" in next_link.attrs:
                    return urljoin(current_url, next_link["href"])
            except Exception as e:
                logger.error(f"Pagination link extraction failed: {e}")

        link_texts = ["next", "next page", "следующая", "下一页"]
        try:
            soup = BeautifulSoup(page_data.get("html_content", ""), "html.parser")
            for text in link_texts:
                next_link = soup.find("a", string=lambda s: s and text in s.lower())
                if next_link and "href" in next_link.attrs:
                    return urljoin(current_url, next_link["href"])
        except Exception as e:
            logger.error(f"Next page link detection failed: {e}")

        return None

    async def scrape_paginated(
        self,
        base_url: str,
        max_pages: int = 10,
        pagination_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        all_data = []
        async for page_data in PaginationHandler.handle_pagination(
            self, base_url, max_pages, pagination_selector
        ):
            all_data.append(page_data)

        return all_data

    async def close(self):
        if self.browser_manager:
            await self.browser_manager.close_sessions()

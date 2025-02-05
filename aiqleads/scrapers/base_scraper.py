from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urljoin
import asyncio
import httpx
from bs4 import BeautifulSoup

from app.services.logging import logger
from app.services.cache.redis_service import AIQRedisCache
from aiqleads.utils.request_fingerprint import RequestFingerprinter
from aiqleads.utils.rate_limiter import RateLimiter
from aiqleads.utils.proxy_manager import ProxyManager
from aiqleads.utils.browser_manager import PersistentBrowserManager
from aiqleads.monitoring.metrics_aggregator import PerformanceMetricsAggregator
from aiqleads.utils.errors import NetworkError, ScraperError


class BaseScraper(ABC):
    """Base Scraper with AI-enhanced dynamic fingerprinting, rate limiting, and proxy management."""

    def __init__(
        self,
        base_url: str,
        rate_limit: int = 10,
        timeout: float = 30.0,
        proxies: Optional[List[str]] = None,
        cache: Optional[AIQRedisCache] = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limiter = RateLimiter(rate_limit)
        self.proxy_manager = ProxyManager(proxies)
        self.cache = cache or AIQRedisCache()
        self.metrics = PerformanceMetricsAggregator()
        self._browser_manager: Optional[PersistentBrowserManager] = None

    async def _get_browser_manager(self) -> PersistentBrowserManager:
        """Lazy initializes the browser manager for Playwright scraping."""
        if not self._browser_manager:
            self._browser_manager = await PersistentBrowserManager.get_instance()
        return self._browser_manager

    async def _safe_fetch(self, url: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """Fetches data from a URL with intelligent request handling and failovers."""
        domain = urlparse(url).netloc
        if not self.rate_limiter.can_make_request(domain):
            return None

        proxy = self.proxy_manager.get_best_proxy(domain)
        headers = RequestFingerprinter.generate_headers(self.base_url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout, proxy=proxy, headers=headers) as client:
                response = await client.request(method, url, **kwargs)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    self.rate_limiter.record_error(domain, 429)
                    return None

        except Exception:
            browser_manager = await self._get_browser_manager()
            page = await browser_manager.get_session(domain)
            await page.goto(url)
            content = await page.content()
            return {"html_content": content}

    @abstractmethod
    async def scrape(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Abstract method for defining the core scraping logic."""
        pass

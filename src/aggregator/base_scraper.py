# src/aggregator/core/base_scraper.py
import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
from collections import defaultdict

import httpx
import orjson
import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright, Browser, Page

from app.core.config import settings
from app.services.logging import logger
from app.services.monitoring import prometheus_metrics
from app.services.cache.redis_service import AIQRedisCache

class RequestFingerprinter:
    """
    Generates randomized request headers to avoid detection
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8",
        "fr-FR,fr;q=0.7",
    ]

    @classmethod
    def generate_headers(cls, base_url: str) -> Dict[str, str]:
        """
        Generate randomized request headers
        
        Args:
            base_url (str): Base URL for referer
        
        Returns:
            Dict[str, str]: Randomized headers
        """
        return {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept-Language": random.choice(cls.ACCEPT_LANGUAGES),
            "Referer": f"https://{urlparse(base_url).netloc}",
            "Accept": "application/json, text/plain, */*",
            "DNT": "1"
        }

class RateLimiter:
    """
    Dynamic rate limiting with adaptive adjustment
    """
    def __init__(self, default_rate_limit: int = 10):
        self._rate_limits = defaultdict(lambda: default_rate_limit)
        self._request_timestamps = defaultdict(list)
        self._error_counters = defaultdict(int)

    def can_make_request(self, domain: str) -> bool:
        """
        Check if a request can be made for a specific domain
        
        Args:
            domain (str): Target domain
        
        Returns:
            bool: Whether request is allowed
        """
        current_time = datetime.now()
        rate_limit = self._rate_limits[domain]
        timestamps = self._request_timestamps[domain]
        
        # Remove old timestamps
        timestamps[:] = [
            ts for ts in timestamps 
            if (current_time - ts).total_seconds() <= 60
        ]
        
        if len(timestamps) < rate_limit:
            timestamps.append(current_time)
            return True
        return False

    def record_error(self, domain: str, status_code: Optional[int] = None):
        """
        Adjust rate limit based on errors
        
        Args:
            domain (str): Target domain
            status_code (Optional[int]): HTTP status code
        """
        self._error_counters[domain] += 1
        
        # Reduce rate limit on repeated errors or 429 status
        if status_code == 429 or self._error_counters[domain] > 5:
            current_limit = self._rate_limits[domain]
            new_limit = max(1, current_limit // 2)
            self._rate_limits[domain] = new_limit
            
            logger.warning(
                f"Rate limit adjusted for {domain}: {current_limit} -> {new_limit}"
            )
            
            # Reset error counter
            self._error_counters[domain] = 0

    def record_success(self, domain: str):
        """
        Gradually increase rate limit after successful requests
        
        Args:
            domain (str): Target domain
        """
        current_limit = self._rate_limits[domain]
        new_limit = min(20, int(current_limit * 1.2))  # 20% increase, max 20
        
        self._rate_limits[domain] = new_limit
        self._error_counters[domain] = 0
        
        logger.info(
            f"Rate limit increased for {domain}: {current_limit} -> {new_limit}"
        )

class ProxyManager:
    """
    Advanced proxy management with performance tracking
    """
    def __init__(self, proxies: Optional[List[str]] = None):
        self._proxies = proxies or []
        self._proxy_performance = defaultdict(lambda: defaultdict(float))
        self._last_used_proxy = {}

    def get_best_proxy(self, domain: str) -> Optional[str]:
        """
        Select best proxy for a specific domain
        
        Args:
            domain (str): Target domain
        
        Returns:
            Optional[str]: Best performing proxy
        """
        if not self._proxies:
            return None
        
        # Prioritize proxies with highest domain-specific performance
        domain_proxy_scores = {
            proxy: self._proxy_performance[domain][proxy] 
            for proxy in self._proxies
        }
        
        # Fallback to round-robin if no performance data
        if not domain_proxy_scores:
            proxy = self._proxies[
                (self._last_used_proxy.get(domain, -1) + 1) % len(self._proxies)
            ]
        else:
            proxy = max(domain_proxy_scores, key=domain_proxy_scores.get)
        
        self._last_used_proxy[domain] = self._proxies.index(proxy)
        return proxy

    def report_proxy_success(self, domain: str, proxy: str):
        """
        Record successful proxy usage
        
        Args:
            domain (str): Target domain
            proxy (str): Proxy URL
        """
        current_score = self._proxy_performance[domain][proxy]
        self._proxy_performance[domain][proxy] = min(1.0, current_score + 0.1)

    def report_proxy_failure(self, domain: str, proxy: str):
        """
        Reduce proxy performance score on failure
        
        Args:
            domain (str): Target domain
            proxy (str): Proxy URL
        """
        current_score = self._proxy_performance[domain][proxy]
        self._proxy_performance[domain][proxy] = max(0.0, current_score * 0.8)

class BaseScraper(ABC):
    """
    Comprehensive base scraper with advanced scraping capabilities
    """
    
    def __init__(
        self, 
        base_url: str,
        default_rate_limit: int = 10,
        timeout: float = 30.0,
        proxies: Optional[List[str]] = None,
        cache: Optional[AIQRedisCache] = None
    ):
        self.base_url = base_url
        self.timeout = timeout
        
        # Core components
        self.rate_limiter = RateLimiter(default_rate_limit)
        self.proxy_manager = ProxyManager(proxies)
        self.cache = cache or AIQRedisCache()
        
        # Monitoring
        self.metrics = PerformanceMetricsAggregator()
        
        # Browser management
        self._browser_manager = None

    async def _get_browser_manager(self) -> PersistentBrowserManager:
        """
        Lazy initialize browser manager
        
        Returns:
            PersistentBrowserManager: Browser management instance
        """
        if not self._browser_manager:
            self._browser_manager = await PersistentBrowserManager.get_instance()
        return self._browser_manager

    async def _safe_fetch(
        self, 
        url: str, 
        method: str = 'GET', 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Comprehensive fetch method with multiple fallback mechanisms
        
        Args:
            url (str): Target URL
            method (str): HTTP method
            **kwargs: Additional request parameters
        
        Returns:
            Optional[Dict[str, Any]]: Fetched data
        """
        domain = urlparse(url).netloc
        
        # Check rate limiting
        if not self.rate_limiter.can_make_request(domain):
            logger.warning(f"Rate limit exceeded for {domain}")
            return None
        
        # Select proxy
        proxy = self.proxy_manager.get_best_proxy(domain)
        
        # Generate dynamic headers
        headers = RequestFingerprinter.generate_headers(self.base_url)
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                follow_redirects=True,
                proxy=proxy,
                headers=headers
            ) as client:
                response = await client.request(method, url, **kwargs)
                
                # Successful response
                if response.status_code == 200:
                    self.rate_limiter.record_success(domain)
                    self.proxy_manager.report_proxy_success(domain, proxy)
                    return response.json()
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.rate_limiter.record_error(domain, 429)
                    self.proxy_manager.report_proxy_failure(domain, proxy)
                    return None
                
                # Log other status codes
                logger.warning(f"Unusual status code {response.status_code} for {url}")
                return None
        
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            self.rate_limiter.record_error(domain)
            
            # Optional: Fallback to browser-based scraping
            try:
                browser_manager = await self._get_browser_manager()
                page = await browser_manager.get_session(domain)
                await page.goto(url)
                content = await page.content()
                return {"html_content": content}
            except Exception as browser_err:
                logger.error(f"Browser scraping failed for {url}: {browser_err}")
                return None

    @abstractmethod
    async def scrape(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Abstract method for core scraping logic
        
        Args:
            query (Optional[str]): Optional search query
        
        Returns:
            List[Dict[str, Any]]: Scraped data
        """
        pass

    async def scrape_paginated(
        self, 
        base_url: str, 
        max_pages: int = 10, 
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Comprehensive paginated scraping method
        
        Args:
            base_url (str): Initial URL to start scraping
            max_pages (int): Maximum number of pages to scrape
            pagination_selector (Optional[str]): CSS selector for next page link
        
        Returns:
            List[Dict[str, Any]]: Combined scraped data from all pages
        """
        all_data = []
        async for page_data in PaginationHandler.handle_pagination(
            self, base_url, max_pages, pagination_selector
        ):
            all_data.append(page_data)
        
        return all_data

    async def close(self):
        """
        Cleanup method to release all resources
        """
        if self._browser_manager:
            await self._browser_manager.close_sessions()

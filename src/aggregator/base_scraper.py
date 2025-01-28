import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlparse, urljoin
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import Page

from app.core.config import settings
from app.services.logging import logger
from app.services.cache.redis_service import AIQRedisCache
from .components.request_fingerprint import RequestFingerprinter
from .components.rate_limiter import RateLimiter
from .components.proxy_manager import ProxyManager
from .components.browser_manager import PersistentBrowserManager
from .components.metrics import PerformanceMetricsAggregator
from .exceptions import NetworkError, ScraperError

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
        """
        Initialize scraper with configuration
        
        Args:
            base_url: Base URL for scraping
            default_rate_limit: Default requests per minute
            timeout: Request timeout in seconds
            proxies: List of proxy URLs
            cache: Redis cache instance
        """
        self.base_url = base_url
        self.timeout = timeout
        
        # Core components
        self.rate_limiter = RateLimiter(default_rate_limit)
        self.proxy_manager = ProxyManager(proxies)
        self.cache = cache or AIQRedisCache()
        
        # Monitoring
        self.metrics = PerformanceMetricsAggregator()
        
        # Browser management
        self._browser_manager: Optional[PersistentBrowserManager] = None

    async def _get_browser_manager(self) -> PersistentBrowserManager:
        """
        Lazy initialize browser manager
        
        Returns:
            PersistentBrowserManager: Browser management instance
            
        Raises:
            ScraperError: If browser initialization fails
        """
        if not self._browser_manager:
            try:
                self._browser_manager = await PersistentBrowserManager.get_instance()
            except Exception as e:
                raise ScraperError(f"Failed to initialize browser manager: {e}")
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
            url: Target URL
            method: HTTP method
            **kwargs: Additional request parameters
        
        Returns:
            Optional[Dict[str, Any]]: Fetched data
            
        Raises:
            NetworkError: If all fetch attempts fail
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
                    if proxy:
                        self.proxy_manager.report_proxy_success(domain, proxy)
                    return response.json()
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.rate_limiter.record_error(domain, 429)
                    if proxy:
                        self.proxy_manager.report_proxy_failure(domain, proxy)
                    return None
                
                # Log other status codes
                logger.warning(f"Unusual status code {response.status_code} for {url}")
                return None
        
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            self.rate_limiter.record_error(domain)
            
            # Fallback to browser-based scraping
            try:
                browser_manager = await self._get_browser_manager()
                page = await browser_manager.get_session(domain)
                await page.goto(url)
                content = await page.content()
                return {"html_content": content}
            except Exception as browser_err:
                error_msg = f"All fetch attempts failed for {url}. HTTP error: {e}, Browser error: {browser_err}"
                logger.error(error_msg)
                raise NetworkError(error_msg)

    @abstractmethod
    async def scrape(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Abstract method for core scraping logic
        
        Args:
            query: Optional search query
        
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
            base_url: Initial URL to start scraping
            max_pages: Maximum number of pages to scrape
            pagination_selector: CSS selector for next page link
        
        Returns:
            List[Dict[str, Any]]: Combined scraped data from all pages
        """
        all_data = []
        current_url = base_url
        current_page = 1

        while current_page <= max_pages:
            try:
                page_data = await self._safe_fetch(current_url)
                if not page_data:
                    break
                    
                all_data.append(page_data)
                
                # Find next page URL
                if 'next_page_token' in page_data:
                    current_url = f"{current_url}?page_token={page_data['next_page_token']}"
                elif pagination_selector:
                    soup = BeautifulSoup(page_data.get('html_content', ''), 'html.parser')
                    next_link = soup.select_one(pagination_selector)
                    if next_link and 'href' in next_link.attrs:
                        current_url = urljoin(current_url, next_link['href'])
                    else:
                        break
                else:
                    break
                    
                current_page += 1
            except Exception as e:
                logger.error(f"Pagination error on page {current_page}: {e}")
                break
        
        return all_data

    async def close(self):
        """Cleanup method to release all resources"""
        if self._browser_manager:
            await self._browser_manager.close_sessions()

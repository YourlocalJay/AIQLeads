import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlparse, urljoin
from datetime import datetime
import time
from functools import wraps

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
from .components.circuit_breaker import CircuitBreaker
from .exceptions import NetworkError, ScraperError

def with_retry(max_retries=3, base_delay=1, max_delay=30):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay")
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

class BaseScraper(ABC):
    """
    Comprehensive base scraper with advanced scraping capabilities
    and reliability features
    """
    
    def __init__(
        self, 
        base_url: str,
        default_rate_limit: int = 10,
        timeout: float = 30.0,
        proxies: Optional[List[str]] = None,
        cache: Optional[AIQRedisCache] = None,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60
    ):
        """
        Initialize scraper with configuration
        
        Args:
            base_url: Base URL for scraping
            default_rate_limit: Default requests per minute
            timeout: Request timeout in seconds
            proxies: List of proxy URLs
            cache: Redis cache instance
            circuit_breaker_threshold: Number of failures before circuit opens
            circuit_breaker_timeout: Seconds before circuit half-opens
        """
        self.base_url = base_url
        self.timeout = timeout
        
        # Core components
        self.rate_limiter = RateLimiter(default_rate_limit)
        self.proxy_manager = ProxyManager(proxies)
        self.cache = cache or AIQRedisCache()
        
        # Reliability components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_timeout
        )
        
        # Monitoring
        self.metrics = PerformanceMetricsAggregator()
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0
        
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

    async def _health_check(self) -> bool:
        """
        Perform health check of scraper components
        
        Returns:
            bool: True if all components are healthy
        """
        current_time = time.time()
        if current_time - self._last_health_check < self._health_check_interval:
            return True
            
        try:
            # Check core components
            if not self.rate_limiter.is_healthy():
                logger.error("Rate limiter health check failed")
                return False
                
            if not self.proxy_manager.is_healthy():
                logger.error("Proxy manager health check failed")
                return False
                
            if not await self.cache.ping():
                logger.error("Cache health check failed")
                return False
                
            # Check browser manager if initialized
            if self._browser_manager:
                if not await self._browser_manager.is_healthy():
                    logger.error("Browser manager health check failed")
                    return False
                    
            self._last_health_check = current_time
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    @with_retry(max_retries=3)
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
        # Check component health
        if not await self._health_check():
            raise ScraperError("Component health check failed")
            
        domain = urlparse(url).netloc
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker is open for {domain}")
            return None
        
        # Check rate limiting
        if not self.rate_limiter.can_make_request(domain):
            logger.warning(f"Rate limit exceeded for {domain}")
            return None
        
        # Select proxy
        proxy = self.proxy_manager.get_best_proxy(domain)
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                follow_redirects=True,
                proxy=proxy,
                headers=RequestFingerprinter.generate_headers(self.base_url)
            ) as client:
                response = await client.request(method, url, **kwargs)
                
                # Successful response
                if response.status_code == 200:
                    self.circuit_breaker.record_success()
                    self.rate_limiter.record_success(domain)
                    if proxy:
                        self.proxy_manager.report_proxy_success(domain, proxy)
                    return response.json()
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.circuit_breaker.record_failure()
                    self.rate_limiter.record_error(domain, 429)
                    if proxy:
                        self.proxy_manager.report_proxy_failure(domain, proxy)
                    return None
                
                # Log other status codes
                logger.warning(f"Unusual status code {response.status_code} for {url}")
                return None
        
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            self.circuit_breaker.record_failure()
            self.rate_limiter.record_error(domain)
            
            # Fallback to browser-based scraping with circuit breaker
            if self.circuit_breaker.can_execute():
                try:
                    browser_manager = await self._get_browser_manager()
                    page = await browser_manager.get_session(domain)
                    await page.goto(url)
                    content = await page.content()
                    self.circuit_breaker.record_success()
                    return {"html_content": content}
                except Exception as browser_err:
                    self.circuit_breaker.record_failure()
                    error_msg = f"All fetch attempts failed for {url}. HTTP error: {e}, Browser error: {browser_err}"
                    logger.error(error_msg)
                    raise NetworkError(error_msg)
            else:
                raise NetworkError(f"Circuit breaker prevented browser fallback for {url}")

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
        last_success_time = time.time()

        while current_page <= max_pages:
            try:
                # Circuit breaker check
                if not self.circuit_breaker.can_execute():
                    logger.warning("Circuit breaker prevented pagination")
                    break
                    
                page_data = await self._safe_fetch(current_url)
                if not page_data:
                    break
                    
                all_data.append(page_data)
                last_success_time = time.time()
                
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
                
                # Check time between successful requests
                if time.time() - last_success_time > self.timeout:
                    logger.warning("Pagination timeout exceeded")
                    break
                    
            except Exception as e:
                logger.error(f"Pagination error on page {current_page}: {e}")
                self.circuit_breaker.record_failure()
                break
        
        return all_data

    async def close(self):
        """Cleanup method to release all resources"""
        if self._browser_manager:
            await self._browser_manager.close_sessions()

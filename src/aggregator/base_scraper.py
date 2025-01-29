import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator, Type, Tuple, Set
from urllib.parse import urlparse, urljoin
from datetime import datetime
import time
from collections import defaultdict
from functools import wraps

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

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

def with_retry(
    max_retries: int = 3, 
    base_delay: float = 1, 
    max_delay: float = 30,
    retriable_errors: Tuple[Type[Exception], ...] = (NetworkError, httpx.TransportError)
):
    """
    Enhanced retry decorator with exponential backoff and jitter
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retriable_errors: Tuple of exception types that should trigger retry
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(self, *args, **kwargs)
                    # Record successful retry if not first attempt
                    if attempt > 0:
                        self.metrics.record_retry_success(attempt)
                    return result
                    
                except retriable_errors as e:
                    last_exception = e
                    if attempt == max_retries:
                        self.metrics.record_retry_failure(max_retries)
                        raise
                    
                    # Calculate exponential backoff with jitter
                    delay = min(
                        base_delay * (2 ** attempt) + random.uniform(0, 1), 
                        max_delay
                    )
                    
                    self.metrics.record_retry_attempt(attempt, str(e))
                    logger.warning(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay")
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    # Non-retriable error
                    raise
            
            raise last_exception
        return wrapper
    return decorator

class BaseScraper(ABC):
    """
    Enhanced base scraper with comprehensive reliability features
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
        """
        self.base_url = base_url
        self.timeout = timeout
        
        # Core components
        self.rate_limiter = RateLimiter(default_rate_limit)
        self.proxy_manager = ProxyManager(proxies)
        self.cache = cache or AIQRedisCache()
        
        # Domain-specific circuit breakers
        self.circuit_breakers = defaultdict(
            lambda: CircuitBreaker(
                failure_threshold=circuit_breaker_threshold,
                recovery_timeout=circuit_breaker_timeout
            )
        )
        
        # Monitoring
        self.metrics = PerformanceMetricsAggregator()
        self._health_check_interval = 60
        self._last_health_check = 0
        
        # Browser management
        self._browser_manager: Optional[PersistentBrowserManager] = None

    def get_circuit_breaker(self, domain: str) -> CircuitBreaker:
        """Get domain-specific circuit breaker"""
        return self.circuit_breakers[domain]

    async def _health_check(self) -> bool:
        """Enhanced health check implementation"""
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
            
            # Check circuit breakers
            open_breakers = [
                domain for domain, cb in self.circuit_breakers.items() 
                if cb.is_open()
            ]
            if open_breakers:
                logger.warning(f"Circuit breakers open for domains: {open_breakers}")
                self.metrics.record_open_circuit_breakers(open_breakers)
                return False
                    
            # Check browser manager if initialized
            if self._browser_manager:
                if not await self._browser_manager.is_healthy():
                    logger.error("Browser manager health check failed")
                    return False
                    
            self._last_health_check = current_time
            self.metrics.record_health_check(True)
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.metrics.record_health_check(False, str(e))
            return False

    @with_retry(max_retries=3, retriable_errors=(NetworkError, httpx.TransportError))
    async def _safe_fetch(
        self, 
        url: str, 
        method: str = 'GET', 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Enhanced fetch method with comprehensive reliability features
        """
        # Check component health
        if not await self._health_check():
            raise ScraperError("Component health check failed")
            
        domain = urlparse(url).netloc
        circuit_breaker = self.get_circuit_breaker(domain)
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker is open for {domain}")
            self.metrics.record_circuit_breaker_rejection(domain)
            return None
        
        # Check rate limiting
        if not self.rate_limiter.can_make_request(domain):
            logger.warning(f"Rate limit exceeded for {domain}")
            self.metrics.record_rate_limit_rejection(domain)
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
                
                # Update rate limits from headers
                if 'X-RateLimit-Limit' in response.headers:
                    new_limit = int(response.headers['X-RateLimit-Limit'])
                    self.rate_limiter.update_limit(domain, new_limit)
                
                # Successful response
                if response.status_code == 200:
                    circuit_breaker.record_success()
                    self.rate_limiter.record_success(domain)
                    if proxy:
                        self.proxy_manager.report_proxy_success(domain, proxy)
                    self.metrics.record_successful_request(domain)
                    return response.json()
                
                # Handle rate limiting
                if response.status_code == 429:
                    circuit_breaker.record_failure()
                    self.rate_limiter.record_error(domain, 429)
                    if proxy:
                        self.proxy_manager.report_proxy_failure(domain, proxy)
                    self.metrics.record_rate_limit_hit(domain)
                    return None
                
                # Log other status codes
                logger.warning(f"Unusual status code {response.status_code} for {url}")
                self.metrics.record_unusual_status_code(domain, response.status_code)
                return None
        
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            circuit_breaker.record_failure()
            self.rate_limiter.record_error(domain)
            self.metrics.record_request_failure(domain, str(e))
            
            # Fallback to browser-based scraping
            try:
                browser_manager = await self._get_browser_manager()
                page = await browser_manager.get_session(domain)
                
                try:
                    await page.goto(url, timeout=15000)  # 15s timeout
                    content = await page.content()
                    circuit_breaker.record_success()
                    self.metrics.record_browser_fallback(domain, success=True)
                    return {"html_content": content}
                    
                except PlaywrightTimeoutError:
                    circuit_breaker.record_failure()
                    self.metrics.record_browser_fallback(domain, success=False)
                    error_msg = f"Browser fallback timeout for {url}"
                    logger.error(error_msg)
                    raise NetworkError(error_msg)
                    
            except Exception as browser_err:
                circuit_breaker.record_failure()
                self.metrics.record_browser_fallback(domain, success=False)
                error_msg = f"All fetch attempts failed for {url}. HTTP error: {e}, Browser error: {browser_err}"
                logger.error(error_msg)
                raise NetworkError(error_msg)

    @abstractmethod
    async def scrape(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Abstract method for core scraping logic"""
        pass

    async def scrape_paginated(
        self, 
        base_url: str, 
        max_pages: int = 10, 
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Enhanced paginated scraping method"""
        all_data = []
        current_url = base_url
        current_page = 1
        last_success_time = time.time()
        domain = urlparse(base_url).netloc
        circuit_breaker = self.get_circuit_breaker(domain)

        while current_page <= max_pages:
            try:
                # Circuit breaker check
                if not circuit_breaker.can_execute():
                    logger.warning(f"Circuit breaker prevented pagination for {domain}")
                    self.metrics.record_pagination_circuit_break(domain)
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
                self.metrics.record_successful_pagination(domain)
                
                # Check time between successful requests
                if time.time() - last_success_time > self.timeout:
                    logger.warning("Pagination timeout exceeded")
                    self.metrics.record_pagination_timeout(domain)
                    break
                    
            except Exception as e:
                logger.error(f"Pagination error on page {current_page}: {e}")
                circuit_breaker.record_failure()
                self.metrics.record_pagination_error(domain, str(e))
                break
        
        return all_data

    async def close(self):
        """Enhanced cleanup method"""
        try:
            if self._browser_manager:
                await self._browser_manager.close_sessions()
            self.metrics.record_cleanup(success=True)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            self.metrics.record_cleanup(success=False, error=str(e))
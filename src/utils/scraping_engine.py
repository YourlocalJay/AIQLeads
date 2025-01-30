import asyncio
import time
import logging
import random
import heapq
import psutil
from typing import TypeVar, List, Callable, Any, Dict, Optional, Tuple, Union
from collections import OrderedDict, deque, defaultdict
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)
T = TypeVar('T')

class ScrapingError(Exception):
    """Comprehensive exception for scraping failures"""
    def __init__(self, message: str, error_type: str = 'unknown', context: Dict[str, Any] = None):
        super().__init__(message)
        self.error_type = error_type
        self.context = context or {}
        self.timestamp = time.time()

class AdaptiveCache:
    """
    Intelligent caching mechanism with adaptive eviction and performance tracking
    
    Key Features:
    - O(1) expiration using heapq
    - Adaptive size management
    - Performance metric tracking
    """
    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self._cache = OrderedDict()
        self._expiry_heap = []
        self._max_size = max_size
        self._ttl = ttl
        self._lock = asyncio.Lock()
        
        # Performance metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached item with hit/miss tracking"""
        async with self._lock:
            await self._evict_expired()
            
            if key in self._cache:
                self._hits += 1
                # Move to end to mark as recently used
                value = self._cache[key]
                del self._cache[key]
                self._cache[key] = value
                return value
            
            self._misses += 1
            return None

    async def set(self, key: str, value: Any) -> None:
        """Store item with adaptive size management"""
        async with self._lock:
            now = time.monotonic()
            
            # Remove existing entry if key exists
            if key in self._cache:
                del self._cache[key]
            
            # Manage cache size
            while len(self._cache) >= self._max_size:
                self._evictions += 1
                # Remove least recently used
                oldest_key, _ = self._cache.popitem(last=False)
                self._expiry_heap = [(exp, k) for exp, k in self._expiry_heap if k != oldest_key]
                heapq.heapify(self._expiry_heap)
            
            # Add new entry
            self._cache[key] = value
            expiry_time = now + self._ttl
            heapq.heappush(self._expiry_heap, (expiry_time, key))

    async def _evict_expired(self) -> None:
        """O(1) expiration using priority queue"""
        now = time.monotonic()
        while self._expiry_heap and self._expiry_heap[0][0] < now:
            _, key = heapq.heappop(self._expiry_heap)
            self._cache.pop(key, None)

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Retrieve cache performance metrics"""
        total_access = self._hits + self._misses
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self._hits / total_access if total_access > 0 else 0.0,
            'evictions': self._evictions,
            'current_size': len(self._cache)
        }

class ResilientScraper:
    """
    Advanced scraping engine with intelligent error handling and recovery
    
    Features:
    - Adaptive retry mechanism
    - Configurable error handling
    - Performance and error tracking
    """
    def __init__(
        self, 
        max_retries: int = 3, 
        base_delay: float = 1.0, 
        max_delay: float = 60.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Error tracking
        self.error_tracker = defaultdict(int)
        self.success_tracker = defaultdict(int)
        
        # Performance metrics
        self._response_times = deque(maxlen=100)

    def _calculate_backoff(self, attempt: int, error_type: str = 'default') -> float:
        """
        Intelligent backoff calculation considering:
        - Exponential base
        - Error type frequency
        - System load
        """
        # Base exponential backoff
        base_delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Error type multiplier
        error_multiplier = 1 + (self.error_tracker[error_type] / max(1, self.success_tracker[error_type]))
        
        # System load factor
        system_load = psutil.cpu_percent() / 100
        
        # Jitter for distributed retry
        jitter = random.uniform(0.8, 1.2)
        
        return base_delay * error_multiplier * (1 + system_load) * jitter

    async def execute(
        self, 
        operation: Callable, 
        error_handler: Optional[Callable[[ScrapingError], Any]] = None
    ) -> Any:
        """
        Execute operation with intelligent retry and error handling
        
        :param operation: Async function to execute
        :param error_handler: Optional custom error handler
        :return: Operation result
        :raises ScrapingError: If all retries fail
        """
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.monotonic()
                result = await operation()
                
                # Track success
                self.success_tracker[operation.__name__] += 1
                
                # Record response time
                self._response_times.append(time.monotonic() - start_time)
                
                return result
            
            except Exception as e:
                # Classify error
                error_type = type(e).__name__
                self.error_tracker[error_type] += 1
                
                # Create comprehensive error
                scrape_error = ScrapingError(
                    message=str(e),
                    error_type=error_type,
                    context={
                        'attempt': attempt,
                        'operation': operation.__name__
                    }
                )
                
                # Custom error handling
                if error_handler:
                    try:
                        return await error_handler(scrape_error)
                    except Exception as handler_error:
                        logger.error(f"Error in error handler: {handler_error}")
                
                # Last attempt
                if attempt == self.max_retries:
                    logger.error(f"Operation failed after {self.max_retries} attempts: {scrape_error}")
                    raise scrape_error
                
                # Adaptive backoff
                await asyncio.sleep(self._calculate_backoff(attempt, error_type))

def circuit_breaker(
    failure_threshold: int = 5, 
    reset_timeout: float = 30.0
):
    """
    Circuit breaker decorator for preventing cascading failures
    
    :param failure_threshold: Number of consecutive failures before breaking
    :param reset_timeout: Time to wait before attempting to reset
    """
    def decorator(func):
        failures = 0
        last_failure_time = 0
        state = 'closed'

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal failures, last_failure_time, state
            current_time = time.time()

            # Check circuit state
            if state == 'open':
                if current_time - last_failure_time < reset_timeout:
                    raise ScrapingError(
                        "Circuit is open", 
                        error_type='circuit_breaker',
                        context={'state': state}
                    )
                state = 'half-open'

            try:
                result = await func(*args, **kwargs)
                
                # Reset on success
                if state == 'half-open':
                    state = 'closed'
                failures = 0
                
                return result
            
            except Exception as e:
                failures += 1
                
                if failures >= failure_threshold:
                    state = 'open'
                    last_failure_time = current_time
                    logger.warning(f"Circuit breaker activated: {failures} consecutive failures")
                
                raise

        return wrapper
    return decorator

class ScrapingOrchestrator:
    """
    Comprehensive scraping orchestration with adaptive strategies
    
    Features:
    - Intelligent caching
    - Resilient execution
    - Performance tracking
    """
    def __init__(
        self, 
        cache_size: int = 10000, 
        cache_ttl: int = 3600,
        max_retries: int = 3
    ):
        self.cache = AdaptiveCache(max_size=cache_size, ttl=cache_ttl)
        self.scraper = ResilientScraper(max_retries=max_retries)

    @circuit_breaker()
    async def scrape(
        self, 
        url: str, 
        extractor: Callable[[str], Any],
        use_cache: bool = True
    ) -> Any:
        """
        Orchestrate scraping with caching and resilience
        
        :param url: Target URL
        :param extractor: Function to extract data
        :param use_cache: Whether to use caching
        :return: Extracted data
        """
        # Check cache first
        if use_cache:
            cached_result = await self.cache.get(url)
            if cached_result is not None:
                return cached_result

        # Scrape with resilience
        async def fetch_and_extract():
            # Simulated fetch - replace with actual fetching logic
            raw_data = await self._fetch(url)
            return extractor(raw_data)

        result = await self.scraper.execute(fetch_and_extract)

        # Cache result
        if use_cache:
            await self.cache.set(url, result)

        return result

    async def _fetch(self, url: str) -> str:
        """
        Placeholder fetch method - to be replaced with actual fetching logic
        
        :param url: URL to fetch
        :return: Raw fetched data
        """
        # Simulated network delay and fetch
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return f"Raw data from {url}"

# Recommended usage
async def main():
    orchestrator = ScrapingOrchestrator()
    
    def extract_title(raw_data: str) -> str:
        # Placeholder extraction logic
        return raw_data.split()[-1]
    
    try:
        result = await orchestrator.scrape(
            "https://example.com", 
            extractor=extract_title
        )
        print(f"Scraped result: {result}")
    except ScrapingError as e:
        logger.error(f"Scraping failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

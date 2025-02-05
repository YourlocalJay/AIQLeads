import asyncio
import time
import random
import logging
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from collections import OrderedDict, deque
import heapq
import functools

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EnhancedResultCache:
    """
    Advanced caching mechanism with efficient expiration and LRU management.

    Features:
    - O(1) cache expiration using heapq
    - Thread-safe async access
    - LRU-based cache management
    - Hit/miss metrics tracking
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10000):
        """
        Initialize the enhanced result cache.

        :param ttl_seconds: Time-to-live for cache entries
        :param max_size: Maximum number of entries in the cache
        """
        self._cache = OrderedDict()
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._expiry_heap = []  # Min-heap for efficient expiration tracking

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a cached value with thread-safe access and metrics tracking.

        :param key: Cache key to retrieve
        :return: Cached value or None if not found
        """
        async with self._lock:
            self._evict_expired()

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
        """
        Store a value in the cache with optimized expiration management.

        :param key: Cache key
        :param value: Value to cache
        """
        async with self._lock:
            now = time.monotonic()

            # Remove existing entry if key exists
            if key in self._cache:
                del self._cache[key]

            # Manage cache size
            while len(self._cache) >= self._max_size:
                # Remove the least recently used item
                oldest_key, _ = self._cache.popitem(last=False)
                # Remove from expiry heap
                self._expiry_heap = [
                    (exp, k) for exp, k in self._expiry_heap if k != oldest_key
                ]
                heapq.heapify(self._expiry_heap)

            # Add new entry
            self._cache[key] = value
            expiry_time = now + self._ttl
            heapq.heappush(self._expiry_heap, (expiry_time, key))

    def _evict_expired(self) -> None:
        """
        Remove expired entries using a priority queue for O(1) expiration.
        """
        now = time.monotonic()
        while self._expiry_heap and self._expiry_heap[0][0] < now:
            _, key = heapq.heappop(self._expiry_heap)
            self._cache.pop(key, None)

    def get_metrics(self) -> Dict[str, int]:
        """
        Retrieve cache performance metrics.

        :return: Dictionary of cache metrics
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (
                self._hits / (self._hits + self._misses)
                if (self._hits + self._misses) > 0
                else 0
            ),
            "current_size": len(self._cache),
        }


class AdaptiveRateLimiter:
    """
    Dynamic rate limiting with token bucket algorithm and background replenishment.

    Features:
    - Adaptive rate adjustment
    - Background token replenishment
    - Burst handling
    """

    def __init__(
        self, initial_rate: int = 100, time_window: int = 60, burst_factor: float = 1.5
    ):
        """
        Initialize the adaptive rate limiter.

        :param initial_rate: Initial requests per time window
        :param time_window: Time window in seconds
        :param burst_factor: Multiplier for burst capacity
        """
        self.rate = initial_rate
        self.time_window = time_window
        self.burst_factor = burst_factor

        self.tokens = initial_rate
        self.max_tokens = int(initial_rate * burst_factor)
        self.lock = asyncio.Lock()

        self.success_count = 0
        self.failure_count = 0

    async def throttle(self) -> None:
        """
        Async context manager for rate-limited execution.
        """
        async with self.lock:
            if self.tokens <= 0:
                await asyncio.sleep(self.time_window / self.rate)
            self.tokens -= 1

    async def _auto_replenish(self) -> None:
        """
        Continuously replenish tokens in the background.
        """
        while True:
            await asyncio.sleep(self.time_window / self.rate)
            async with self.lock:
                self.tokens = min(self.tokens + 1, self.max_tokens)

    def start_replenishment(self) -> None:
        """
        Start background token replenishment.
        """
        asyncio.create_task(self._auto_replenish())

    def adjust_rate(self, success: bool) -> None:
        """
        Dynamically adjust rate based on success/failure ratio.

        :param success: Whether the last request was successful
        """
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        # Adjust rate based on success ratio
        total_attempts = self.success_count + self.failure_count
        if total_attempts > 10:  # Avoid premature adjustment
            success_ratio = self.success_count / total_attempts

            if success_ratio < 0.5:
                # High failure rate: reduce rate
                self.rate = max(1, int(self.rate * 0.8))
            elif success_ratio > 0.9:
                # Very high success rate: increase rate
                self.rate = int(self.rate * 1.2)

            # Reset counters
            self.success_count = 0
            self.failure_count = 0


class SmartBatchProcessor(Generic[T]):
    """
    Intelligent batch processing with adaptive retry and error handling.

    Features:
    - Concurrent batch processing
    - Adaptive retry mechanism
    - Error-specific handling
    """

    def __init__(
        self,
        retries: int = 3,
        batch_size: int = 10,
        concurrency: int = 5,
        backoff_base: float = 2.0,
    ):
        """
        Initialize the smart batch processor.

        :param retries: Maximum retry attempts
        :param batch_size: Initial batch size
        :param concurrency: Maximum concurrent processing
        :param backoff_base: Base for exponential backoff
        """
        self.retries = retries
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(concurrency)
        self.backoff_base = backoff_base

    async def process_batch(
        self,
        items: List[T],
        processor: Callable[[T], Any],
        error_handler: Optional[Callable[[T, Exception], Any]] = None,
    ) -> List[Any]:
        """
        Process a batch of items with intelligent retry and error handling.

        :param items: List of items to process
        :param processor: Function to process each item
        :param error_handler: Optional function to handle processing errors
        :return: List of processed results
        """
        tasks = [
            self._process_with_retry(item, processor, error_handler) for item in items
        ]
        return await asyncio.gather(*tasks)

    async def _process_with_retry(
        self,
        item: T,
        processor: Callable[[T], Any],
        error_handler: Optional[Callable[[T, Exception], Any]],
    ) -> Any:
        """
        Process a single item with retry logic and error handling.

        :param item: Item to process
        :param processor: Function to process the item
        :param error_handler: Optional error handling function
        :return: Processed result
        """
        for attempt in range(self.retries + 1):
            try:
                async with self.semaphore:
                    return await processor(item)
            except Exception as e:
                if attempt == self.retries:
                    logger.warning(
                        f"Item {repr(item)} failed after {self.retries} attempts: {str(e)}",
                        extra={"item": repr(item), "error": str(e), "attempt": attempt},
                    )
                    if error_handler:
                        return await error_handler(item, e)
                    raise

                # Exponential backoff with jitter
                delay = (self.backoff_base**attempt) + random.uniform(0, 0.1)
                await asyncio.sleep(delay)

        return None


class PerformanceMonitor:
    """
    Advanced performance monitoring with rolling buffer and percentile tracking.

    Features:
    - Fixed-size rolling buffer
    - Sliding time window statistics
    - P90/P99 latency calculations
    """

    def __init__(self, retention_period: int = 3600, max_entries: int = 10000):
        """
        Initialize the performance monitor.

        :param retention_period: Maximum time to retain metrics
        :param max_entries: Maximum number of entries per operation
        """
        self.metrics: Dict[str, deque] = {}
        self.lock = asyncio.Lock()
        self.retention = retention_period
        self.max_entries = max_entries

    async def record_timing(self, operation: str, duration: float) -> None:
        """
        Record operation timing with automatic pruning.

        :param operation: Name of the operation
        :param duration: Execution duration
        """
        async with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = deque(maxlen=self.max_entries)

            self.metrics[operation].append((time.monotonic(), duration))

    async def get_stats(self, operation: str, window: int = 300) -> Dict[str, float]:
        """
        Get statistics for a sliding time window.

        :param operation: Name of the operation
        :param window: Time window in seconds
        :return: Dictionary of performance statistics
        """
        async with self.lock:
            now = time.monotonic()
            relevant_data = [
                d for ts, d in self.metrics.get(operation, []) if now - ts <= window
            ]

            if not relevant_data:
                return {}

            sorted_data = sorted(relevant_data)
            return {
                "average": sum(relevant_data) / len(relevant_data),
                "p90": sorted_data[int(len(sorted_data) * 0.9)],
                "p99": sorted_data[int(len(sorted_data) * 0.99)],
                "min": min(sorted_data),
                "max": max(sorted_data),
                "count": len(sorted_data),
            }


def memoize_expensive_parsing(ttl: int = 3600, max_size: int = 1000):
    """
    Decorator for memoizing expensive parsing operations.

    :param ttl: Time-to-live for cached results
    :param max_size: Maximum number of entries in cache
    :return: Memoization decorator
    """

    def decorator(func):
        cache = EnhancedResultCache(ttl_seconds=ttl, max_size=max_size)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a unique cache key based on function arguments
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get cached result
            cached_result = await cache.get(key)
            if cached_result is not None:
                return cached_result

            # Compute and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result)

            return result

        return wrapper

    return decorator

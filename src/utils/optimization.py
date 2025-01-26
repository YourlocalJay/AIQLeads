"""
Optimization utilities for enhancing parser and scraper performance.
"""

import asyncio
from typing import TypeVar, List, Callable, Any, Dict, Optional
from functools import lru_cache
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ResultCache:
    """Thread-safe cache for storing parsed results."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached result if valid."""
        async with self._lock:
            if key not in self._cache:
                return None
                
            timestamp = self._timestamps[key]
            if datetime.utcnow() - timestamp > self._ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None
                
            return self._cache[key]

    async def set(self, key: str, value: Any) -> None:
        """Store result in cache."""
        async with self._lock:
            self._cache[key] = value
            self._timestamps[key] = datetime.utcnow()

    async def invalidate(self, key: str) -> None:
        """Remove item from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]

class BatchProcessor:
    """Efficient batch processing of items."""
    
    def __init__(
        self,
        batch_size: int = 100,
        max_concurrent: int = 10
    ):
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(
        self,
        items: List[T],
        processor: Callable[[T], Any]
    ) -> List[Any]:
        """
        Process items in optimized batches.

        Args:
            items: List of items to process
            processor: Async function to process each item

        Returns:
            List of processed results
        """
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *(self._process_item(item, processor) for item in batch)
            )
            results.extend(batch_results)
        return results

    async def _process_item(
        self,
        item: T,
        processor: Callable[[T], Any]
    ) -> Any:
        """Process single item with concurrency control."""
        async with self.semaphore:
            return await processor(item)

class RateLimiter:
    """Advanced rate limiting with dynamic adjustment."""
    
    def __init__(
        self,
        rate_limit: int,
        time_window: int,
        burst_size: Optional[int] = None
    ):
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.burst_size = burst_size or rate_limit
        self.tokens = self.burst_size
        self.last_update = datetime.utcnow()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire rate limiting tokens with dynamic adjustment.

        Args:
            tokens: Number of tokens to acquire
        """
        async with self.lock:
            await self._replenish()
            
            if tokens > self.burst_size:
                raise ValueError(f"Requested tokens {tokens} exceeds burst size {self.burst_size}")
            
            while self.tokens < tokens:
                replenish_time = (tokens - self.tokens) * (self.time_window / self.rate_limit)
                await asyncio.sleep(replenish_time)
                await self._replenish()
            
            self.tokens -= tokens

    async def _replenish(self) -> None:
        """Replenish rate limiting tokens."""
        now = datetime.utcnow()
        elapsed = (now - self.last_update).total_seconds()
        
        new_tokens = int(elapsed * (self.rate_limit / self.time_window))
        if new_tokens > 0:
            self.tokens = min(self.tokens + new_tokens, self.burst_size)
            self.last_update = now

@lru_cache(maxsize=1000)
def cache_parser_result(key: str, result: Any) -> Any:
    """Cache parser results for performance."""
    return result

class PerformanceMonitor:
    """Monitor and optimize performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()

    async def record_timing(self, operation: str, duration: float) -> None:
        """Record operation timing."""
        async with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration)

    def get_average_timing(self, operation: str) -> Optional[float]:
        """Get average timing for operation."""
        if operation not in self.metrics:
            return None
        return sum(self.metrics[operation]) / len(self.metrics[operation])

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        return {
            op: {
                'average': sum(timings) / len(timings),
                'min': min(timings),
                'max': max(timings),
                'count': len(timings)
            }
            for op, timings in self.metrics.items()
        }
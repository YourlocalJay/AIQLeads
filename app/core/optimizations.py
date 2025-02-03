"""
Core optimizations module for AIQLeads project.
Handles cache enhancement, performance tracking, and memory monitoring.
"""
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time: float
    memory_usage: float
    cache_hits: int
    cache_misses: int
    error_count: int

class CacheManager:
    """Enhanced caching system with performance tracking."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """Retrieve item from cache with performance tracking."""
        try:
            value = self._cache.get(key)
            if value is not None:
                self._hits += 1
            else:
                self._misses += 1
            return value
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
            
    def set(self, key: str, value: Any) -> bool:
        """Store item in cache with size management."""
        try:
            if len(self._cache) >= self._max_size:
                # Implement LRU eviction
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False
            
    @property
    def metrics(self) -> Dict[str, int]:
        """Return cache performance metrics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self._max_size
        }

class PerformanceTracker:
    """System-wide performance tracking."""
    
    def __init__(self):
        self._metrics = PerformanceMetrics(
            execution_time=0.0,
            memory_usage=0.0,
            cache_hits=0,
            cache_misses=0,
            error_count=0
        )
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    async def track_operation(self, operation_name: str):
        """Context manager for tracking operation performance."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            await self._record_metrics(operation_name, execution_time)
            
    async def _record_metrics(self, operation_name: str, execution_time: float):
        """Record performance metrics for an operation."""
        try:
            self._metrics.execution_time += execution_time
            # Submit memory usage tracking to thread pool
            self._executor.submit(self._track_memory_usage)
            logger.info(f"Operation {operation_name} completed in {execution_time:.3f}s")
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
            self._metrics.error_count += 1
            
    def _track_memory_usage(self):
        """Track system memory usage."""
        try:
            import psutil
            process = psutil.Process()
            self._metrics.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        except Exception as e:
            logger.error(f"Error tracking memory usage: {e}")
            
    @property
    def metrics(self) -> PerformanceMetrics:
        """Return current performance metrics."""
        return self._metrics

# Initialize global instances
cache_manager = CacheManager()
performance_tracker = PerformanceTracker()

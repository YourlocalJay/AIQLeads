import time
import logging
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

import psutil

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """
    Container for performance metrics.
    """
    execution_time: float = 0.0
    memory_usage: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0

class CacheManager:
    """
    Thread-safe LRU cache manager with performance tracking.
    """

    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            try:
                if key in self._cache:
                    self._hits += 1
                    self._cache.move_to_end(key)
                    return self._cache[key]
                else:
                    self._misses += 1
                    return None
            except Exception as e:
                logger.error(f"Cache retrieval error: {e}")
                return None

    def set(self, key: str, value: Any) -> bool:
        with self._lock:
            try:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
                self._cache[key] = value
                self._cache.move_to_end(key)
                return True
            except Exception as e:
                logger.error(f"Cache storage error: {e}")
                return False

    @property
    def metrics(self) -> Dict[str, int]:
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "max_size": self._max_size
            }

class PerformanceTracker:
    """
    Performance tracker for execution time and memory usage.
    """

    def __init__(self):
        self._metrics = PerformanceMetrics()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()

    def track_operation(self, operation_name: str):
        start_time = time.perf_counter()
        try:
            yield
        except Exception as e:
            logger.error(f"Operation '{operation_name}' failed: {e}")
            with self._lock:
                self._metrics.error_count += 1
            raise
        finally:
            execution_time = time.perf_counter() - start_time
            self._record_metrics(operation_name, execution_time)

    def _record_metrics(self, operation_name: str, execution_time: float):
        with self._lock:
            try:
                self._metrics.execution_time += execution_time
                logger.info(f"Operation '{operation_name}' completed in {execution_time:.3f}s")
                self._executor.submit(self._track_memory_usage)
            except Exception as e:
                logger.error(f"Error recording metrics: {e}")
                self._metrics.error_count += 1

    def _track_memory_usage(self):
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024
            with self._lock:
                self._metrics.memory_usage = memory_usage
        except Exception as e:
            logger.error(f"Error tracking memory usage: {e}")
            with self._lock:
                self._metrics.error_count += 1

    @property
    def metrics(self) -> PerformanceMetrics:
        with self._lock:
            return self._metrics

# Example global singletons
cache_manager = CacheManager()
performance_tracker = PerformanceTracker()

if __name__ == "__main__":
    import asyncio

    async def main():
        # CacheManager demo
        cache_manager.set("key1", "value1")
        value = cache_manager.get("key1")
        print(f"Cached value for 'key1': {value}")
        print(f"Cache metrics: {cache_manager.metrics}")

        # PerformanceTracker demo
        with performance_tracker.track_operation("example_operation"):
            await asyncio.sleep(1)

        print(f"Performance metrics: {performance_tracker.metrics}")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(main())

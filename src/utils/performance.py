"""
Performance enhancement utilities for optimizing data processing and resource usage.
"""

import asyncio
from typing import TypeVar, Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from collections import deque
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class PerformanceMetrics:
    """Performance metrics container."""
    operation_time: float
    memory_usage: int
    success_rate: float
    throughput: float

class ResourcePool:
    """
    Managed resource pool for efficient resource utilization.
    """
    
    def __init__(
        self,
        max_size: int,
        create_resource: Callable[[], Any],
        cleanup_resource: Callable[[Any], None]
    ):
        self.max_size = max_size
        self.create_resource = create_resource
        self.cleanup_resource = cleanup_resource
        self.available = asyncio.Queue()
        self.in_use = set()
        self.lock = asyncio.Lock()

    async def acquire(self) -> Any:
        """Acquire a resource from the pool."""
        try:
            resource = await self.available.get()
        except asyncio.QueueEmpty:
            async with self.lock:
                if len(self.in_use) < self.max_size:
                    resource = await self.create_resource()
                else:
                    resource = await self.available.get()
        
        self.in_use.add(resource)
        return resource

    async def release(self, resource: Any) -> None:
        """Release a resource back to the pool."""
        self.in_use.remove(resource)
        await self.available.put(resource)

class AsyncBatchProcessor:
    """
    Enhanced batch processor with adaptive sizing.
    """
    
    def __init__(
        self,
        min_batch_size: int = 10,
        max_batch_size: int = 1000,
        target_latency: float = 0.1
    ):
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_latency = target_latency
        self.current_batch_size = min_batch_size
        self.processing_times = deque(maxlen=100)

    async def process_items(
        self,
        items: List[T],
        processor: Callable[[List[T]], Any]
    ) -> List[Any]:
        """Process items with adaptive batch sizing."""
        results = []
        for i in range(0, len(items), self.current_batch_size):
            batch = items[i:i + self.current_batch_size]
            
            start_time = time.monotonic()
            batch_results = await processor(batch)
            processing_time = time.monotonic() - start_time
            
            self.processing_times.append(processing_time)
            self._adjust_batch_size()
            
            results.extend(batch_results)
        
        return results

    def _adjust_batch_size(self) -> None:
        """Adjust batch size based on processing times."""
        if not self.processing_times:
            return

        avg_time = sum(self.processing_times) / len(self.processing_times)
        
        if avg_time > self.target_latency:
            self.current_batch_size = max(
                self.min_batch_size,
                int(self.current_batch_size * 0.8)
            )
        else:
            self.current_batch_size = min(
                self.max_batch_size,
                int(self.current_batch_size * 1.2)
            )

class ConcurrencyManager:
    """
    Advanced concurrency management with adaptive throttling.
    """
    
    def __init__(
        self,
        initial_concurrency: int = 10,
        max_concurrency: int = 50,
        error_threshold: float = 0.1
    ):
        self.current_concurrency = initial_concurrency
        self.max_concurrency = max_concurrency
        self.error_threshold = error_threshold
        self.error_rate = 0.0
        self.semaphore = asyncio.Semaphore(initial_concurrency)
        self.lock = asyncio.Lock()

    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """Execute function with managed concurrency."""
        async with self.semaphore:
            try:
                result = await func(*args, **kwargs)
                await self._update_metrics(True)
                return result
            except Exception as e:
                await self._update_metrics(False)
                raise e

    async def _update_metrics(self, success: bool) -> None:
        """Update performance metrics and adjust concurrency."""
        async with self.lock:
            self.error_rate = 0.9 * self.error_rate + 0.1 * (0 if success else 1)
            
            if self.error_rate > self.error_threshold:
                self._reduce_concurrency()
            elif self.error_rate < self.error_threshold / 2:
                self._increase_concurrency()

    def _reduce_concurrency(self) -> None:
        """Reduce concurrency level."""
        new_concurrency = max(1, int(self.current_concurrency * 0.8))
        if new_concurrency != self.current_concurrency:
            self.current_concurrency = new_concurrency
            self.semaphore = asyncio.Semaphore(self.current_concurrency)

    def _increase_concurrency(self) -> None:
        """Increase concurrency level."""
        new_concurrency = min(
            self.max_concurrency,
            int(self.current_concurrency * 1.2)
        )
        if new_concurrency != self.current_concurrency:
            self.current_concurrency = new_concurrency
            self.semaphore = asyncio.Semaphore(self.current_concurrency)

class PerformanceOptimizer:
    """
    Comprehensive performance optimization manager.
    """
    
    def __init__(self):
        self.batch_processor = AsyncBatchProcessor()
        self.concurrency_manager = ConcurrencyManager()
        self.resource_pools: Dict[str, ResourcePool] = {}
        self.metrics = {}

    async def optimize_operation(
        self,
        operation_name: str,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with full optimization suite."""
        start_time = time.monotonic()
        
        try:
            result = await self.concurrency_manager.execute(func, *args, **kwargs)
            
            processing_time = time.monotonic() - start_time
            self._update_metrics(operation_name, processing_time, True)
            
            return result
            
        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._update_metrics(operation_name, processing_time, False)
            raise e

    def _update_metrics(
        self,
        operation: str,
        processing_time: float,
        success: bool
    ) -> None:
        """Update operation metrics."""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'total_operations': 0,
                'successful_operations': 0,
                'total_time': 0,
                'average_time': 0
            }
        
        metrics = self.metrics[operation]
        metrics['total_operations'] += 1
        if success:
            metrics['successful_operations'] += 1
        metrics['total_time'] += processing_time
        metrics['average_time'] = metrics['total_time'] / metrics['total_operations']

    def get_metrics(self, operation: str) -> Dict[str, Any]:
        """Retrieve metrics for specific operation."""
        if operation not in self.metrics:
            return {}
            
        metrics = self.metrics[operation]
        return {
            'success_rate': metrics['successful_operations'] / metrics['total_operations'],
            'average_time': metrics['average_time'],
            'total_operations': metrics['total_operations']
        }
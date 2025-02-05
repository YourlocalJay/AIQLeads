import time
import psutil
from contextlib import contextmanager
from typing import List, Dict


class PerformanceOptimizer:
    def __init__(self):
        self.metrics = {}
        self.optimization_strategies = [
            "batch_processing",
            "resource_monitoring",
            "adaptive_scaling",
        ]

    def optimize_batch(self, data: List[Dict]) -> List[Dict]:
        batch_size = len(data)
        if batch_size > 100:
            # Implement chunking for large batches
            return self._process_in_chunks(data)
        return self._process_batch(data)

    def _process_in_chunks(self, data: List[Dict], chunk_size: int = 100) -> List[Dict]:
        results = []
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            results.extend(self._process_batch(chunk))
        return results

    def _process_batch(self, batch: List[Dict]) -> List[Dict]:
        # Add processing logic here
        return batch

    @contextmanager
    def measure_performance(self):
        start_time = time.time()
        start_memory = self.get_memory_usage()

        metrics = {}
        try:
            yield metrics
        finally:
            end_time = time.time()
            end_memory = self.get_memory_usage()

            metrics.update(
                {
                    "duration_ms": (end_time - start_time) * 1000,
                    "memory_usage": end_memory,
                    "memory_delta": end_memory - start_memory,
                }
            )

    def get_memory_usage(self) -> int:
        process = psutil.Process()
        return process.memory_info().rss

    def check_resource_usage(self) -> Dict[str, float]:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        return {"cpu": cpu_percent, "memory": memory_percent}

    def get_optimization_strategies(self) -> List[str]:
        return self.optimization_strategies.copy()

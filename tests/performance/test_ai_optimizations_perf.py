import unittest
import time
import psutil
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, stdev
from app.core.ai_cache import AIOptimizedCache
from app.core.ai_circuit_breaker import AICircuitBreaker
from app.core.ai_monitoring import AIResourceMonitor


class TestAIOptimizationsPerformance(unittest.TestCase):
    def setUp(self):
        self.cache = AIOptimizedCache(max_size=10000)
        self.monitor = AIResourceMonitor(db_path=":memory:")
        self.circuit_breaker = AICircuitBreaker(failure_threshold=5, recovery_timeout=2)
        self.performance_thresholds = {
            "cache_write_time": 0.001,  # 1ms
            "cache_read_time": 0.0005,  # 0.5ms
            "monitoring_write_time": 0.002,  # 2ms
            "circuit_breaker_time": 0.001,  # 1ms
            "max_memory_increase": 100 * 1024 * 1024,  # 100MB
        }

    def test_memory_usage(self):
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Generate significant test load
        large_data = "x" * 10000
        for i in range(1000):
            key = f"memory_test_key_{i}"
            self.cache.set(key, large_data)
            self.monitor.record_metric(
                "memory_test", float(i), {"data_size": len(large_data)}
            )

        # Force garbage collection
        import gc

        gc.collect()

        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        self.assertLess(
            memory_increase,
            self.performance_thresholds["max_memory_increase"],
            f"Memory increase ({memory_increase / 1024 / 1024:.2f}MB) exceeds threshold",
        )

    def test_persistence_performance(self):
        # Test Redis persistence if available
        if self.cache._redis:
            # Redis write performance
            write_stats = self.measure_operation(
                lambda: self.cache._persist("redis_test_key", "test_value", None, 1.0)
            )
            self.assertLess(write_stats["mean"], 0.002)  # 2ms threshold for Redis

        # Test SQLite persistence
        write_stats = self.measure_operation(
            lambda: self.monitor._conn.execute(
                "INSERT OR REPLACE INTO metrics (timestamp, metric_name, value, context) "
                "VALUES (?, ?, ?, ?)",
                (datetime.now(), "test_metric", 1.0, "{}"),
            )
        )
        self.assertLess(write_stats["mean"], 0.005)  # 5ms threshold for SQLite

    def test_resource_efficiency(self):
        # CPU usage test
        process = psutil.Process(os.getpid())
        initial_cpu_percent = process.cpu_percent()

        # Generate load
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(1000):
                futures.append(
                    executor.submit(self.cache.set, f"key_{i}", f"value_{i}")
                )
                futures.append(
                    executor.submit(self.monitor.record_metric, "test", float(i))
                )

            for future in futures:
                future.result()

        # Check CPU usage
        final_cpu_percent = process.cpu_percent()
        cpu_increase = final_cpu_percent - initial_cpu_percent
        self.assertLess(
            cpu_increase, 50
        )  # Should not increase CPU usage by more than 50%

    def test_load_distribution(self):
        # Test even distribution of load across threads
        thread_timings = {}

        def worker_operation(thread_id, iterations):
            start_time = time.perf_counter()
            for i in range(iterations):
                self.cache.set(f"thread_{thread_id}_key_{i}", "test_value")
                self.monitor.record_metric("thread_test", float(i))
            return time.perf_counter() - start_time

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for thread_id in range(10):
                futures[thread_id] = executor.submit(worker_operation, thread_id, 100)

            for thread_id, future in futures.items():
                thread_timings[thread_id] = future.result()

        # Calculate timing statistics
        timing_values = list(thread_timings.values())
        timing_mean = mean(timing_values)
        timing_stdev = stdev(timing_values)

        # Verify even distribution (standard deviation should be < 20% of mean)
        self.assertLess(timing_stdev / timing_mean, 0.2)


if __name__ == "__main__":
    unittest.main()

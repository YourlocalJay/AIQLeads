import unittest
import time
from src.utils.performance_optimizer import PerformanceOptimizer
from src.core import SystemIntegration


class TestPerformanceBenchmarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.optimizer = PerformanceOptimizer()
        cls.system = SystemIntegration()

    def test_batch_processing_performance(self):
        batch_sizes = [10, 100, 1000]
        results = {}

        for size in batch_sizes:
            test_data = [{"id": i, "value": f"test_{i}"} for i in range(size)]
            start_time = time.time()
            self.optimizer.optimize_batch(test_data)
            duration = time.time() - start_time
            results[size] = duration

            self.assertLess(duration, size * 0.01)  # 10ms per item threshold

    def test_system_throughput(self):
        request_count = 1000
        start_time = time.time()

        for _ in range(request_count):
            self.system.process_request({"type": "benchmark"})

        duration = time.time() - start_time
        requests_per_second = request_count / duration

        self.assertGreater(requests_per_second, 100)  # Minimum 100 RPS

    def test_memory_usage(self):
        initial_memory = self.optimizer.get_memory_usage()
        large_data = [{"data": "x" * 1000} for _ in range(1000)]

        with self.optimizer.measure_performance() as metrics:
            self.optimizer.optimize_batch(large_data)

        memory_increase = metrics["memory_usage"] - initial_memory
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # Max 100MB increase


if __name__ == "__main__":
    unittest.main()

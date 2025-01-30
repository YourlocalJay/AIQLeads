import unittest
from unittest.mock import Mock, patch
from src.utils.performance_optimizer import PerformanceOptimizer

class TestPerformanceOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = PerformanceOptimizer()
        self.mock_metrics = Mock()

    def test_batch_processing_optimization(self):
        test_data = [{'id': i, 'value': f'test_{i}'} for i in range(10)]
        result = self.optimizer.optimize_batch(test_data)
        self.assertEqual(len(result), len(test_data))
        self.assertTrue(all(isinstance(item, dict) for item in result))

    @patch('src.utils.performance_optimizer.monitor_resources')
    def test_resource_monitoring(self, mock_monitor):
        mock_monitor.return_value = {'cpu': 50, 'memory': 70}
        metrics = self.optimizer.check_resource_usage()
        self.assertIn('cpu', metrics)
        self.assertIn('memory', metrics)

    def test_performance_metrics_collection(self):
        with self.optimizer.measure_performance() as metrics:
            # Simulate some work
            _ = [i * i for i in range(1000)]
        self.assertIn('duration_ms', metrics)
        self.assertIn('memory_usage', metrics)

    def test_optimization_strategies(self):
        strategies = self.optimizer.get_optimization_strategies()
        self.assertIsInstance(strategies, list)
        self.assertTrue(len(strategies) > 0)

if __name__ == '__main__':
    unittest.main()
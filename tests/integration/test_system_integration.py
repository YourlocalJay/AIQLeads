import unittest
from unittest.mock import patch
from src.core import SystemIntegration
from src.utils.performance_optimizer import PerformanceOptimizer

class TestSystemIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.system = SystemIntegration()
        cls.optimizer = PerformanceOptimizer()

    def test_end_to_end_flow(self):
        test_data = {'user_id': '123', 'action': 'purchase'}
        with self.system.transaction() as tx:
            result = tx.process(test_data)
            self.assertTrue(result['success'])
            self.assertIn('transaction_id', result)

    @patch('src.core.redis_client')
    def test_redis_integration(self, mock_redis):
        mock_redis.get.return_value = b'test_value'
        result = self.system.cache_lookup('test_key')
        self.assertEqual(result, 'test_value')
        mock_redis.get.assert_called_once_with('test_key')

    def test_performance_under_load(self):
        with self.optimizer.measure_performance() as metrics:
            for _ in range(100):
                self.system.process_request({'type': 'test'})
        self.assertLess(metrics['duration_ms'], 5000)  # 5 second threshold

    def test_error_recovery(self):
        with patch('src.core.process_transaction') as mock_process:
            mock_process.side_effect = [Exception('Test error'), {'success': True}]
            result = self.system.process_with_retry({'test': 'data'})
            self.assertTrue(result['success'])
            self.assertEqual(mock_process.call_count, 2)

if __name__ == '__main__':
    unittest.main()
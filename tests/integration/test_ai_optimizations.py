import unittest
import threading
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from app.core.ai_cache import AIOptimizedCache
from app.core.ai_circuit_breaker import AICircuitBreaker
from app.core.ai_monitoring import AIResourceMonitor

class TestAIOptimizationsIntegration(unittest.TestCase):
    def setUp(self):
        self.cache = AIOptimizedCache(max_size=100)
        self.monitor = AIResourceMonitor(db_path=':memory:')
        self.circuit_breaker = AICircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5
        )

    def test_cache_with_monitoring(self):
        # Test cache operations with monitoring
        def cache_operation():
            start_time = time.time()
            
            # Cache operation
            self.cache.set('test_key', 'test_value', weight=1.5)
            value = self.cache.get('test_key')
            
            # Record metrics
            operation_time = time.time() - start_time
            self.monitor.record_metric(
                'cache_operation_time',
                operation_time,
                {'operation': 'get', 'key': 'test_key'}
            )
            
            return value

        # Run multiple cache operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(lambda _: cache_operation(), range(10)))

        # Verify cache operations
        self.assertTrue(all(r == 'test_value' for r in results))

        # Check monitoring data
        metrics = self.monitor.get_metrics(
            'cache_operation_time',
            datetime.now() - timedelta(minutes=5)
        )
        self.assertGreater(len(metrics), 0)

    def test_circuit_breaker_with_monitoring(self):
        @self.circuit_breaker
        def failing_operation():
            raise ValueError("Test failure")

        # Test circuit breaker with monitoring
        def monitored_operation():
            start_time = time.time()
            try:
                failing_operation()
            except Exception as e:
                # Record failure metrics
                self.monitor.record_metric(
                    'operation_failure',
                    1.0,
                    {'error_type': type(e).__name__}
                )
                raise
            finally:
                # Record operation time
                operation_time = time.time() - start_time
                self.monitor.record_metric(
                    'operation_time',
                    operation_time
                )

        # Execute operations and verify circuit breaker behavior
        failure_count = 0
        for _ in range(5):
            try:
                monitored_operation()
            except Exception:
                failure_count += 1

        # Circuit should be open after 3 failures
        self.assertEqual(self.circuit_breaker.get_state(), "OPEN")
        
        # Verify monitoring data
        failure_metrics = self.monitor.get_metrics(
            'operation_failure',
            datetime.now() - timedelta(minutes=5)
        )
        self.assertEqual(len(failure_metrics), failure_count)

    def test_full_system_integration(self):
        # Test all components working together
        @self.circuit_breaker
        def complex_operation(key, value):
            start_time = time.time()
            
            try:
                # Cache operation
                self.cache.set(key, value)
                result = self.cache.get(key)
                
                # Record success
                self.monitor.record_metric(
                    'operation_success',
                    1.0,
                    {'operation': 'cache_access'}
                )
                
                return result
                
            except Exception as e:
                # Record failure
                self.monitor.record_metric(
                    'operation_failure',
                    1.0,
                    {'error_type': type(e).__name__}
                )
                raise
            finally:
                # Record operation time
                operation_time = time.time() - start_time
                self.monitor.record_metric(
                    'operation_time',
                    operation_time
                )

        # Run concurrent operations
        def worker(i):
            return complex_operation(f'key_{i}', f'value_{i}')

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(worker, range(20)))

        # Verify results
        self.assertEqual(len(results), 20)
        self.assertTrue(all(results[i] == f'value_{i}' for i in range(20)))

        # Verify monitoring data
        success_metrics = self.monitor.get_metrics(
            'operation_success',
            datetime.now() - timedelta(minutes=5)
        )
        self.assertEqual(len(success_metrics), 20)

        # Check system performance
        perf_stats = self.monitor.get_aggregates(
            'operation_time',
            datetime.now() - timedelta(minutes=5)
        )
        self.assertIsNotNone(perf_stats['average'])
        self.assertLess(perf_stats['average'], 1.0)  # Performance threshold

    def test_error_recovery(self):
        # Test system recovery after failures
        @self.circuit_breaker
        def unstable_operation():
            if getattr(self, '_error_count', 0) < 3:
                self._error_count = getattr(self, '_error_count', 0) + 1
                raise ValueError("Temporary failure")
            return "Success"

        # Run operations until circuit breaker opens
        self._error_count = 0
        for _ in range(3):
            try:
                unstable_operation()
            except ValueError:
                pass

        # Verify circuit breaker is open
        self.assertEqual(self.circuit_breaker.get_state(), "OPEN")

        # Wait for recovery timeout
        time.sleep(6)  # recovery_timeout + 1

        # System should recover
        result = unstable_operation()
        self.assertEqual(result, "Success")
        
        # Verify circuit breaker has recovered
        self.assertEqual(self.circuit_breaker.get_state(), "CLOSED")

        # Check monitoring data
        recovery_time = self.monitor.get_metrics(
            'operation_time',
            datetime.now() - timedelta(minutes=5)
        )
        self.assertGreater(len(recovery_time), 0)

if __name__ == '__main__':
    unittest.main()
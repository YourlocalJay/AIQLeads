"""
Performance component test suite
Tests monitoring, optimization, and management functionality
"""

import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.performance.monitor import PerformanceMonitor
from src.performance.optimizer import PerformanceOptimizer
from src.performance.manager import PerformanceManager

class TestPerformanceMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = PerformanceMonitor(history_size=100)
        
    def test_measurement_lifecycle(self):
        """Test complete measurement cycle"""
        # Start measurement
        self.monitor.start_measurement("test_op")
        
        # Simulate work
        time.sleep(0.1)
        
        # End measurement
        metrics = self.monitor.end_measurement("test_op")
        
        # Verify metrics
        self.assertIn("duration_ms", metrics)
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_delta_bytes", metrics)
        self.assertTrue(metrics["duration_ms"] > 0)
        
    def test_history_management(self):
        """Test historical data management"""
        # Add multiple measurements
        for i in range(5):
            self.monitor.start_measurement(f"op_{i}")
            time.sleep(0.1)
            self.monitor.end_measurement(f"op_{i}")
            
        history = self.monitor.get_history()
        self.assertEqual(len(history), 5)
        
    def test_statistics_generation(self):
        """Test statistics calculation"""
        # Add measurements
        for i in range(3):
            self.monitor.start_measurement("test_op")
            time.sleep(0.1)
            self.monitor.end_measurement("test_op")
            
        stats = self.monitor.get_statistics()
        self.assertIn("test_op", stats)
        self.assertIn("avg_duration_ms", stats["test_op"])

class TestPerformanceOptimizer(unittest.TestCase):
    def setUp(self):
        self.thresholds = {
            "duration_ms": 100,
            "cpu_percent": 50,
            "memory_bytes": 1000000
        }
        self.optimizer = PerformanceOptimizer(self.thresholds)
        
    def test_metric_analysis(self):
        """Test metric analysis functionality"""
        metrics = {
            "duration_ms": 150,
            "cpu_percent": 60,
            "memory_delta_bytes": 500000
        }
        
        suggestions = self.optimizer.analyze_metrics(metrics)
        self.assertTrue(len(suggestions) > 0)
        
    def test_optimization_application(self):
        """Test optimization application"""
        metrics = {
            "duration_ms": 200,
            "cpu_percent": 80,
            "memory_delta_bytes": 2000000
        }
        
        result = self.optimizer.optimize_operation("test_op", metrics)
        self.assertIn("suggestions", result)
        self.assertIn("applied_optimizations", result)
        
    def test_threshold_adjustment(self):
        """Test adaptive threshold adjustment"""
        metrics_history = [
            {"duration_ms": 80, "cpu_percent": 40},
            {"duration_ms": 90, "cpu_percent": 45}
        ]
        
        original_thresholds = self.thresholds.copy()
        self.optimizer.adjust_thresholds(metrics_history)
        
        # Verify thresholds were adjusted
        self.assertNotEqual(self.optimizer.thresholds, original_thresholds)

class TestPerformanceManager(unittest.TestCase):
    def setUp(self):
        self.thresholds = {
            "duration_ms": 100,
            "cpu_percent": 50,
            "memory_bytes": 1000000
        }
        self.manager = PerformanceManager(self.thresholds)
        
    def test_operation_management(self):
        """Test operation lifecycle management"""
        # Start operation
        self.manager.start_operation("test_op")
        self.assertIn("test_op", self.manager.active_operations)
        
        # End operation
        metrics = self.manager.end_operation("test_op")
        self.assertNotIn("test_op", self.manager.active_operations)
        self.assertIsInstance(metrics, dict)
        
    def test_trend_analysis(self):
        """Test performance trend analysis"""
        # Add historical data
        for i in range(3):
            self.manager.start_operation("test_op")
            time.sleep(0.1)
            self.manager.end_operation("test_op")
            
        trends = self.manager.analyze_trends(days=1)
        self.assertIn("test_op", trends)
        
    def test_report_generation(self):
        """Test performance report generation"""
        # Add some data
        self.manager.start_operation("test_op")
        time.sleep(0.1)
        self.manager.end_operation("test_op")
        
        report = self.manager.get_performance_report()
        self.assertIn("monitoring", report)
        self.assertIn("optimization", report)

def run_tests():
    """Execute all performance tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)

if __name__ == '__main__':
    run_tests()
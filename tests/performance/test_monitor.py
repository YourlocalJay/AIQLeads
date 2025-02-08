"""
Comprehensive test suite for PerformanceMonitor
Tests all major functionality and edge cases
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.performance.monitor import PerformanceMonitor

class TestPerformanceMonitor:
    @pytest.fixture
    def monitor(self):
        return PerformanceMonitor(history_size=100)
        
    def test_init(self, monitor):
        """Test monitor initialization"""
        assert monitor.metrics == {}
        assert len(monitor.history) == 0
        assert isinstance(monitor.start_time, datetime)
        
    def test_start_measurement(self, monitor):
        """Test starting measurement"""
        monitor.start_measurement("test_op")
        assert "test_op" in monitor.metrics
        metrics = monitor.metrics["test_op"]
        assert "start_time" in metrics
        assert "start_cpu" in metrics
        assert "start_memory" in metrics
        assert "start_io" in metrics
        assert "start_network" in metrics
        
    def test_end_measurement(self, monitor):
        """Test ending measurement and metric calculation"""
        monitor.start_measurement("test_op")
        time.sleep(0.1)  # Ensure measurable duration
        metrics = monitor.end_measurement("test_op")
        
        assert metrics["operation"] == "test_op"
        assert metrics["duration_ms"] > 0
        assert isinstance(metrics["cpu_percent"], (int, float))
        assert isinstance(metrics["memory_delta_bytes"], (int, float))
        assert isinstance(metrics["io_read_bytes"], (int, float))
        assert isinstance(metrics["io_write_bytes"], (int, float))
        assert isinstance(metrics["network_sent_bytes"], (int, float))
        assert isinstance(metrics["network_recv_bytes"], (int, float))
        assert isinstance(metrics["timestamp"], datetime)
        
    def test_end_measurement_invalid_operation(self, monitor):
        """Test ending measurement for non-existent operation"""
        with pytest.raises(ValueError):
            monitor.end_measurement("invalid_op")
            
    def test_get_history(self, monitor):
        """Test retrieving measurement history"""
        # Add some measurements
        operations = ["op1", "op2", "op3"]
        for op in operations:
            monitor.start_measurement(op)
            time.sleep(0.1)
            monitor.end_measurement(op)
            
        history = monitor.get_history()
        assert len(history) == len(operations)
        assert all(isinstance(m, dict) for m in history)
        assert all(m["operation"] in operations for m in history)
        
    def test_get_statistics(self, monitor):
        """Test calculating statistics from history"""
        # Add multiple measurements for same operation
        op = "test_op"
        for _ in range(3):
            monitor.start_measurement(op)
            time.sleep(0.1)
            monitor.end_measurement(op)
            
        stats = monitor.get_statistics()
        assert op in stats
        op_stats = stats[op]
        assert op_stats["count"] == 3
        assert "avg_duration_ms" in op_stats
        assert "min_duration_ms" in op_stats
        assert "max_duration_ms" in op_stats
        assert "avg_cpu_percent" in op_stats
        assert "avg_memory_delta_bytes" in op_stats
        
    def test_history_size_limit(self):
        """Test history size limitation"""
        size = 5
        monitor = PerformanceMonitor(history_size=size)
        
        # Add more measurements than size limit
        for i in range(size + 5):
            monitor.start_measurement(f"op{i}")
            monitor.end_measurement(f"op{i}")
            
        assert len(monitor.get_history()) == size
        
    def test_check_thresholds(self, monitor):
        """Test threshold violation detection"""
        thresholds = {
            "test_op": {
                "duration_ms": 50,
                "cpu_percent": 10
            }
        }
        
        monitor.start_measurement("test_op")
        time.sleep(0.1)  # Ensure threshold violation
        monitor.end_measurement("test_op")
        
        violations = monitor.check_thresholds(thresholds)
        assert len(violations) > 0
        assert all(v["operation"] == "test_op" for v in violations)
        
    def test_generate_report(self, monitor):
        """Test comprehensive report generation"""
        # Add some measurements
        monitor.start_measurement("op1")
        time.sleep(0.1)
        monitor.end_measurement("op1")
        
        report = monitor.generate_report()
        assert isinstance(report["start_time"], datetime)
        assert isinstance(report["end_time"], datetime)
        assert report["total_operations"] == 1
        assert "statistics" in report
        assert "system_info" in report
        
        system_info = report["system_info"]
        assert "cpu_count" in system_info
        assert "memory_total" in system_info
        assert "disk_usage" in system_info
        assert "load_avg" in system_info
        
    @patch('psutil.cpu_percent')
    @patch('psutil.Process')
    def test_resource_measurement_errors(self, mock_process, mock_cpu):
        """Test handling of resource measurement errors"""
        mock_cpu.side_effect = Exception("CPU measurement failed")
        mock_process.side_effect = Exception("Process info unavailable")
        
        monitor = PerformanceMonitor()
        monitor.start_measurement("error_test")
        metrics = monitor.end_measurement("error_test")
        
        # Should still have basic metrics
        assert metrics["operation"] == "error_test"
        assert "duration_ms" in metrics
        assert "timestamp" in metrics
        
    def test_concurrent_measurements(self, monitor):
        """Test handling multiple concurrent measurements"""
        operations = ["op1", "op2", "op3"]
        
        # Start all operations
        for op in operations:
            monitor.start_measurement(op)
            
        # End in different order
        results = []
        for op in reversed(operations):
            results.append(monitor.end_measurement(op))
            
        assert len(results) == len(operations)
        assert all(r["operation"] in operations for r in results)
        
    def test_long_running_operation(self, monitor):
        """Test measuring long-running operation"""
        monitor.start_measurement("long_op")
        time.sleep(1)  # Longer operation
        metrics = monitor.end_measurement("long_op")
        
        assert metrics["duration_ms"] >= 1000  # At least 1 second
        
    def test_empty_statistics(self, monitor):
        """Test statistics calculation with no history"""
        stats = monitor.get_statistics()
        assert stats == {}
        
    def test_invalid_threshold_format(self, monitor):
        """Test handling invalid threshold format"""
        monitor.start_measurement("test_op")
        monitor.end_measurement("test_op")
        
        # Invalid threshold formats
        invalid_thresholds = [
            None,
            {},
            {"test_op": None},
            {"test_op": "invalid"},
            {"test_op": {"invalid_metric": 100}}
        ]
        
        for threshold in invalid_thresholds:
            violations = monitor.check_thresholds(threshold)
            assert isinstance(violations, list)
            
    def test_memory_cleanup(self, monitor):
        """Test memory cleanup after measurements"""
        initial_metrics = len(monitor.metrics)
        
        monitor.start_measurement("test_op")
        assert len(monitor.metrics) == initial_metrics + 1
        
        monitor.end_measurement("test_op")
        assert len(monitor.metrics) == initial_metrics
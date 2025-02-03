"""
Unit tests for the monitoring system.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from app.core.monitoring import (
    ResourceMonitor,
    ResourceMetrics,
    resource_monitor,
    start_monitoring
)

@pytest.fixture
def monitor():
    """Fixture providing a clean ResourceMonitor instance."""
    return ResourceMonitor(sampling_interval=0.1)

class MockPsutilProcess:
    """Mock for psutil.Process."""
    def cpu_percent(self):
        return 25.0

    def memory_info(self):
        return Mock(rss=1024 * 1024 * 100)  # 100MB

    def num_threads(self):
        return 10

    def num_handles(self):
        return 100

@pytest.fixture
def mock_psutil():
    """Fixture providing mock psutil functions."""
    with patch('psutil.Process', return_value=MockPsutilProcess()), \
         patch('psutil.virtual_memory', return_value=Mock(
             available=1024 * 1024 * 1024,  # 1GB
             total=2 * 1024 * 1024 * 1024   # 2GB
         )), \
         patch('psutil.disk_usage', return_value=Mock(
             percent=75.0
         )), \
         patch('psutil.net_io_counters', return_value=Mock(
             _asdict=lambda: {'bytes_sent': 1000, 'bytes_recv': 2000}
         )):
        yield

class TestResourceMonitor:
    """Test suite for ResourceMonitor class."""

    @pytest.mark.asyncio
    async def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor._sampling_interval == 0.1
        assert monitor._running is False
        assert isinstance(monitor._metrics, ResourceMetrics)
        assert len(monitor._history) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor, mock_psutil):
        """Test starting and stopping monitoring."""
        # Start monitoring in background
        task = asyncio.create_task(monitor.start_monitoring())
        await asyncio.sleep(0.3)  # Allow some samples to collect
        
        # Stop monitoring
        await monitor.stop_monitoring()
        await task
        
        # Verify metrics were collected
        metrics = monitor.get_current_metrics()
        assert metrics.cpu_percent == 25.0
        assert metrics.memory_used == 100.0  # 100MB
        assert metrics.thread_count == 10
        assert len(monitor.get_metrics_history()) > 0

    @pytest.mark.asyncio
    async def test_metrics_collection(self, monitor, mock_psutil):
        """Test metrics collection."""
        task = asyncio.create_task(monitor.start_monitoring())
        await asyncio.sleep(0.3)
        await monitor.stop_monitoring()
        await task

        history = monitor.get_metrics_history()
        assert len(history) > 0
        
        # Verify metrics values
        latest = history[-1]
        assert latest.cpu_percent == 25.0
        assert latest.memory_used == 100.0
        assert latest.disk_usage == 75.0
        assert latest.thread_count == 10
        assert latest.handle_count == 100

    @pytest.mark.asyncio
    async def test_average_metrics(self, monitor, mock_psutil):
        """Test average metrics calculation."""
        task = asyncio.create_task(monitor.start_monitoring())
        await asyncio.sleep(0.3)
        await monitor.stop_monitoring()
        await task

        avg_metrics = monitor.get_average_metrics(window_minutes=1)
        assert avg_metrics is not None
        assert avg_metrics.cpu_percent == 25.0
        assert avg_metrics.memory_used == 100.0
        assert avg_metrics.thread_count == 10

    def test_resource_warnings(self, monitor, mock_psutil):
        """Test resource warning generation."""
        with patch.object(MockPsutilProcess, 'cpu_percent', return_value=85.0):
            task = asyncio.create_task(monitor.start_monitoring())
            asyncio.run_coroutine_threadsafe(asyncio.sleep(0.2), asyncio.get_event_loop())
            asyncio.run_coroutine_threadsafe(monitor.stop_monitoring(), asyncio.get_event_loop())
            
            warnings = monitor.get_resource_warnings()
            assert len(warnings) > 0
            assert any("CPU usage" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_cost_estimation(self, monitor, mock_psutil):
        """Test cost estimation calculations."""
        task = asyncio.create_task(monitor.start_monitoring())
        await asyncio.sleep(0.3)
        await monitor.stop_monitoring()
        await task

        # Test current cost
        metrics = monitor.get_current_metrics()
        assert metrics.cost_estimate >= 0

        # Test monthly projection
        monthly_cost = monitor.estimate_monthly_cost()
        assert monthly_cost > 0
        assert monthly_cost < 1000  # Sanity check on cost magnitude

    @pytest.mark.asyncio
    async def test_metrics_history_limit(self, monitor, mock_psutil):
        """Test metrics history size limiting."""
        monitor._history = [ResourceMetrics() for _ in range(1000)]
        
        task = asyncio.create_task(monitor.start_monitoring())
        await asyncio.sleep(0.3)
        await monitor.stop_monitoring()
        await task

        assert len(monitor.get_metrics_history()) <= 1000

class TestGlobalMonitor:
    """Test suite for global monitor instance."""

    @pytest.mark.asyncio
    async def test_global_monitor(self, mock_psutil):
        """Test global monitor instance."""
        task = asyncio.create_task(start_monitoring())
        await asyncio.sleep(0.3)
        await resource_monitor.stop_monitoring()
        await task

        metrics = resource_monitor.get_current_metrics()
        assert metrics.cpu_percent == 25.0
        assert metrics.memory_used == 100.0
        assert len(resource_monitor.get_metrics_history()) > 0

if __name__ == "__main__":
    pytest.main([__file__])
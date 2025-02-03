"""
Unit tests for core optimizations module.
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch
from app.core.optimizations import (
    CacheManager,
    PerformanceTracker,
    PerformanceMetrics
)

@pytest.fixture
def cache_manager():
    """Fixture providing a clean CacheManager instance."""
    return CacheManager(max_size=3)

@pytest.fixture
def performance_tracker():
    """Fixture providing a clean PerformanceTracker instance."""
    return PerformanceTracker()

class TestCacheManager:
    """Test suite for CacheManager class."""

    def test_cache_initialization(self, cache_manager):
        """Test cache initialization with correct max size."""
        assert cache_manager._max_size == 3
        assert len(cache_manager._cache) == 0
        assert cache_manager._hits == 0
        assert cache_manager._misses == 0
        assert isinstance(cache_manager._lock, threading.Lock)

    def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations."""
        # Set and get a value
        assert cache_manager.set("test_key", "test_value") is True
        value = cache_manager.get("test_key")
        assert value == "test_value"
        assert cache_manager._hits == 1
        assert cache_manager._misses == 0

        # Get non-existent value
        value = cache_manager.get("nonexistent")
        assert value is None
        assert cache_manager._hits == 1
        assert cache_manager._misses == 1

    def test_cache_lru_eviction(self, cache_manager):
        """Test LRU cache eviction policy."""
        # Fill cache
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache_manager.get("key1")
        
        # Add new item, should evict key2
        cache_manager.set("key4", "value4")
        
        assert cache_manager.get("key1") == "value1"  # Still present
        assert cache_manager.get("key2") is None      # Evicted
        assert cache_manager.get("key3") == "value3"  # Still present
        assert cache_manager.get("key4") == "value4"  # Newly added

    def test_cache_thread_safety(self, cache_manager):
        """Test cache thread safety."""
        def worker(tid):
            for i in range(100):
                key = f"key{i}"
                cache_manager.set(key, f"value{tid}-{i}")
                cache_manager.get(key)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        metrics = cache_manager.metrics
        assert metrics["hits"] + metrics["misses"] == 300  # Total operations
        assert metrics["size"] <= cache_manager._max_size  # Size constraint maintained

    def test_cache_metrics(self, cache_manager):
        """Test cache metrics collection."""
        # Perform operations
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")      # Hit
        cache_manager.get("missing")   # Miss
        
        metrics = cache_manager.metrics
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["size"] == 1
        assert metrics["max_size"] == 3

class TestPerformanceTracker:
    """Test suite for PerformanceTracker class."""

    def test_track_operation_success(self, performance_tracker):
        """Test successful operation tracking."""
        with performance_tracker.track_operation("test_op"):
            time.sleep(0.1)  # Simulate work
            
        metrics = performance_tracker.metrics
        assert metrics.execution_time > 0
        assert metrics.error_count == 0
        assert metrics.memory_usage >= 0

    def test_track_operation_error(self, performance_tracker):
        """Test error tracking in operations."""
        try:
            with performance_tracker.track_operation("error_op"):
                raise ValueError("Test error")
        except ValueError:
            pass
            
        metrics = performance_tracker.metrics
        assert metrics.error_count == 1
        assert metrics.execution_time > 0

    def test_thread_safety(self, performance_tracker):
        """Test performance tracker thread safety."""
        def worker():
            with performance_tracker.track_operation(f"thread_op_{threading.get_ident()}"):
                time.sleep(0.01)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        metrics = performance_tracker.metrics
        assert metrics.execution_time > 0
        assert metrics.error_count == 0

    def test_memory_tracking(self, performance_tracker):
        """Test memory usage tracking."""
        with patch('psutil.Process') as mock_process:
            mock_memory_info = Mock()
            mock_memory_info.rss = 1024 * 1024  # 1 MB
            mock_process.return_value.memory_info.return_value = mock_memory_info
            
            with performance_tracker.track_operation("memory_test"):
                pass
                
            # Allow time for the background thread to update memory metrics
            time.sleep(0.1)
            
        assert performance_tracker.metrics.memory_usage > 0

    def test_nested_operations(self, performance_tracker):
        """Test nested operation tracking."""
        with performance_tracker.track_operation("outer"):
            time.sleep(0.1)
            with performance_tracker.track_operation("inner"):
                time.sleep(0.1)

        metrics = performance_tracker.metrics
        assert metrics.execution_time >= 0.2
        assert metrics.error_count == 0

if __name__ == "__main__":
    pytest.main([__file__])
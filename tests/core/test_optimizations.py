"""
Unit tests for core optimizations module.
Tests cache management and performance tracking functionality.
"""
import pytest
import asyncio
import time
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

    def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations."""
        # Set and get a value
        cache_manager.set("test_key", "test_value")
        value = cache_manager.get("test_key")
        assert value == "test_value"
        assert cache_manager._hits == 1
        assert cache_manager._misses == 0

        # Get non-existent value
        value = cache_manager.get("nonexistent")
        assert value is None
        assert cache_manager._hits == 1
        assert cache_manager._misses == 1

    def test_cache_eviction(self, cache_manager):
        """Test LRU cache eviction policy."""
        # Fill cache to max size
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")
        
        # Add one more item, should evict oldest
        cache_manager.set("key4", "value4")
        
        # Check eviction
        assert cache_manager.get("key1") is None  # Should be evicted
        assert cache_manager.get("key2") == "value2"
        assert cache_manager.get("key3") == "value3"
        assert cache_manager.get("key4") == "value4"

    def test_cache_metrics(self, cache_manager):
        """Test cache metrics collection."""
        # Perform some operations
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")  # Hit
        cache_manager.get("nonexistent")  # Miss
        
        metrics = cache_manager.metrics
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["size"] == 1
        assert metrics["max_size"] == 3

    def test_cache_error_handling(self, cache_manager):
        """Test cache error handling."""
        with patch.dict(cache_manager._cache, {}, clear=True):
            # Force an error by making _cache non-subscriptable
            cache_manager._cache = None
            
            # Should handle error gracefully
            assert cache_manager.set("key", "value") is False
            assert cache_manager.get("key") is None

class TestPerformanceTracker:
    """Test suite for PerformanceTracker class."""

    @pytest.mark.asyncio
    async def test_operation_tracking(self, performance_tracker):
        """Test operation performance tracking."""
        async with performance_tracker.track_operation("test_op"):
            await asyncio.sleep(0.1)  # Simulate work
            
        metrics = performance_tracker.metrics
        assert metrics.execution_time > 0
        assert metrics.error_count == 0

    @pytest.mark.asyncio
    async def test_error_tracking(self, performance_tracker):
        """Test error tracking in operations."""
        try:
            async with performance_tracker.track_operation("error_op"):
                raise ValueError("Test error")
        except ValueError:
            pass
            
        metrics = performance_tracker.metrics
        assert metrics.error_count == 0  # Error count only increments on metric recording errors

    def test_memory_tracking(self, performance_tracker):
        """Test memory usage tracking."""
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024  # 1 MB
            performance_tracker._track_memory_usage()
            
        assert performance_tracker.metrics.memory_usage == 1.0  # Should be 1 MB

    def test_metrics_initialization(self, performance_tracker):
        """Test metrics initialization."""
        metrics = performance_tracker.metrics
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.execution_time == 0.0
        assert metrics.memory_usage == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.error_count == 0

@pytest.mark.integration
class TestIntegration:
    """Integration tests for cache and performance tracking."""

    @pytest.mark.asyncio
    async def test_cache_with_performance_tracking(self, cache_manager, performance_tracker):
        """Test cache operations with performance tracking."""
        async with performance_tracker.track_operation("cache_ops"):
            cache_manager.set("key1", "value1")
            cache_manager.get("key1")
            cache_manager.get("nonexistent")
            
        cache_metrics = cache_manager.metrics
        perf_metrics = performance_tracker.metrics
        
        assert cache_metrics["hits"] == 1
        assert cache_metrics["misses"] == 1
        assert perf_metrics.execution_time > 0
        assert perf_metrics.error_count == 0

if __name__ == "__main__":
    pytest.main([__file__])
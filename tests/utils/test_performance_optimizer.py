"""Tests for Performance Optimization Engine v3.0"""

import asyncio
import pytest
import psutil
from unittest.mock import Mock, patch, AsyncMock
from src.utils.performance_optimizer import (
    SystemMetrics,
    AIQResourcePool,
    AdaptiveBatchProcessor,
    AIQTelemetry,
    AIQOptimizer,
    Parser
)

@pytest.fixture
def mock_system_metrics():
    with patch('psutil.cpu_percent', return_value=50.0), \
         patch('psutil.virtual_memory', return_value=Mock(percent=60.0)), \
         patch('psutil.disk_io_counters', return_value=(1000, 2000)), \
         patch('psutil.net_io_counters', return_value=(3000, 4000)):
        yield

@pytest.fixture
def resource_pool():
    def factory():
        return Parser()
    
    def cleanup(resource):
        pass
    
    return AIQResourcePool(factory=factory, cleanup=cleanup)

@pytest.mark.asyncio
async def test_resource_pool_acquire(resource_pool, mock_system_metrics):
    """Test resource acquisition and release"""
    async with resource_pool.acquire() as resource:
        assert isinstance(resource, Parser)
        # Pool should have one active resource
        assert len(resource_pool._pool) == 0
    
    # Resource should be returned to pool
    assert len(resource_pool._pool) == 1

@pytest.mark.asyncio
async def test_resource_pool_max_size(mock_system_metrics):
    """Test pool respects max size limit"""
    pool = AIQResourcePool(
        factory=lambda: Parser(),
        cleanup=lambda x: None,
        max_size=2
    )
    
    resources = []
    for _ in range(3):
        async with pool.acquire() as resource:
            resources.append(resource)
            
    assert len(pool._pool) <= 2

@pytest.fixture
def batch_processor():
    return AdaptiveBatchProcessor()

@pytest.mark.asyncio
async def test_batch_processor_basic(batch_processor):
    """Test basic batch processing functionality"""
    items = list(range(100))
    
    async def process_batch(batch):
        return [x * 2 for x in batch]
        
    results = await batch_processor.process(items, process_batch)
    assert len(results) == 100
    assert results[0] == 0
    assert results[-1] == 198

@pytest.mark.asyncio
async def test_batch_processor_adaptive_sizing(batch_processor):
    """Test batch size adapts based on performance"""
    items = list(range(1000))
    initial_size = batch_processor.batch_size
    
    async def slow_processor(batch):
        await asyncio.sleep(0.1)  # Simulate slow processing
        return batch
        
    results = await batch_processor.process(items, slow_processor)
    
    assert len(results) == 1000
    assert batch_processor.batch_size != initial_size

@pytest.fixture
def telemetry():
    return AIQTelemetry()

@pytest.mark.asyncio
async def test_telemetry_tracking(telemetry):
    """Test metric tracking and retrieval"""
    await telemetry.track('throughput', 100.0)
    await telemetry.track('latency', 0.5)
    await telemetry.track('error_rate', 0.01)
    
    stats = await telemetry.get_realtime_stats()
    assert 'throughput_1m' in stats
    assert 'latency_p95' in stats
    assert 'error_rate_1m' in stats

@pytest.fixture
async def optimizer():
    opt = AIQOptimizer()
    return opt

@pytest.mark.asyncio
async def test_optimizer_pipeline(optimizer):
    """Test end-to-end pipeline optimization"""
    async def data_generator():
        for i in range(3):
            yield [f"item_{j}" for j in range(10)]
            
    await optimizer.optimize_pipeline(data_generator())
    
    # Verify metrics were collected
    assert len(optimizer.telemetry.metrics['throughput']) > 0
    assert len(optimizer.telemetry.metrics['latency']) > 0

@pytest.mark.asyncio
async def test_system_under_pressure(resource_pool, mock_system_metrics):
    """Test backpressure when system is loaded"""
    with patch('psutil.cpu_percent', return_value=90.0):
        is_pressured = await resource_pool._system_under_pressure()
        assert is_pressured is True

@pytest.mark.asyncio
async def test_adaptive_batch_size_adjustment(batch_processor):
    """Test batch size adjusts based on performance metrics"""
    # Simulate successful processing history
    batch_processor._latency_history.extend([0.1] * 10)
    batch_processor._error_history.clear()
    
    original_size = batch_processor.batch_size
    batch_processor._adjust_parameters()
    
    assert batch_processor.batch_size > original_size

@pytest.mark.asyncio
async def test_error_handling(batch_processor):
    """Test error handling during batch processing"""
    items = list(range(50))
    
    async def failing_processor(batch):
        if len(batch) > 10:
            raise ValueError("Simulated failure")
        return batch
        
    results = await batch_processor.process(items, failing_processor)
    assert len(results) < 50  # Some items should fail

@pytest.mark.asyncio
async def test_telemetry_retention(telemetry):
    """Test metric retention and aggregation"""
    # Add test metrics
    for i in range(3700):  # More than maxlen
        await telemetry.track('throughput', float(i))
    
    assert len(telemetry.metrics['throughput']) == 3600  # Should respect maxlen

@pytest.mark.asyncio
async def test_parser_implementation():
    """Test the example Parser class"""
    parser = Parser()
    result = await parser.process(['test', 'data'])
    assert result == ['TEST', 'DATA']
    
    # Test cleanup
    parser.cleanup()  # Should not raise any errors
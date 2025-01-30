"""Tests for decorator utilities"""

import pytest
import asyncio
import time
from functools import partial
from unittest.mock import Mock, patch, AsyncMock
from src.utils.decorators import (
    timing_decorator,
    async_timing_decorator,
    log_exceptions,
    async_log_exceptions,
    circuit_breaker,
    redact_sensitive,
    retry_with_backoff
)

# Test data
SENSITIVE_DATA = {
    'password': 'secret123',
    'api_key': 'abc123xyz',
    'email': 'test@example.com'
}

@pytest.mark.asyncio
async def test_async_timing_decorator():
    """Test async timing decorator measures execution time"""
    @async_timing_decorator
    async def slow_async_function():
        await asyncio.sleep(0.1)
        return 'done'
        
    with patch('logging.info') as mock_log:
        result = await slow_async_function()
        assert result == 'done'
        mock_log.assert_called_once()
        log_msg = mock_log.call_args[0][0]
        assert 'slow_async_function took' in log_msg
        assert 'seconds' in log_msg

def test_timing_decorator():
    """Test sync timing decorator measures execution time"""
    @timing_decorator
    def slow_function():
        time.sleep(0.1)
        return 'done'
        
    with patch('logging.info') as mock_log:
        result = slow_function()
        assert result == 'done'
        mock_log.assert_called_once()
        log_msg = mock_log.call_args[0][0]
        assert 'slow_function took' in log_msg
        assert 'seconds' in log_msg

def test_log_exceptions():
    """Test exception logging for sync functions"""
    @log_exceptions
    def failing_function():
        raise ValueError("Test error")
        
    with patch('logging.error') as mock_log:
        with pytest.raises(ValueError):
            failing_function()
        mock_log.assert_called_once()
        assert 'Test error' in mock_log.call_args[0][0]

@pytest.mark.asyncio
async def test_async_log_exceptions():
    """Test exception logging for async functions"""
    @async_log_exceptions
    async def failing_async_function():
        raise ValueError("Test async error")
        
    with patch('logging.error') as mock_log:
        with pytest.raises(ValueError):
            await failing_async_function()
        mock_log.assert_called_once()
        assert 'Test async error' in mock_log.call_args[0][0]

@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker pattern"""
    success_count = 0
    failure_count = 0
    
    @circuit_breaker(failure_threshold=3, reset_timeout=1)
    async def unstable_function():
        nonlocal success_count, failure_count
        if failure_count < 3:
            failure_count += 1
            raise ValueError("Simulated failure")
        success_count += 1
        return "success"
    
    # Test failures open circuit
    for _ in range(3):
        with pytest.raises(ValueError):
            await unstable_function()
            
    # Circuit should be open now
    with pytest.raises(Exception) as exc_info:
        await unstable_function()
    assert "Circuit breaker open" in str(exc_info.value)
    
    # Wait for reset
    await asyncio.sleep(1.1)
    
    # Should work now
    result = await unstable_function()
    assert result == "success"
    assert success_count == 1

def test_redact_sensitive():
    """Test sensitive data redaction"""
    @redact_sensitive(['password', 'api_key'])
    def process_data(data):
        return data
        
    input_data = SENSITIVE_DATA.copy()
    result = process_data(input_data)
    
    assert result['password'] == '***'
    assert result['api_key'] == '***'
    assert result['email'] == SENSITIVE_DATA['email']

@pytest.mark.asyncio
async def test_retry_with_backoff():
    """Test retry with exponential backoff"""
    attempt_count = 0
    
    @retry_with_backoff(max_retries=3, base_delay=0.1)
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    start_time = time.time()
    result = await failing_function()
    duration = time.time() - start_time
    
    assert result == "success"
    assert attempt_count == 3
    assert duration >= 0.3  # Should have waited at least base_delay * (2^1 + 2^2)

@pytest.mark.asyncio
async def test_circuit_breaker_half_open():
    """Test circuit breaker half-open state"""
    failure_count = 0
    
    @circuit_breaker(failure_threshold=2, reset_timeout=0.1)
    async def unstable_function():
        nonlocal failure_count
        if failure_count < 2:
            failure_count += 1
            raise ValueError("Initial failures")
        return "success"
    
    # Fail twice to open circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            await unstable_function()
    
    # Circuit should be open
    with pytest.raises(Exception) as exc_info:
        await unstable_function()
    assert "Circuit breaker open" in str(exc_info.value)
    
    # Wait for half-open state
    await asyncio.sleep(0.2)
    
    # Should succeed now
    result = await unstable_function()
    assert result == "success"

def test_redact_sensitive_nested():
    """Test redaction of nested sensitive data"""
    @redact_sensitive(['password', 'secret'])
    def process_nested(data):
        return data
        
    input_data = {
        'user': {
            'password': '12345',
            'profile': {
                'secret': 'hidden'
            }
        }
    }
    
    result = process_nested(input_data)
    assert result['user']['password'] == '***'
    assert result['user']['profile']['secret'] == '***'

@pytest.mark.asyncio
async def test_retry_max_attempts():
    """Test retry exhaustion"""
    attempt_count = 0
    
    @retry_with_backoff(max_retries=3, base_delay=0.1)
    async def always_fails():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("Persistent failure")
    
    with pytest.raises(ValueError) as exc_info:
        await always_fails()
        
    assert attempt_count == 4  # Initial + 3 retries
    assert "Persistent failure" in str(exc_info.value)
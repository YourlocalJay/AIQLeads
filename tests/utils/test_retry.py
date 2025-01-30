"""Tests for retry utility with enhanced configuration and features"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.utils.retry import (
    RetryStrategy,
    AsyncRetryStrategy,
    retry_with_backoff,
    async_retry_with_backoff,
    ExponentialBackoff,
    FixedBackoff,
    JitterBackoff
)

class TestException(Exception):
    """Custom exception for testing"""
    pass

@pytest.fixture
def mock_strategy():
    return RetryStrategy(
        max_retries=3,
        backoff=ExponentialBackoff(base_delay=0.1),
        exceptions=(TestException,)
    )

@pytest.fixture
def mock_async_strategy():
    return AsyncRetryStrategy(
        max_retries=3,
        backoff=ExponentialBackoff(base_delay=0.1),
        exceptions=(TestException,)
    )

def test_exponential_backoff():
    """Test exponential backoff delay calculation"""
    backoff = ExponentialBackoff(base_delay=0.1, max_delay=1.0)
    delays = [backoff.get_delay(attempt) for attempt in range(5)]
    
    assert delays[0] == 0.1
    assert delays[1] == 0.2
    assert delays[2] == 0.4
    assert delays[3] == 0.8
    assert delays[4] == 1.0  # Should cap at max_delay

def test_fixed_backoff():
    """Test fixed backoff delay"""
    backoff = FixedBackoff(delay=0.5)
    delays = [backoff.get_delay(attempt) for attempt in range(3)]
    assert all(delay == 0.5 for delay in delays)

def test_jitter_backoff():
    """Test jitter backoff provides varied delays"""
    backoff = JitterBackoff(base_delay=0.1, factor=0.5)
    delays = [backoff.get_delay(1) for _ in range(10)]
    assert all(0.05 <= delay <= 0.15 for delay in delays)
    assert len(set(delays)) > 1  # Should get different values

@pytest.mark.asyncio
async def test_async_retry_success():
    """Test successful async retry after failures"""
    attempts = 0

    @async_retry_with_backoff(max_retries=3, base_delay=0.1)
    async def flaky_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TestException(f"Attempt {attempts} failed")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert attempts == 3

def test_sync_retry_with_context():
    """Test retry with context data"""
    context = {"attempts": 0}

    @retry_with_backoff(max_retries=2, base_delay=0.1)
    def context_aware_function():
        context["attempts"] += 1
        if context["attempts"] < 3:
            raise TestException("Still failing")
        return "success"

    result = context_aware_function()
    assert result == "success"
    assert context["attempts"] == 3

@pytest.mark.asyncio
async def test_retry_timeout():
    """Test retry with timeout"""
    start_time = asyncio.get_event_loop().time()

    with pytest.raises(TestException):
        @async_retry_with_backoff(max_retries=2, base_delay=0.1)
        async def slow_function():
            await asyncio.sleep(0.2)
            raise TestException("Timeout test")
        await slow_function()

    duration = asyncio.get_event_loop().time() - start_time
    assert duration >= 0.6  # Base delays + execution time

def test_different_exceptions():
    """Test handling different exception types"""
    attempts = []

    @retry_with_backoff(
        max_retries=2,
        base_delay=0.1,
        exceptions=(ValueError, RuntimeError)
    )
    def mixed_errors():
        attempt = len(attempts)
        attempts.append(attempt)
        if attempt == 0:
            raise ValueError("First error")
        if attempt == 1:
            raise RuntimeError("Second error")
        return "success"

    result = mixed_errors()
    assert result == "success"
    assert len(attempts) == 3

@pytest.mark.asyncio
async def test_concurrent_retries():
    """Test concurrent retry operations"""
    results = []

    @async_retry_with_backoff(max_retries=2, base_delay=0.1)
    async def concurrent_operation(id):
        if len(results) < 2:
            results.append(id)
            raise TestException(f"Failure {id}")
        return f"success {id}"

    tasks = [
        asyncio.create_task(concurrent_operation(i))
        for i in range(3)
    ]
    
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    successful = [r for r in completed if isinstance(r, str)]
    assert len(successful) > 0

def test_retry_logging(caplog):
    """Test retry logging functionality"""
    @retry_with_backoff(max_retries=1, base_delay=0.1)
    def logged_function():
        raise TestException("Test log")

    with pytest.raises(TestException):
        logged_function()

    log_messages = [r.message for r in caplog.records]
    assert any("retry attempt" in msg.lower() for msg in log_messages)

@pytest.mark.asyncio
async def test_retry_cleanup():
    """Test cleanup function execution"""
    cleanup_calls = []

    async def cleanup():
        cleanup_calls.append(True)

    @async_retry_with_backoff(
        max_retries=1,
        base_delay=0.1,
        cleanup_func=cleanup
    )
    async def failing_function():
        raise TestException("Test cleanup")

    with pytest.raises(TestException):
        await failing_function()

    assert len(cleanup_calls) == 2  # Initial attempt + 1 retry
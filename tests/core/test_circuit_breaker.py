"""
Unit tests for circuit breaker implementation.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
    CircuitOpenError,
    circuit_protected
)

@pytest.fixture
def circuit_breaker():
    """Fixture providing a clean CircuitBreaker instance."""
    return CircuitBreaker(
        name="test_circuit",
        failure_threshold=3,
        recovery_timeout=1.0,
        half_open_timeout=0.5,
        reset_timeout=5.0
    )

@pytest.fixture
def registry():
    """Fixture providing a clean CircuitBreakerRegistry instance."""
    return CircuitBreakerRegistry()

class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    @pytest.mark.asyncio
    async def test_initial_state(self, circuit_breaker):
        """Test circuit breaker initialization."""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.stats.failure_count == 0
        assert circuit_breaker.stats.success_count == 0
        assert isinstance(circuit_breaker._lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_successful_execution(self, circuit_breaker):
        """Test successful function execution."""
        async def success_func():
            return "success"

        result = await circuit_breaker.execute(success_func)
        assert result == "success"
        assert circuit_breaker.stats.success_count == 1
        assert circuit_breaker.stats.failure_count == 0
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_sync_function_execution(self, circuit_breaker):
        """Test execution of synchronous functions."""
        def sync_func():
            return "sync success"

        result = await circuit_breaker.execute(sync_func)
        assert result == "sync success"
        assert circuit_breaker.stats.success_count == 1

    @pytest.mark.asyncio
    async def test_circuit_opening(self, circuit_breaker):
        """Test circuit opens after threshold failures."""
        async def fail_func():
            raise ValueError("test error")

        # Generate failures up to threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(fail_func)

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.stats.consecutive_failures == 3
        
        # Verify circuit blocks execution when open
        with pytest.raises(CircuitOpenError):
            await circuit_breaker.execute(fail_func)

    @pytest.mark.asyncio
    async def test_circuit_recovery(self, circuit_breaker):
        """Test circuit recovery process."""
        async def fail_func():
            raise ValueError("test error")
            
        async def success_func():
            return "success"

        # Force circuit open
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(fail_func)

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should be half-open and accept new requests
        result = await circuit_breaker.execute(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Wait for half-open timeout
        await asyncio.sleep(0.6)
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure(self, circuit_breaker):
        """Test circuit behavior when failing in half-open state."""
        async def fail_func():
            raise ValueError("test error")

        # Force circuit open
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(fail_func)

        # Wait for recovery
        await asyncio.sleep(1.1)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Fail in half-open state
        with pytest.raises(ValueError):
            await circuit_breaker.execute(fail_func)

        # Should return to open state
        await asyncio.sleep(0.6)
        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_failure_count_reset(self, circuit_breaker):
        """Test failure count reset after timeout."""
        async def fail_func():
            raise ValueError("test error")

        # Single failure
        with pytest.raises(ValueError):
            await circuit_breaker.execute(fail_func)

        # Wait for reset timeout
        await asyncio.sleep(5.1)

        # Another failure should start count from 1
        with pytest.raises(ValueError):
            await circuit_breaker.execute(fail_func)

        assert circuit_breaker.stats.consecutive_failures == 1
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_state_transitions_with_load(self, circuit_breaker):
        """Test circuit behavior under load."""
        async def fail_func():
            await asyncio.sleep(0.1)  # Simulate work
            raise ValueError("test error")

        async def success_func():
            await asyncio.sleep(0.1)  # Simulate work
            return "success"

        # Create multiple concurrent operations
        tasks = []
        for _ in range(5):
            tasks.append(asyncio.create_task(circuit_breaker.execute(fail_func)))

        # Wait for all tasks to complete
        with pytest.raises(ValueError):
            await asyncio.gather(*tasks)

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.stats.consecutive_failures >= 3

class TestCircuitBreakerRegistry:
    """Test suite for CircuitBreakerRegistry class."""

    @pytest.mark.asyncio
    async def test_circuit_creation(self, registry):
        """Test circuit creation and retrieval."""
        circuit1 = await registry.get_circuit("test1")
        circuit2 = await registry.get_circuit("test2")
        
        assert len(registry.circuits) == 2
        assert "test1" in registry.circuits
        assert "test2" in registry.circuits
        
        # Should get same instance
        circuit1_again = await registry.get_circuit("test1")
        assert circuit1 is circuit1_again

    @pytest.mark.asyncio
    async def test_registry_reset(self, registry):
        """Test resetting all circuits in registry."""
        circuit1 = await registry.get_circuit("test1")
        circuit2 = await registry.get_circuit("test2")
        
        async def fail_func():
            raise ValueError("test error")

        # Force failures
        for circuit in [circuit1, circuit2]:
            with pytest.raises(ValueError):
                await circuit.execute(fail_func)

        await registry.reset_all()
        
        for circuit in registry.circuits.values():
            assert circuit.state == CircuitState.CLOSED
            assert circuit.stats.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_configuration(self, registry):
        """Test circuit creation with custom configuration."""
        circuit = await registry.get_circuit(
            "custom_circuit",
            failure_threshold=5,
            recovery_timeout=30.0
        )
        
        assert circuit.failure_threshold == 5
        assert circuit.recovery_timeout == 30.0

class TestCircuitBreakerDecorator:
    """Test suite for circuit_protected decorator."""

    @pytest.mark.asyncio
    async def test_decorator_basic(self):
        """Test basic decorator functionality."""
        @circuit_protected("test_decorator", failure_threshold=2)
        async def test_func(should_fail: bool = False):
            if should_fail:
                raise ValueError("test error")
            return "success"

        # Test successful execution
        result = await test_func(should_fail=False)
        assert result == "success"

        # Test circuit opening
        with pytest.raises(ValueError):
            await test_func(should_fail=True)
        with pytest.raises(ValueError):
            await test_func(should_fail=True)

        # Circuit should be open now
        with pytest.raises(CircuitOpenError):
            await test_func(should_fail=False)

    @pytest.mark.asyncio
    async def test_decorator_sync_function(self):
        """Test decorator with synchronous function."""
        @circuit_protected("sync_decorator")
        def sync_func():
            return "sync success"

        result = await sync_func()
        assert result == "sync success"

    @pytest.mark.asyncio
    async def test_decorator_configuration(self):
        """Test decorator with custom configuration."""
        @circuit_protected(
            "custom_decorator",
            failure_threshold=5,
            recovery_timeout=30.0
        )
        async def test_func():
            return "success"

        circuit = registry.circuits.get("custom_decorator")
        assert circuit.failure_threshold == 5
        assert circuit.recovery_timeout == 30.0

if __name__ == "__main__":
    pytest.main([__file__])
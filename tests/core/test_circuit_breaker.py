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

    @pytest.mark.asyncio
    async def test_successful_execution(self, circuit_breaker):
        """Test successful function execution."""
        async def success_func():
            return "success"

        result = await circuit_breaker.execute(success_func)
        assert result == "success"
        assert circuit_breaker.stats.success_count == 1
        assert circuit_breaker.stats.failure_count == 0

    @pytest.mark.asyncio
    async def test_failed_execution(self, circuit_breaker):
        """Test failed function execution."""
        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await circuit_breaker.execute(fail_func)
        
        assert circuit_breaker.stats.failure_count == 1
        assert circuit_breaker.stats.success_count == 0

    @pytest.mark.asyncio
    async def test_circuit_opening(self, circuit_breaker):
        """Test circuit opens after threshold failures."""
        async def fail_func():
            raise ValueError("test error")

        for _ in range(3):  # Failure threshold
            with pytest.raises(ValueError):
                await circuit_breaker.execute(fail_func)

        assert circuit_breaker.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            await circuit_breaker.execute(fail_func)

    @pytest.mark.asyncio
    async def test_circuit_recovery(self, circuit_breaker):
        """Test circuit recovery after timeout."""
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
        
        # Should be half-open now
        result = await circuit_breaker.execute(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Wait for half-open timeout
        await asyncio.sleep(0.6)
        
        # Should be closed after successful execution
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reset_functionality(self, circuit_breaker):
        """Test circuit breaker reset."""
        async def fail_func():
            raise ValueError("test error")

        # Force some failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(fail_func)

        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.stats.failure_count == 0
        assert circuit_breaker.stats.success_count == 0

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

        # Force some failures
        with pytest.raises(ValueError):
            await circuit1.execute(fail_func)
        with pytest.raises(ValueError):
            await circuit2.execute(fail_func)

        await registry.reset_all()
        
        for circuit in registry.circuits.values():
            assert circuit.state == CircuitState.CLOSED
            assert circuit.stats.failure_count == 0

class TestCircuitBreakerDecorator:
    """Test suite for circuit_protected decorator."""

    @pytest.mark.asyncio
    async def test_decorator_functionality(self):
        """Test circuit breaker decorator."""
        success_count = 0
        failure_count = 0

        @circuit_protected("test_decorator", failure_threshold=2)
        async def test_func(should_fail: bool = False):
            nonlocal success_count, failure_count
            if should_fail:
                failure_count += 1
                raise ValueError("test error")
            success_count += 1
            return "success"

        # Test successful execution
        result = await test_func(should_fail=False)
        assert result == "success"
        assert success_count == 1

        # Test circuit opening
        with pytest.raises(ValueError):
            await test_func(should_fail=True)
        with pytest.raises(ValueError):
            await test_func(should_fail=True)
            
        # Circuit should be open now
        with pytest.raises(CircuitOpenError):
            await test_func(should_fail=False)

        assert failure_count == 2

if __name__ == "__main__":
    pytest.main([__file__])
"""
Circuit breaker implementation for AIQLeads.
Provides fault tolerance and system resilience patterns.
"""
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar
from dataclasses import dataclass
import time
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = 'closed'      # Normal operation
    OPEN = 'open'         # Failing state
    HALF_OPEN = 'half_open'  # Testing recovery

@dataclass
class CircuitStats:
    """Statistics for circuit breaker monitoring."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    consecutive_failures: int = 0
    total_requests: int = 0

class CircuitBreaker:
    """
    Circuit breaker implementation for protecting system resources.
    
    Attributes:
        name: Identifier for the circuit
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        half_open_timeout: Seconds to wait in half-open state
        reset_timeout: Seconds after which to reset failure count
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_timeout: float = 30.0,
        reset_timeout: float = 600.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.reset_timeout = reset_timeout
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = time.time()
        self._lock = asyncio.Lock()
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                await self._handle_success()
                return result
                
            except Exception as e:
                await self._handle_failure(e)
                raise
    
    async def _check_state_transition(self):
        """Check and update circuit state based on conditions."""
        current_time = time.time()
        
        if self._state == CircuitState.OPEN:
            if current_time - self._last_state_change >= self.recovery_timeout:
                logger.info(f"Circuit {self.name} transitioning from OPEN to HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = current_time
                
        elif self._state == CircuitState.HALF_OPEN:
            if current_time - self._last_state_change >= self.half_open_timeout:
                if self._stats.consecutive_failures == 0:
                    logger.info(f"Circuit {self.name} transitioning from HALF_OPEN to CLOSED")
                    self._state = CircuitState.CLOSED
                else:
                    logger.warning(f"Circuit {self.name} transitioning back to OPEN due to failures")
                    self._state = CircuitState.OPEN
                self._last_state_change = current_time
    
    async def _handle_success(self):
        """Update stats after successful execution."""
        self._stats.success_count += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_time = time.time()
        self._stats.total_requests += 1
        
        if self._state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit {self.name} success in HALF_OPEN state")
    
    async def _handle_failure(self, error: Exception):
        """Update stats and potentially open circuit after failure."""
        current_time = time.time()
        self._stats.failure_count += 1
        self._stats.consecutive_failures += 1
        self._stats.last_failure_time = current_time
        self._stats.total_requests += 1
        
        # Reset failure count if enough time has passed
        if current_time - self._stats.last_failure_time > self.reset_timeout:
            self._stats.consecutive_failures = 1
        
        if (self._state == CircuitState.CLOSED and 
            self._stats.consecutive_failures >= self.failure_threshold):
            logger.warning(
                f"Circuit {self.name} opening due to {self._stats.consecutive_failures} "
                f"consecutive failures. Last error: {str(error)}"
            )
            self._state = CircuitState.OPEN
            self._last_state_change = current_time
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state
    
    @property
    def stats(self) -> CircuitStats:
        """Current circuit statistics."""
        return self._stats
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = time.time()

class CircuitOpenError(Exception):
    """Raised when attempting to execute while circuit is open."""
    pass

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_circuit(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_timeout: float = 30.0,
        reset_timeout: float = 600.0
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        async with self._lock:
            if name not in self._circuits:
                self._circuits[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    half_open_timeout=half_open_timeout,
                    reset_timeout=reset_timeout
                )
            return self._circuits[name]
    
    async def reset_all(self):
        """Reset all circuit breakers."""
        async with self._lock:
            for circuit in self._circuits.values():
                circuit.reset()
    
    @property
    def circuits(self) -> Dict[str, CircuitBreaker]:
        """All registered circuit breakers."""
        return self._circuits.copy()

# Global registry instance
registry = CircuitBreakerRegistry()

def circuit_protected(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    half_open_timeout: float = 30.0,
    reset_timeout: float = 600.0
):
    """Decorator for applying circuit breaker protection to functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            circuit = await registry.get_circuit(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                half_open_timeout=half_open_timeout,
                reset_timeout=reset_timeout
            )
            return await circuit.execute(func, *args, **kwargs)
        return wrapper
    return decorator
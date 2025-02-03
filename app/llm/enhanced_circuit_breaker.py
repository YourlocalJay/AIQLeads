import asyncio
import time
import logging
from typing import Any, Callable, Dict, Optional, TypeVar
from enum import Enum
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitStats:
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_success_time: float = 0.0
    last_failure_time: float = 0.0
    total_requests: int = 0

class CircuitOpenError(Exception):
    pass

class CircuitBreaker:
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
        async with self._lock:
            await self._check_state_transition()

            if self._state == CircuitState.OPEN:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")

            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                await self._handle_success()
                return result
            except Exception as e:
                await self._handle_failure(e)
                raise

    async def _check_state_transition(self):
        current_time = time.time()
        
        if self._state == CircuitState.OPEN and current_time - self._last_state_change >= self.recovery_timeout:
            logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
            self._state = CircuitState.HALF_OPEN
            self._last_state_change = current_time

        elif self._state == CircuitState.HALF_OPEN and current_time - self._last_state_change >= self.half_open_timeout:
            if self._stats.consecutive_failures == 0:
                logger.info(f"Circuit {self.name} transitioning to CLOSED")
                self._state = CircuitState.CLOSED
            else:
                logger.warning(f"Circuit {self.name} transitioning back to OPEN")
                self._state = CircuitState.OPEN
            self._last_state_change = current_time

    async def _handle_success(self):
        self._stats.success_count += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_time = time.time()
        self._stats.total_requests += 1
        if self._state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit {self.name} recovering, returning to CLOSED")
            self._state = CircuitState.CLOSED

    async def _handle_failure(self, error: Exception):
        current_time = time.time()
        self._stats.failure_count += 1
        self._stats.consecutive_failures += 1
        self._stats.last_failure_time = current_time
        self._stats.total_requests += 1

        if current_time - self._stats.last_failure_time > self.reset_timeout:
            self._stats.consecutive_failures = 1

        if self._state == CircuitState.CLOSED and self._stats.consecutive_failures >= self.failure_threshold:
            logger.warning(f"Circuit {self.name} opening due to {self._stats.consecutive_failures} consecutive failures.")
            self._state = CircuitState.OPEN
            self._last_state_change = current_time

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def stats(self) -> CircuitStats:
        return self._stats

    def reset(self):
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = time.time()

class CircuitBreakerRegistry:
    def __init__(self):
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_circuit(self, name: str, **kwargs) -> CircuitBreaker:
        async with self._lock:
            if name not in self._circuits:
                self._circuits[name] = CircuitBreaker(name=name, **kwargs)
            return self._circuits[name]

    async def reset_all(self):
        async with self._lock:
            for circuit in self._circuits.values():
                circuit.reset()

    @property
    def circuits(self) -> Dict[str, CircuitBreaker]:
        return self._circuits.copy()

registry = CircuitBreakerRegistry()

def circuit_protected(name: str, **kwargs):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            circuit = await registry.get_circuit(name, **kwargs)
            return await circuit.execute(func, *args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    import asyncio

    @circuit_protected(name="example_circuit", failure_threshold=3)
    async def example_function(x: int, y: int) -> int:
        if x == y:
            raise ValueError("x and y cannot be equal")
        return x + y

    async def main():
        try:
            result = await example_function(1, 2)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

        try:
            result = await example_function(1, 1)
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(main())

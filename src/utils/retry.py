import asyncio
import logging
import functools
from typing import TypeVar, Callable, Any, Optional, Type, Union, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryError(Exception):
    """Custom exception for retry failures"""
    def __init__(
        self,
        message: str,
        last_error: Optional[Exception] = None,
        attempts: int = 0
    ):
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts

async def with_retry(
    func: Callable[..., Any],
    max_attempts: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 2.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for the delay after each retry
        exceptions: Exception or tuple of exceptions to catch and retry
        on_retry: Optional callback function called after each retry attempt
        
    Returns:
        Result from the function if successful
        
    Raises:
        RetryError: If max attempts are exceeded
    """
    attempt = 1
    delay = initial_delay
    last_error = None

    while attempt <= max_attempts:
        try:
            return await func()
        except exceptions as e:
            last_error = e
            
            if attempt == max_attempts:
                logger.error(
                    f"Max retry attempts ({max_attempts}) exceeded for {func.__name__}. "
                    f"Last error: {str(e)}"
                )
                raise RetryError(
                    f"Failed after {attempt} attempts",
                    last_error=e,
                    attempts=attempt
                )
            
            if on_retry:
                on_retry(e, attempt)
            
            logger.warning(
                f"Retry attempt {attempt}/{max_attempts} for {func.__name__} "
                f"failed: {str(e)}. Retrying in {delay:.2f}s"
            )
            
            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)
            attempt += 1

def with_retry_decorator(
    max_attempts: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 2.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator for adding retry logic to async functions.
    
    Args:
        Same as with_retry function
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async def retry_func() -> Any:
                return await func(*args, **kwargs)
            
            return await with_retry(
                retry_func,
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                exceptions=exceptions,
                on_retry=on_retry
            )
        return wrapper
    return decorator

class CircuitBreaker:
    """
    Circuit breaker implementation to prevent repeated calls to failing services.
    """
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_timeout: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, or half-open

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failures} failures")

    def record_success(self) -> None:
        """Record a success and reset the circuit breaker"""
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"
        logger.info("Circuit breaker reset after successful operation")

    def can_execute(self) -> bool:
        """Check if the operation can be executed"""
        if self.state == "closed":
            return True
            
        if self.state == "open" and self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed >= self.reset_timeout:
                self.state = "half-open"
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
            
        if self.state == "half-open":
            elapsed = (datetime.now() - self.last_failure_time).total_seconds() \
                if self.last_failure_time else 0
            return elapsed >= self.half_open_timeout
            
        return False

def with_circuit_breaker(
    circuit_breaker: CircuitBreaker,
    fallback: Optional[Callable[..., Any]] = None
) -> Callable:
    """
    Decorator for adding circuit breaker logic to async functions.
    
    Args:
        circuit_breaker: CircuitBreaker instance to use
        fallback: Optional fallback function to call when circuit is open
        
    Returns:
        Decorated function with circuit breaker logic
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not circuit_breaker.can_execute():
                if fallback:
                    return await fallback(*args, **kwargs)
                raise Exception("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
                
        return wrapper
    return decorator
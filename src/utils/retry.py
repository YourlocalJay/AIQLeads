import os
import logging
import functools
import random
import asyncio
from typing import Any, Callable, Optional, Union, Type, Tuple

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Custom exception for retry failures"""
    pass

class RetryDecorator:
    """Enhanced retry logic with dynamic configuration and metrics."""
    
    def __init__(
        self,
        max_attempts: Optional[int] = None,
        initial_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        on_retry: Optional[Callable[[Exception, int], None]] = None
    ):
        """
        Initialize retry configuration.
        
        :param max_attempts: Maximum number of retry attempts
        :param initial_delay: Initial delay between retries
        :param max_delay: Maximum delay between retries
        :param backoff_factor: Multiplier for increasing delay between retries
        :param exceptions: Exception or tuple of exceptions to retry on
        :param on_retry: Optional callback function to execute on each retry
        """
        self.max_attempts = max_attempts or int(os.getenv("RETRY_MAX_ATTEMPTS", 3))
        self.initial_delay = initial_delay or float(os.getenv("RETRY_INITIAL_DELAY", 0.1))
        self.max_delay = max_delay or float(os.getenv("RETRY_MAX_DELAY", 2.0))
        self.backoff_factor = backoff_factor or float(os.getenv("RETRY_BACKOFF_FACTOR", 2.0))
        self.exceptions = exceptions
        self.on_retry = on_retry

    async def with_retry(self, func: Callable[..., Any]) -> Any:
        """
        Execute function with retry logic.
        
        :param func: Async function to execute with retry mechanism
        :return: Result of the function
        :raises RetryError: If max retry attempts are exceeded
        """
        attempt = 1
        delay = self.initial_delay
        
        while True:
            try:
                return await func()
            except self.exceptions as e:
                if attempt >= self.max_attempts:
                    logger.error(f"Max retry attempts ({self.max_attempts}) exceeded")
                    raise RetryError(f"Max retries exceeded after {attempt} attempts") from e
                
                if self.on_retry:
                    await self.on_retry(e, attempt)
                    
                logger.warning(
                    f"Retry attempt {attempt}/{self.max_attempts} after error: {str(e)}",
                    exc_info=True
                )
                
                await self._sleep_with_backoff(delay, attempt)
                delay = min(delay * self.backoff_factor, self.max_delay)
                attempt += 1

    async def _sleep_with_backoff(self, delay: float, attempt: int) -> None:
        """
        Non-blocking sleep with exponential backoff and jitter.
        
        :param delay: Base delay time
        :param attempt: Current retry attempt number
        """
        jitter = delay * 0.1
        sleep_time = min(delay + (random.uniform(-jitter, jitter)), self.max_delay)
        logger.debug(f"Retry attempt {attempt} sleeping {sleep_time:.2f}s")
        await asyncio.sleep(sleep_time)

def with_retry_decorator(**kwargs) -> Callable:
    """
    Decorator factory for retry logic.
    
    :param kwargs: Configuration parameters for RetryDecorator
    :return: Retry decorator
    """
    retry = RetryDecorator(**kwargs)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await retry.with_retry(lambda: func(*args, **kwargs))
        return wrapper
    return decorator

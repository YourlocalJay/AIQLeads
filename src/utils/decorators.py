import time
import logging
import functools
from typing import Any, Callable
from fastapi import Request

logger = logging.getLogger(__name__)

def async_timed():
    """
    Decorator for timing async functions and logging their execution time.
    Also stores the execution time in request.state if a request object is available.
    """
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            # Find request object if it exists
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for arg in kwargs.values():
                    if isinstance(arg, Request):
                        request = arg
                        break

            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                total_time = time.time() - start
                
                # Log execution time
                logger.debug(
                    f"{func.__module__}.{func.__name__} took {total_time:.2f}s"
                )
                
                # Store in request state if available
                if request:
                    request.state.process_time = total_time
                
                # Log warning for slow operations
                if total_time > 1.0:  # 1 second threshold
                    logger.warning(
                        f"Slow operation detected: {func.__module__}.{func.__name__} "
                        f"took {total_time:.2f}s"
                    )
        
        return wrapped
    return wrapper
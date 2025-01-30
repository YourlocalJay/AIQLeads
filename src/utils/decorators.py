import time
import logging
import functools
import os
import random
from typing import Any, Callable, Optional, Union, Dict
from fastapi import Request

logger = logging.getLogger(__name__)

def async_timed(
    threshold: float = None,
    redact_keys: Optional[set] = None,
    request_param_name: Optional[str] = "request"
):
    """
    Enhanced decorator for timing async functions with FastAPI integration.
    
    Features:
    - Configurable request parameter name detection
    - Sensitive data redaction (recursive)
    - Multiple timing storage in request.state
    - Configurable threshold from environment variables
    
    :param threshold: Execution time threshold for warnings (defaults to ENV: ASYNC_TIMED_THRESHOLD or 1.0)
    :param redact_keys: Set of parameter names to redact from logs
    :param request_param_name: Name of the Request parameter in decorated functions
    """
    threshold = threshold or float(os.getenv("ASYNC_TIMED_THRESHOLD", 1.0))
    
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            request = _find_request(args, kwargs, request_param_name)
            safe_args = _sanitize_args(args, redact_keys or set())
            safe_kwargs = _sanitize_kwargs(kwargs, redact_keys or set())
            
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error during {func.__name__} execution: {str(e)}")
                raise
            finally:
                total_time = time.perf_counter() - start
                _store_timing(request, func.__name__, total_time)
                _log_execution(func, total_time, safe_args, safe_kwargs, threshold)
        
        return wrapped
    return wrapper

def _find_request(args: tuple, kwargs: dict, param_name: str) -> Optional[Request]:
    """Find Request object in function parameters."""
    return kwargs.get(param_name) if isinstance(kwargs.get(param_name), Request) else \
           next((arg for arg in args if isinstance(arg, Request)), None)

def _recursive_redact(data: Any, redact: set) -> Any:
    """Recursively redact sensitive data in dictionaries and lists."""
    if isinstance(data, dict):
        return {k: _recursive_redact(v, redact) if k not in redact else f"<REDACTED {type(v).__name__}>" for k, v in data.items()}
    elif isinstance(data, list):
        return [_recursive_redact(item, redact) for item in data]
    return data

def _sanitize_args(args: tuple, redact: set) -> tuple:
    """Sanitize positional arguments recursively."""
    return tuple(_recursive_redact(arg, redact) for arg in args)

def _sanitize_kwargs(kwargs: dict, redact: set) -> dict:
    """Sanitize keyword arguments recursively."""
    return {k: _recursive_redact(v, redact) for k, v in kwargs.items()}

def _store_timing(request: Optional[Request], func_name: str, timing: float) -> None:
    """Store timing data in request state safely."""
    if request:
        if not hasattr(request.state, "timings") or not isinstance(request.state.timings, dict):
            request.state.timings = {}
        request.state.timings[func_name] = timing

def _log_execution(func: Callable, total_time: float, args: tuple, kwargs: dict, threshold: float) -> None:
    """Handle logging with different verbosity levels."""
    log_data = {
        "module": func.__module__,
        "function": func.__name__,
        "duration": f"{total_time:.2f}s",
        "args": args,
        "kwargs": kwargs
    }
    logger.debug(f"Execution metrics: {log_data}")
    
    if total_time > threshold:
        logger.warning(
            f"Slow operation: {func.__module__}.{func.__name__} "
            f"took {total_time:.2f}s (Threshold: {threshold}s)"
        )

def circuit_breaker(
    failure_threshold: int = 3, 
    reset_timeout: float = 30.0,
    fallback: Optional[Callable] = None
) -> Callable:
    """
    Circuit breaker decorator to prevent cascading failures.
    
    :param failure_threshold: Number of consecutive failures before breaking
    :param reset_timeout: Time to wait before attempting to reset
    :param fallback: Optional fallback function to call when circuit is open
    :return: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        failures = 0
        last_failure_time = 0
        state = 'closed'

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            nonlocal failures, last_failure_time, state
            current_time = time.time()

            # Check circuit state
            if state == 'open':
                if current_time - last_failure_time < reset_timeout:
                    logger.warning(f"Circuit breaker {func.__name__} is open")
                    return fallback(*args, **kwargs) if fallback else None
                state = 'half-open'

            try:
                result = await func(*args, **kwargs)
                
                # Reset on success
                if state == 'half-open':
                    state = 'closed'
                failures = 0
                
                return result
            
            except Exception as e:
                failures += 1
                
                if failures >= failure_threshold:
                    state = 'open'
                    last_failure_time = current_time
                    logger.warning(f"Circuit breaker activated for {func.__name__}: {failures} consecutive failures")
                
                raise

        return wrapper
    return decorator
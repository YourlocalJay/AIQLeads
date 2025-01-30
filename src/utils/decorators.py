import time
import logging
import functools
import os
from typing import Any, Callable, Optional, Dict
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
            request = find_request(args, kwargs, request_param_name)
            safe_args = sanitize_args(args, redact_keys or set())
            safe_kwargs = sanitize_kwargs(kwargs, redact_keys or set())
            
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error during {func.__name__} execution: {str(e)}")
                raise
            finally:
                total_time = time.perf_counter() - start
                store_timing(request, func.__name__, total_time)
                log_execution(func, total_time, safe_args, safe_kwargs, threshold)
        
        return wrapped
    return wrapper

def find_request(args: tuple, kwargs: dict, param_name: str) -> Optional[Request]:
    """Find Request object in function parameters."""
    return kwargs.get(param_name) if isinstance(kwargs.get(param_name), Request) else \
           next((arg for arg in args if isinstance(arg, Request)), None)

def recursive_redact(data: Any, redact: set) -> Any:
    """Recursively redact sensitive data in dictionaries and lists."""
    if isinstance(data, dict):
        return {k: recursive_redact(v, redact) if k not in redact else f"<REDACTED {type(v).__name__}>" for k, v in data.items()}
    elif isinstance(data, list):
        return [recursive_redact(item, redact) for item in data]
    return data

def sanitize_args(args: tuple, redact: set) -> tuple:
    """Sanitize positional arguments recursively."""
    return tuple(recursive_redact(arg, redact) for arg in args)

def sanitize_kwargs(kwargs: dict, redact: set) -> dict:
    """Sanitize keyword arguments recursively."""
    return {k: recursive_redact(v, redact) for k, v in kwargs.items()}

def store_timing(request: Optional[Request], func_name: str, timing: float) -> None:
    """Store timing data in request state safely."""
    if request:
        if not hasattr(request.state, "timings") or not isinstance(request.state.timings, dict):
            request.state.timings = {}
        request.state.timings[func_name] = timing

def log_execution(func: Callable, total_time: float, args: tuple, kwargs: dict, threshold: float) -> None:
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

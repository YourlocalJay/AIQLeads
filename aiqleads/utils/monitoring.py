"""
Monitoring utilities for AIQLeads
Handles performance monitoring and error tracking
"""

import time
import logging
import traceback
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._metrics: Dict[str, Dict[str, Any]] = {}
        
    def track_operation(self, operation_name: str) -> Callable:
        """Decorator to track operation performance"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    self._record_metric(operation_name, duration, success=True)
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    self._record_metric(operation_name, duration, success=False, error=str(e))
                    raise
            return wrapper
        return decorator
        
    def _record_metric(self, operation: str, duration: float, success: bool, error: Optional[str] = None) -> None:
        """Record performance metrics for an operation"""
        if operation not in self._metrics:
            self._metrics[operation] = {
                "count": 0,
                "total_duration": 0.0,
                "failures": 0,
                "last_error": None,
                "last_run": None
            }
            
        metrics = self._metrics[operation]
        metrics["count"] += 1
        metrics["total_duration"] += duration
        metrics["last_run"] = datetime.now().isoformat()
        
        if not success:
            metrics["failures"] += 1
            metrics["last_error"] = error
            
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for specified operation or all operations"""
        if operation:
            metrics = self._metrics.get(operation, {})
            if metrics:
                metrics = metrics.copy()
                metrics["avg_duration"] = (
                    metrics["total_duration"] / metrics["count"] 
                    if metrics["count"] > 0 else 0.0
                )
            return metrics
        return self._metrics

class ErrorTracker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._errors: Dict[str, Dict[str, Any]] = {}
        
    def track_errors(self, error_category: str) -> Callable:
        """Decorator to track and categorize errors"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self._record_error(error_category, e)
                    raise
            return wrapper
        return decorator
        
    def _record_error(self, category: str, error: Exception) -> None:
        """Record error details for tracking"""
        if category not in self._errors:
            self._errors[category] = {
                "count": 0,
                "last_occurrence": None,
                "error_types": {}
            }
            
        error_info = self._errors[category]
        error_type = type(error).__name__
        
        if error_type not in error_info["error_types"]:
            error_info["error_types"][error_type] = {
                "count": 0,
                "recent_errors": []
            }
            
        error_info["count"] += 1
        error_info["last_occurrence"] = datetime.now().isoformat()
        
        type_info = error_info["error_types"][error_type]
        type_info["count"] += 1
        
        error_details = {
            "message": str(error),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Keep last 5 errors of each type
        type_info["recent_errors"] = (
            type_info["recent_errors"][-4:] + [error_details]
        )
        
    def get_error_stats(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get error statistics for specified category or all categories"""
        if category:
            return self._errors.get(category, {})
        return self._errors

# Global instances for shared use
performance_monitor = PerformanceMonitor()
error_tracker = ErrorTracker()

from typing import Dict, Optional, Any
from functools import wraps
import time
from prometheus_client import Counter, Histogram, Info
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class SchemaMetrics:
    def __init__(self):
        # Core validation metrics
        self.validation_duration = Histogram(
            'schema_validation_duration_seconds',
            'Time spent on schema validation',
            ['endpoint', 'schema_version'],
            buckets=(0.001, 0.002, 0.005, 0.01, 0.025, 0.05, 0.1)  # Fine-grained buckets for <10ms target
        )
        
        self.validation_errors = Counter(
            'schema_validation_errors_total',
            'Total schema validation errors',
            ['endpoint', 'error_type', 'schema_version']
        )
        
        self.cache_operations = Counter(
            'schema_cache_operations_total',
            'Schema cache operations',
            ['operation', 'status']
        )
        
        # Schema version tracking
        self.schema_info = Info('schema_version_info', 'Schema version information')
        
        # Cache performance metrics
        self.cache_hit_ratio = Histogram(
            'schema_cache_hit_ratio',
            'Schema cache hit ratio',
            buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99)  # Focus on target >85%
        )

    @contextmanager
    def track_validation_time(self, endpoint: str, schema_version: str):
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.validation_duration.labels(endpoint=endpoint, schema_version=schema_version).observe(duration)
            
            if duration > 0.01:  # 10ms threshold
                logger.warning(f"Schema validation exceeded 10ms threshold: {duration:.4f}s for {endpoint}")

    def track_cache_operation(self, operation: str, hit: bool):
        status = 'hit' if hit else 'miss'
        self.cache_operations.labels(operation=operation, status=status).inc()
        
        if operation == 'get':
            current_hits = self.cache_operations.labels(operation='get', status='hit')._value.get()
            total_gets = (self.cache_operations.labels(operation='get', status='hit')._value.get() +
                         self.cache_operations.labels(operation='get', status='miss')._value.get())
            
            if total_gets > 0:
                hit_ratio = current_hits / total_gets
                self.cache_hit_ratio.observe(hit_ratio)
                
                if hit_ratio < 0.85:  # 85% threshold
                    logger.warning(f"Cache hit ratio below threshold: {hit_ratio:.2%}")

    def record_validation_error(self, endpoint: str, error_type: str, schema_version: str):
        self.validation_errors.labels(
            endpoint=endpoint,
            error_type=error_type,
            schema_version=schema_version
        ).inc()
        
        logger.error(f"Schema validation error: {error_type} for {endpoint} (version: {schema_version})")

def monitor_schema_validation(endpoint: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = SchemaMetrics()
            schema_version = kwargs.get('schema_version', 'default')
            
            try:
                with metrics.track_validation_time(endpoint, schema_version):
                    return await func(*args, **kwargs)
            except Exception as e:
                metrics.record_validation_error(endpoint, type(e).__name__, schema_version)
                raise
                
        return wrapper
    return decorator
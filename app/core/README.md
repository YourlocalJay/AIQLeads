# Core Module Documentation

This module provides core functionality for the AIQLeads project, including system optimizations, caching, and fault tolerance patterns.

## Components

### Circuit Breaker (`circuit_breaker.py`)

Implements the circuit breaker pattern for fault tolerance:

```python
from app.core.circuit_breaker import circuit_protected

# Basic usage with decorator
@circuit_protected("api_service")
async def call_api():
    return await make_request()

# Manual circuit creation
from app.core.circuit_breaker import CircuitBreaker

circuit = CircuitBreaker(
    name="database",
    failure_threshold=5,
    recovery_timeout=60.0
)
```

Configuration options:
- `failure_threshold`: Number of failures before opening circuit
- `recovery_timeout`: Seconds to wait before recovery attempt
- `half_open_timeout`: Time in half-open state
- `reset_timeout`: Time before resetting failure count

### Performance Tracking (`optimizations.py`)

Provides system-wide performance monitoring:

```python
from app.core.optimizations import performance_tracker

# Track operation performance
async with performance_tracker.track_operation("critical_task"):
    result = await process_data()

# Access metrics
metrics = performance_tracker.metrics
print(f"Memory usage: {metrics.memory_usage}MB")
```

### Enhanced Caching (`optimizations.py`)

Implements an LRU cache with performance metrics:

```python
from app.core.optimizations import cache_manager

# Basic operations
cache_manager.set("key", "value")
value = cache_manager.get("key")

# Monitor performance
metrics = cache_manager.metrics
print(f"Hit ratio: {metrics['hits']/(metrics['hits'] + metrics['misses'])}")
```

## Testing

Run tests with pytest:

```bash
pip install -r tests/requirements-test.txt
pytest tests/core/
```

## Best Practices

1. Circuit Breaker Usage:
   - Use for external service calls
   - Configure thresholds based on service SLAs
   - Monitor circuit states

2. Performance Tracking:
   - Track long-running operations
   - Monitor memory usage
   - Review metrics regularly

3. Caching:
   - Set appropriate cache sizes
   - Monitor hit/miss ratios
   - Handle eviction properly

## Integration Points

1. Monitoring:
   ```python
   # Get circuit status
   circuit = await registry.get_circuit("api_service")
   state = circuit.state
   stats = circuit.stats
   ```

2. Metrics:
   ```python
   # Collect all metrics
   cache_metrics = cache_manager.metrics
   perf_metrics = performance_tracker.metrics
   ```

3. Health Checks:
   ```python
   # Check circuit states
   circuits = registry.circuits
   unhealthy = [c for c in circuits.values() if c.state != CircuitState.CLOSED]
   ```

## Error Handling

1. Circuit Open:
   ```python
   try:
       result = await protected_operation()
   except CircuitOpenError:
       result = await fallback_operation()
   ```

2. Cache Errors:
   ```python
   success = cache_manager.set("key", "value")
   if not success:
       # Handle cache failure
   ```

## Future Enhancements

1. Monitoring Integration:
   - Prometheus metrics export
   - Grafana dashboard templates
   - Alert configuration

2. Advanced Features:
   - Custom circuit policies
   - Distributed caching
   - Advanced metrics

3. Configuration:
   - External configuration
   - Dynamic updates
   - Environment overrides
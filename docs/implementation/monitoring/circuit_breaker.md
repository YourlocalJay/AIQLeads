# Circuit Breaker Implementation

## Overview

The circuit breaker pattern prevents cascading failures by monitoring for failures and encapsulating the logic of preventing a failure from constantly recurring.

## Implementation

### Base Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.metrics = MetricsCollector()

    async def call(self, func, *args, **kwargs):
        if not self.can_execute():
            raise CircuitOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def can_execute(self):
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_time:
                self.state = CircuitState.HALF_OPEN
                self.metrics.record_state_change('half_open')
                return True
            return False
            
        # Half-open state
        return True

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.metrics.record_state_change('closed')

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.metrics.record_state_change('open')
```

## Configuration

### Failure Thresholds
- Default: 5 failures
- Configurable per service
- Reset on successful execution

### Recovery Time
- Default: 60 seconds
- Configurable per service
- Exponential backoff option

### States
1. Closed
   - Normal operation
   - Counting failures
   
2. Open
   - Failing fast
   - Preventing calls
   - Waiting for recovery
   
3. Half-Open
   - Testing recovery
   - Limited calls
   - Monitoring closely

## Monitoring

### Metrics
- State changes
- Failure counts
- Recovery attempts
- Success rates

### Alerts
- Circuit open events
- Recovery failures
- Repeated failures
- State transitions

## Integration

### Service Integration
```python
class LeadProcessingService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_time=30
        )
    
    async def process_lead(self, lead_data):
        return await self.circuit_breaker.call(
            self._process_lead_internal,
            lead_data
        )
    
    async def _process_lead_internal(self, lead_data):
        # Lead processing logic
        pass
```

### Monitoring Integration
```python
class CircuitBreakerMetrics:
    def __init__(self):
        self.collector = MetricsCollector()
    
    def record_state_change(self, new_state):
        self.collector.record_metric(
            'circuit_breaker_state',
            new_state,
            {'timestamp': time.time()}
        )
    
    def record_failure(self):
        self.collector.record_metric(
            'circuit_breaker_failure',
            1,
            {'timestamp': time.time()}
        )
```
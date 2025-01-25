# Rate Limiter System

## Overview
Redis-backed rate limiting system with circuit breaker pattern, request batching, and queue management.

## Components
### Base Rate Limiter
- Redis persistence with failover
- Circuit breaker protection
- Concurrent request handling
- Metrics collection

### Application Rate Limiter
- Request batching
- Configurable key prefixing
- Enhanced metrics

### Aggregator Rate Limiter
- Token bucket algorithm
- Request queuing
- Window-based limiting

## Implementation

### Base Usage
```python
from src.aggregator.scrapers.rate_limiters import BaseRateLimiter

limiter = BaseRateLimiter(
    requests_per_minute=100,
    redis_url="redis://localhost:6379/0",
    circuit_breaker_threshold=5
)
await limiter.initialize()

if await limiter.acquire("endpoint_name"):
    process_request()
```

### Application Usage
```python
from src.utils.rate_limiter import RateLimiter

limiter = RateLimiter(
    requests_per_minute=100,
    redis_url="redis://localhost:6379/0",
    key_prefix="api",
    batch_size=10
)

batch = await limiter.acquire_batch("endpoint", items)
```

### Configuration
```python
CONFIG = {
    "redis": {
        "url": "redis://localhost:6379/0",
        "failover_urls": [
            "redis://backup:6379/0"
        ]
    },
    "circuit_breaker": {
        "threshold": 5,
        "timeout": 60
    },
    "queue": {
        "max_size": 1000,
        "batch_size": 10
    },
    "alerts": {
        "error_rate_threshold": 5.0,  # Percentage
        "queue_full_threshold": 80.0,  # Percentage
        "circuit_trips_threshold": 3,  # Per minute
        "response_time_threshold": 500,  # Milliseconds
        "batch_failure_threshold": 10.0,  # Percentage
        "redis_latency_threshold": 100,  # Milliseconds
    }
}
```

## Metrics
- Request count and rates
- Circuit breaker status
- Queue lengths
- Cache hit rates
- Error rates
- Redis latency
- Batch success rates

## Redis Schema
```
{prefix}:{endpoint}:requests -> Sorted set of timestamps
{prefix}:{endpoint}:metrics -> Hash of metrics
{prefix}:{endpoint}:state -> Circuit breaker state
{prefix}:{endpoint}:alerts -> Recent alert history
```

## Monitoring
### Grafana Dashboards
- Request Rate Panel
- Error Rate Panel
- Queue Status Panel
- Circuit Breaker Panel
- Redis Health Panel

### Alert Thresholds
- Error Rate: > 5%
- Queue Full: > 80%
- Circuit Trips: > 3/min
- Response Time: > 500ms
- Batch Failures: > 10%
- Redis Latency: > 100ms

### Alert Channels
- Slack: Real-time notifications
- PagerDuty: Critical failures
- Email: Daily summaries
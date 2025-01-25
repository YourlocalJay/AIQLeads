# Rate Limiter System

## Overview
Redis-backed rate limiting system with real-time metrics, monitoring, and alerts.

## Components
- Redis state persistence
- Per-endpoint rate limiting
- Real-time monitoring dashboard
- Slack/PagerDuty alerts
- Configurable thresholds

## Implementation

### Basic Usage
```python
from src.utils.rate_limiter import RateLimiter

limiter = RateLimiter(
    key="endpoint_name",
    max_requests=100,
    time_window=60  # seconds
)

async def endpoint_handler():
    if not await limiter.allow_request():
        raise RateLimitExceeded()
    return await process_request()
```

### Configuration
```python
RATE_LIMIT_CONFIG = {
    "default": {
        "max_requests": 100,
        "time_window": 60
    },
    "high_priority": {
        "max_requests": 200,
        "time_window": 60
    }
}
```

### Metrics Collection
- Request count
- Error rates
- Response times
- Cache hit rates

### Alert Thresholds
- Error Rate: > 5%
- Response Time: > 500ms
- Rate Limit Hits: > 10/min

## Redis Schema
```
rate_limit:{endpoint}:requests -> Sorted set of request timestamps
rate_limit:{endpoint}:metrics -> Hash of metric values
rate_limit:{endpoint}:config -> Hash of configuration
```

## Monitoring
- Real-time dashboard with Grafana
- Alert integration via Slack/PagerDuty
- Custom metric collection

## Recovery Mechanisms
- Automatic Redis failover
- Request queuing
- Circuit breakers
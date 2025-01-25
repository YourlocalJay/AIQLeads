# RateLimiter.md

## Overview

The Rate Limiter in AIQLeads is a critical system component designed to manage the frequency of API requests and internal operations. It prevents system overload, ensures fair resource usage, and mitigates abusive behavior. It operates with a robust architecture leveraging **Redis**, **custom tokens**, and **monitoring tools** to provide real-time rate limiting, tracking, and alerting capabilities.

---

## Key Features

1. **Redis-Powered Token Bucket Algorithm**
   - Redis is used for maintaining tokens and rate state in memory with high availability and low latency.
   - Supports both global and user-specific rate limits.
   - Implements expiration mechanisms to clean up stale buckets.

2. **Dynamic Rate Limits**
   - Configurable thresholds for different API tiers:
     - **Basic Tier**: 100 requests per minute.
     - **Pro Tier**: 500 requests per minute.
     - **Enterprise Tier**: 1,000 requests per minute.
   - Adaptive rate limits based on system load or subscription tier.

3. **Circuit Breaker Integration**
   - Automatically disables or throttles operations if API or system failures exceed a specified threshold.
   - Prevents cascading failures across dependent systems.

4. **Real-Time Monitoring and Alerts**
   - Integration with **Prometheus/Grafana** to visualize rate limiter performance.
   - Slack and PagerDuty alerts for:
     - Excessive API usage.
     - Persistent Redis failures.
     - Rate limit breaches.

---

## Architecture

### High-Level Design

1. **Core Components**:
   - **Token Bucket Store**: Redis maintains token buckets for all users or system components.
   - **Rate Limiter Middleware**: A FastAPI middleware that checks the token count for each request.
   - **Rate Limiter Service**: Handles token issuance, refills, and synchronization with Redis.

2. **Flow**:
   - **Request Flow**:
     - On each API request, the middleware intercepts the request and:
       1. Validates the user’s identity or subscription tier.
       2. Checks the token bucket for available capacity in Redis.
       3. Allows or denies the request based on token availability.
   - **Token Refill**:
     - Token refill occurs asynchronously based on the user’s rate limit configuration.

3. **Database Support**:
   - Token states are persisted in Redis for fast lookup.
   - Fallback mechanisms ensure continued operation in case of Redis downtime.

4. **Integration Points**:
   - **Prometheus**: Tracks token usage, request latencies, and rate limit breaches.
   - **Redis Sentinel/Cluster**: Ensures high availability of the token bucket store.
   - **Slack Alerts**: Sends notifications for critical failures or unusual usage spikes.

---

## Configuration

### Rate Limits
The rate limiter allows tier-based configuration.

```yaml
# Sample YAML Configuration
rate_limits:
  basic:
    requests_per_minute: 100
    burst_limit: 20
  pro:
    requests_per_minute: 500
    burst_limit: 100
  enterprise:
    requests_per_minute: 1000
    burst_limit: 200
```

### Redis Settings
Defined in the `settings.py` file:

```python
REDIS_URL = "redis://localhost:6379/0"
DEFAULT_EXPIRY = 60  # seconds
TOKEN_BUCKET_CAPACITY = 100
TOKEN_BUCKET_REFILL_RATE = 1  # tokens/second
```

---

## Implementation Details

### Token Bucket Algorithm
The token bucket is implemented using Redis commands:

1. **Initialization**:
   - A bucket is created for each user or component.
   - The bucket has a maximum capacity (e.g., 100 tokens).

2. **Token Consumption**:
   - On each request, the middleware deducts a token using a Lua script to ensure atomicity.

3. **Refill Logic**:
   - Tokens are refilled periodically based on the configured rate.

Example Lua Script for Atomic Token Deduction:

```lua
local tokens = redis.call("GET", KEYS[1])
if not tokens then
  tokens = tonumber(ARGV[1])
  redis.call("SET", KEYS[1], tokens, "EX", ARGV[2])
end
if tonumber(tokens) > 0 then
  redis.call("DECR", KEYS[1])
  return 1
else
  return 0
end
```

### Circuit Breaker Integration
The circuit breaker is implemented in the `rate_limiter.py` module. It:

- Tracks consecutive failures.
- Disables or slows down the rate limiter when thresholds are exceeded.

---

## Monitoring and Metrics

### Prometheus Metrics

- **Tokens Consumed**:
  ```plaintext
  rate_limiter_tokens_consumed{tier="basic"} 95
  rate_limiter_tokens_consumed{tier="pro"} 450
  ```

- **Rate Limit Breaches**:
  ```plaintext
  rate_limiter_breaches{tier="basic"} 5
  rate_limiter_breaches{tier="enterprise"} 1
  ```

- **Redis Latency**:
  ```plaintext
  redis_operation_latency_ms 10.5
  ```

### Grafana Dashboards

- **Key Panels**:
  - Requests per second.
  - Rate limit breaches per tier.
  - Redis connection health.

---

## Alerts and Notifications

### Slack Alerts
- Triggers:
  - Breach threshold for API requests.
  - Redis unavailability for over 5 minutes.

### PagerDuty Notifications
- Triggers:
  - Circuit breaker activation.
  - Persistent rate limiter failures impacting user requests.

---

## Testing

### Unit Tests
- `test_rate_limiter.py`
  - Covers token consumption, refill logic, and Redis interactions.

### Integration Tests
- `test_rate_limiter_integration.py`
  - Tests Redis persistence and token state across multiple API calls.

### Performance Tests
- Load test scenarios using tools like Locust or JMeter.
- Validate the rate limiter’s ability to handle bursts and sustained traffic.

---

## Future Enhancements

1. **Dynamic Throttling**
   - Automatically adjust rate limits based on real-time system load or subscription upgrades.

2. **Per-Endpoint Rate Limits**
   - Allow different thresholds for specific endpoints (e.g., higher limits for GET requests).

3. **Caching Layer**
   - Introduce a lightweight local cache for frequent token lookups to reduce Redis overhead.

4. **Enhanced Analytics**
   - Add anomaly detection to flag unusual traffic patterns or abuse.

---

## Conclusion
The AIQLeads Rate Limiter is a highly performant, scalable, and configurable component designed to ensure fair resource usage and prevent abuse. By leveraging Redis, Prometheus, and robust algorithms, it provides the foundation for managing high-traffic API interactions while delivering real-time visibility and control for system administrators.

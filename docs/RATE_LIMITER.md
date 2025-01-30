# AIQLeads Rate Limiter

## Overview
The AIQLeads Rate Limiter is a Redis-backed solution providing intelligent rate limiting with AI-driven batching, high availability, and comprehensive monitoring capabilities.

## Key Features

### 1. AI-Driven Adaptive Batching
- Dynamic batch size adjustments based on success rates
- Rolling window analysis for optimal throughput
- Automatic scaling based on performance metrics
- Intelligent backpressure handling

### 2. High Availability
- Multi-region Redis support
- Automatic failover handling
- Local fallback capability
- Circuit breaking protection

### 3. Advanced Monitoring
- Comprehensive metrics collection
- Prometheus compatibility
- Real-time performance tracking
- Detailed failure analysis

## Usage Example

```python
# Initialize the rate limiter
limiter = RateLimiter(
    requests_per_minute=1000,
    redis_urls=[
        "redis://primary:6379",
        "redis://secondary:6379"
    ],
    key_prefix="api",
    batch_size=10
)

# Process a batch of items
async def process_items(items):
    allowed_items = await limiter.acquire_batch(
        endpoint="users",
        items=items,
        max_retries=3
    )
    return allowed_items
```

## Configuration Options

### Required Parameters
- `requests_per_minute`: Maximum requests allowed per minute
- `redis_urls`: List of Redis instance URLs for HA setup

### Optional Parameters
- `key_prefix`: Redis key prefix (default: "app")
- `batch_size`: Initial batch size (default: 10)
- `fallback_enabled`: Enable local fallback (default: True)

## Monitoring & Metrics

### Available Metrics
- Total requests processed
- Successful/partial/failed batches
- Redis failure count
- Batch success rate
- Average batch utilization
- Fallback activation status

### Prometheus Integration
Compatible with Prometheus monitoring:
```python
metrics = await limiter.get_enhanced_metrics("endpoint")
```

## Best Practices

1. Redis Configuration
   - Use multiple Redis instances for HA
   - Configure appropriate timeouts
   - Monitor Redis health

2. Batch Size Tuning
   - Start with conservative batch sizes
   - Monitor success rates
   - Allow AI adaptation time

3. Error Handling
   - Implement proper retry logic
   - Monitor fallback usage
   - Track error patterns

4. Performance Optimization
   - Monitor batch utilization
   - Adjust pressure thresholds
   - Review metrics regularly

## Implementation Details

### Key Components

1. Batch Processing
   - Intelligent batch chunking
   - Automatic retry mechanism
   - Failure detection

2. Redis Management
   - Connection pooling
   - Automatic failover
   - Key prefix validation

3. Metrics Collection
   - Real-time tracking
   - Historical analysis
   - Performance indicators

### Safety Features

1. Input Validation
   - Key prefix safety checks
   - Batch size validation
   - Parameter sanitization

2. Error Recovery
   - Automatic Redis failover
   - Local fallback mechanism
   - Circuit breaker pattern

3. Resource Protection
   - Adaptive backpressure
   - Connection pooling
   - Memory management
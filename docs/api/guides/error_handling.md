# Error Handling Guide

This guide explains how to handle errors in the AIQLeads API.

## Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "field": "string",
      "reason": "string"
    }
  }
}
```

## HTTP Status Codes

| Status Code | Description |
|------------|-------------|
| 400 | Bad Request - Invalid parameters or payload |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Valid auth but insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Request validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Server Error - Internal server error |
| 503 | Service Unavailable - Service temporarily unavailable |

## Error Codes

### Authentication Errors

| Code | Description |
|------|-------------|
| `invalid_auth` | Invalid authentication credentials |
| `expired_key` | API key has expired |
| `insufficient_scope` | API key lacks required permissions |

### Validation Errors

| Code | Description |
|------|-------------|
| `invalid_param` | Invalid parameter value |
| `missing_param` | Required parameter missing |
| `invalid_format` | Invalid data format |

### Business Logic Errors

| Code | Description |
|------|-------------|
| `resource_exists` | Resource already exists |
| `resource_locked` | Resource is locked for editing |
| `dependency_conflict` | Operation conflicts with dependencies |

## Error Handling Best Practices

### Rate Limiting

When receiving a 429 status code:
1. Check the `X-RateLimit-Reset` header
2. Wait until the reset timestamp
3. Retry the request

Example rate limit headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1612345678
```

### Retry Strategy

For 5xx errors:
1. Implement exponential backoff
2. Start with 1 second delay
3. Double delay with each retry
4. Maximum 5 retries

Example retry implementation:
```python
def make_request_with_retry(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = make_request(url)
            return response
        except ServerError:
            if attempt == max_retries - 1:
                raise
            sleep_time = (2 ** attempt)
            time.sleep(sleep_time)
```

### Validation Errors

For 422 validation errors:
1. Check the error.details field
2. Extract the specific validation failure
3. Update the request accordingly

Example validation error:
```json
{
  "error": {
    "code": "invalid_format",
    "message": "Invalid lead data format",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  }
}
```

### Error Logging

Important error fields to log:
- HTTP status code
- Error code
- Error message
- Request ID (from `X-Request-ID` header)
- Timestamp
- Request context

Example logging:
```python
{
    "timestamp": "2025-01-28T12:00:00Z",
    "request_id": "req_abc123",
    "status_code": 422,
    "error_code": "invalid_format",
    "error_message": "Invalid lead data format",
    "context": {
        "endpoint": "/v1/leads",
        "method": "POST",
        "user_id": "usr_123"
    }
}
```

## Common Error Scenarios

### Authentication

```json
{
  "error": {
    "code": "invalid_auth",
    "message": "Invalid API key provided",
    "details": {
      "reason": "API key has been revoked"
    }
  }
}
```

### Rate Limiting

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests",
    "details": {
      "reset_at": "2025-01-28T12:05:00Z",
      "retry_after": 300
    }
  }
}
```

### Validation

```json
{
  "error": {
    "code": "invalid_param",
    "message": "Invalid parameter value",
    "details": {
      "field": "score_min",
      "reason": "Must be between 0 and 100"
    }
  }
}
```
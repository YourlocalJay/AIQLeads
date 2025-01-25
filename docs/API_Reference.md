# AIQLeads API Reference

## Schema Validation Framework

### Core Validation Rules

1. **Authentication Data**
   - Email: RFC 5322 standard compliance
   - Password: Minimum 8 characters, includes uppercase, lowercase, number, special character
   - Phone: International format with country code (+X-XXX-XXX-XXXX)
   - Token: JWT format with required claims

2. **Lead Data**
   - Price: Positive decimal, maximum 2 decimal places
   - Location: Valid coordinates within supported regions
   - Description: Maximum 2000 characters
   - Metadata: Valid JSON object with predefined schema

3. **Transaction Data**
   - Amount: Positive decimal, maximum 2 decimal places
   - Timestamp: ISO 8601 format
   - Reference IDs: UUID v4 format
   - Status: Enumerated valid states

### Enhanced Error Responses

All validation errors return a 422 Unprocessable Entity status with detailed context:

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "request_id": "uuid-v4",
  "timestamp": "2025-01-25T12:00:00Z",
  "detail": [
    {
      "field": "field_name",
      "error": "specific_error_type",
      "message": "Human-readable explanation",
      "value": "submitted_value",
      "constraints": {
        "rule_name": "rule_details",
        "allowed_values": ["valid_options"],
        "pattern": "regex_pattern"
      },
      "location": "body|query|header",
      "suggestion": "Suggested correction"
    }
  ],
  "metrics": {
    "validation_time": "5ms",
    "schema_version": "1.2.0"
  }
}
```

## Monitoring Integration

### Validation Metrics

```json
{
  "metrics": {
    "validation_time": "5ms",
    "schema_version": "1.2.0",
    "cache_status": "hit|miss",
    "validation_path": "auth.login.email"
  },
  "telemetry": {
    "request_id": "uuid-v4",
    "timestamp": "2025-01-25T12:00:00Z",
    "client_version": "2.1.0"
  }
}
```

[Previous authentication endpoints content...]

## Performance Considerations

### Validation Processing
- Average validation time: 5ms
- Timeout threshold: 500ms
- Rate limits: 100 requests/minute
- Schema cache hit rate: 95%

### Response Times
- Authentication: 95% < 200ms
- Data validation: 99% < 100ms
- Error responses: 90% < 50ms
- Schema resolution: 95% < 10ms

### Monitoring Integration
- Prometheus metrics export
- Grafana dashboards
- Alert thresholds
- Performance tracking

## Best Practices

1. **Input Validation**
   - Always validate data before processing
   - Use appropriate content-type headers
   - Handle character encoding properly
   - Implement schema caching

2. **Error Handling**
   - Include sufficient error details
   - Maintain consistent error format
   - Avoid exposing internal errors
   - Track validation failures

3. **Security**
   - Validate authentication tokens
   - Sanitize all user inputs
   - Implement rate limiting
   - Monitor validation patterns

4. **Performance**
   - Use schema caching
   - Implement batch validation
   - Monitor validation times
   - Track schema versions

## Testing Guidelines

1. **Validation Testing**
   - Test boundary conditions
   - Verify all validation rules
   - Check error message clarity
   - Monitor performance impact

2. **Performance Testing**
   - Monitor validation times
   - Test under expected load
   - Verify timeout handling
   - Track cache efficiency
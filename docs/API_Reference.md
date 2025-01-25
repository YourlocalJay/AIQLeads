# AIQLeads API Reference

## Schema Validation Framework

### Core Validation Rules

1. **Authentication Data**
   - Email: RFC 5322 standard compliance
   - Password: Minimum 8 characters, includes uppercase, lowercase, number, special character
   - Phone: International format with country code (+X-XXX-XXX-XXXX)

2. **Lead Data**
   - Price: Positive decimal, maximum 2 decimal places
   - Location: Valid coordinates within supported regions
   - Description: Maximum 2000 characters

3. **Transaction Data**
   - Amount: Positive decimal, maximum 2 decimal places
   - Timestamp: ISO 8601 format
   - Reference IDs: UUID v4 format

### Standard Error Responses

All validation errors return a 422 Unprocessable Entity status with structured details:

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "detail": [
    {
      "field": "field_name",
      "error": "specific_error_type",
      "message": "Human-readable explanation",
      "constraints": {
        "rule_name": "rule_details"
      }
    }
  ]
}
```

## Authentication Endpoints

### Login
**POST /api/auth/login**

Validates user credentials and issues access token.

#### Request Schema
```json
{
  "email": "user@example.com",     // Required, valid email format
  "password": "SecurePass123!",   // Required, meets complexity rules
  "device_id": "uuid-v4"          // Optional, UUID v4 format
}
```

#### Success Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Validation Errors
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "detail": [
    {
      "field": "email",
      "error": "invalid_format",
      "message": "Invalid email format"
    }
  ]
}
```

### Register
**POST /api/auth/register**

Creates new user account with validation.

#### Request Schema
```json
{
  "email": "user@example.com",      // Required, unique email
  "password": "SecurePass123!",    // Required, meets complexity rules
  "phone": "+1-234-567-8900",      // Optional, valid format
  "company_name": "Example Inc"     // Optional, 2-100 chars
}
```

#### Success Response (201 Created)
```json
{
  "id": "uuid-v4",
  "email": "user@example.com",
  "created_at": "2025-01-25T12:00:00Z"
}
```

[Previous API endpoints content continues...]

## Performance Considerations

### Validation Processing
- Average validation time: 5ms
- Timeout threshold: 500ms
- Rate limits: 100 requests/minute

### Response Times
- Authentication: 95% < 200ms
- Data validation: 99% < 100ms
- Error responses: 90% < 50ms

## Best Practices

1. **Input Validation**
   - Always validate data before processing
   - Use appropriate content-type headers
   - Handle character encoding properly

2. **Error Handling**
   - Include sufficient error details
   - Maintain consistent error format
   - Avoid exposing internal errors

3. **Security**
   - Validate authentication tokens
   - Sanitize all user inputs
   - Implement rate limiting

## Testing Guidelines

1. **Validation Testing**
   - Test boundary conditions
   - Verify all validation rules
   - Check error message clarity

2. **Performance Testing**
   - Monitor validation times
   - Test under expected load
   - Verify timeout handling

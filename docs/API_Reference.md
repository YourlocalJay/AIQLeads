# AIQLeads API Reference

## Schema Validation

All API endpoints implement strict schema validation using Pydantic. Requests must conform to the following validation rules:

### Common Validation Rules
- Email addresses must be valid format
- Phone numbers must include country code (+X-XXX-XXX-XXXX)
- Passwords must meet complexity requirements

### Validation Error Responses
When validation fails, the API returns a 422 Unprocessable Entity response:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Detailed error message",
      "type": "value_error"
    }
  ]
}
```

[Previous API Reference Content...]

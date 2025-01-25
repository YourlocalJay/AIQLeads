## Validation Service Documentation

### Error Handling
The validation service uses a standardized error handling system:
```python
from services.validation.errors import ValidationError, ValidationErrorType

try:
    # Your validation code
    raise ValidationError(
        error_type=ValidationErrorType.SCHEMA_ERROR,
        message="Invalid schema",
        field="email"
    )
except ValidationError as e:
    response = handle_validation_error(e)
```

### Error Types
- SCHEMA_ERROR: Schema validation failures
- DATA_TYPE_ERROR: Type mismatches
- MISSING_FIELD: Required field absence
- INVALID_FORMAT: Format violations
- BUSINESS_RULE: Business logic violations
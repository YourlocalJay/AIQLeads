# Schema Documentation

## Overview
The schema system provides data validation and serialization for the AIQLeads platform. It ensures data integrity across the application by enforcing consistent validation rules and type checking.

## User Schemas

### UserBase
Base schema containing common user fields:
- `email`: Email address (validated format)
- `first_name`: Optional first name
- `last_name`: Optional last name
- `company_name`: Optional company name
- `phone`: Optional phone number with strict format validation

### UserCreate
Schema for user creation operations:
- Inherits from UserBase
- Adds required password field with complexity validation:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character (@$!%*?&#)

### UserUpdate
Schema for partial user updates:
- All fields optional
- Maintains validation rules from UserBase
- Password updates follow same complexity requirements
- Phone number updates maintain strict format validation

### UserInDB
Database representation schema:
- Inherits from UserBase
- Adds system fields:
  - `id`: Unique identifier
  - `is_active`: Account status
  - `is_verified`: Email verification status
  - `created_at`: Account creation timestamp
  - `updated_at`: Last update timestamp
- Configured for ORM mode
- Handles UTC datetime serialization

### UserResponse
API response schema:
- Inherits from UserInDB
- Excludes sensitive information
- Used for API endpoints

## Validation Rules

### Phone Number Format
- Must include country code
- Format: +X-XXX-XXX-XXXX
- Validates:
  - Proper country code format
  - No double plus signs
  - Correct digit grouping
  - Allowed separators (hyphen or space)

### Password Requirements
- Minimum 8 characters
- Must include:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Numbers (0-9)
  - Special characters (@$!%*?&#)

## Usage Examples

### User Creation
```python
user_data = {
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "phone": "+1-234-567-8900"
}
user = UserCreate(**user_data)
```

### User Update
```python
update_data = {
    "phone": "+1-555-123-4567",
    "company_name": "New Company"
}
update = UserUpdate(**update_data)
```

## Performance Considerations
- Schema validation average processing time: 5ms
- Optimized for high-throughput validation
- Efficient memory usage through Pydantic
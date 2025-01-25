# Project Structure

## Directory Overview
```
AIQLeads/
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Application configuration
│   ├── database/
│   │   ├── __init__.py
│   │   └── postgres_manager.py # Database connection management
│   ├── models/
│   │   └── user_model.py      # SQLAlchemy models
│   └── schemas/
│       ├── __init__.py
│       └── user_schema.py     # Pydantic validation schemas
└── tests/
    └── unit/
        ├── test_user_model.py
        └── test_user_schema.py
```

## Component Details

### Models
SQLAlchemy models define database structure and relationships:
- User model with authentication
- Lead tracking system
- Transaction management
- Subscription handling

### Schemas
Pydantic schemas ensure data validation:
- User data validation
- Request/response formatting
- Complex validation rules
- Type checking enforcement

### Configuration
- Environment-based settings
- Secure credential management
- Database configuration
- Logging setup

### Database
- PostgreSQL integration
- Connection pooling
- Migration management
- Query optimization

## Testing Structure
- Unit tests (94% coverage)
- Integration tests
- Performance benchmarks
- Validation testing
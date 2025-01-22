# Project Structure

```
AIQLeads/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_model.py
│   │   ├── lead_model.py
│   │   ├── transaction_model.py
│   │   ├── subscription_model.py
│   │   └── market_insights_model.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── lead_service.py
│   │   ├── pricing_service.py
│   │   └── recommendations_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py
│   │   │   │   ├── leads.py
│   │   │   │   └── transactions.py
│   │   │   └── dependencies.py
│   │   └── middleware.py
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_user_model.py
│   │   ├── test_lead_model.py
│   │   ├── test_transaction_model.py
│   │   └── test_subscription_model.py
│   └── integration/
│       ├── __init__.py
│       └── test_alembic_migrations.py
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── initial_migration.py
├── docs/
│   ├── README.md
│   ├── Architecture.md
│   ├── ProjectStructure.md
│   ├── MVP_Overview.md
│   └── MarketInsights.md
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
└── UPDATE.md
```

## Key Directories

- `src/`: Main application code
  - `models/`: SQLAlchemy models defining database schema
  - `services/`: Business logic and core functionality
  - `api/`: FastAPI routes and endpoint handlers
  - `utils/`: Shared utilities and helper functions

- `tests/`: Test suite
  - `unit/`: Unit tests for individual components
  - `integration/`: Integration tests for system components

- `migrations/`: Alembic database migrations
  - `versions/`: Individual migration scripts

- `docs/`: Project documentation

## File Naming Conventions

1. All Python files use snake_case
2. Test files are prefixed with `test_`
3. Model files are suffixed with `_model.py`
4. Service files are suffixed with `_service.py`
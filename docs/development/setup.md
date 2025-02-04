# Development Setup Guide

## Overview
This guide provides detailed instructions for setting up the AIQLeads development environment.

## Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git
- PostgreSQL client
- Redis client

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/YourlocalJay/AIQLeads.git
cd AIQLeads
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your local settings
```

### 3. Development Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Pre-commit Hooks
```bash
pre-commit install
```

## Database Setup

### Local PostgreSQL
```bash
# Create database
psql -U postgres -c 'create database aiqleads;'

# Run migrations
alembic upgrade head
```

### Using Docker
```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head
```

## Development Tools

### Code Quality
- Black for formatting
- Flake8 for linting
- MyPy for type checking
- Pytest for testing

### Running Tests
```bash
# Unit tests
pytest

# With coverage
pytest --cov=app

# Integration tests
pytest tests/integration
```

### Local Development Server
```bash
# Start development server
uvicorn app.main:app --reload

# With debugger
python -m debugpy --listen 5678 -m uvicorn app.main:app --reload
```

## Git Workflow

### Branch Strategy
- main: Production code
- develop: Integration branch
- feature/*: New features
- bugfix/*: Bug fixes
- release/*: Release preparation

### Commit Guidelines
- Use semantic commit messages
- Include ticket numbers
- Keep commits focused

## Documentation

### API Documentation
- OpenAPI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Code Documentation
```bash
# Generate documentation
sphinx-build -b html docs/source docs/build
```

## Troubleshooting

### Common Issues
1. Database connection errors
   - Check PostgreSQL service
   - Verify connection string
   - Check permissions

2. Redis connection issues
   - Verify Redis service
   - Check port availability
   - Review configuration

3. Docker issues
   - Clean containers: `docker-compose down -v`
   - Rebuild: `docker-compose build --no-cache`
   - Check logs: `docker-compose logs -f`

## Support

### Getting Help
- Check existing documentation
- Review closed issues
- Open new issue with details

### Contributing
Refer to CONTRIBUTING.md for:
- Code style guide
- Pull request process
- Review guidelines
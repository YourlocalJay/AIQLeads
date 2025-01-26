# AIQLeads Project

## Project Overview
AIQLeads is a comprehensive lead management and market insights platform built with modern architecture principles. The system leverages advanced AI capabilities, geospatial analytics, and real-time processing to deliver actionable insights.

## Current Status
- Core infrastructure: Complete
- User management: Complete
- Lead processing: Complete
- Market insights: Complete
- Schema monitoring: Complete
- AI recommendations: In development (35%)

## Active Development
1. Integration Testing Framework (95%)
2. Cart Management System (80%)
3. AI Recommendations System (35%)

## Next Milestone
- Target Date: February 15, 2025
- Deliverable: AI Recommendations MVP

## Technical Stack
- Backend: FastAPI, PostgreSQL 15.4, PostGIS 3.4
- Caching: Redis 7.2
- Testing: PyTest (94% coverage)
- Authentication: JWT with Argon2 hashing
- Analytics: Prometheus, Grafana
- ML Pipeline: Custom feature engineering and training infrastructure

## Getting Started
Refer to [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions and development guidelines.

## Project Structure
```
AIQLeads/
├── api/            # FastAPI routes and endpoints
├── core/           # Core business logic
├── models/         # Database models and schemas
├── services/       # External service integrations
├── utils/          # Utility functions and helpers
├── tests/          # Test suites
└── docs/           # Documentation
```

## Documentation
- API Documentation: `/docs/api`
- Architecture Overview: `/docs/architecture`
- Development Guide: `/docs/development`
- Deployment Guide: `/docs/deployment`
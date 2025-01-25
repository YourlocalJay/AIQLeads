# Project Structure for AIQLeads MVP

## Current Directory Structure
The following outlines the existing directory structure for the AIQLeads MVP as of the latest development stage:

```
AIQLeads/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                 # Continuous Integration workflow
│   │   ├── cd.yml                 # Continuous Deployment workflow
│   │   └── lint.yml               # Linting workflow
├── .gitignore                     # Ignore rules for Git
├── LICENSE                        # License for the repository
├── README.md                      # Project overview and instructions
├── requirements.txt               # Python dependencies
├── setup.py                       # Python package setup (or pyproject.toml if in use)
├── Dockerfile                     # Container setup for the application
├── docker-compose.yml             # Orchestration for Docker services
├── .env.example                   # Example environment variable configuration
├── UPDATE.md                      # Tracker for MVP development and progress
├── docs/                          # Documentation folder
│   ├── README.md                  # Documentation overview
│   ├── MVP_Overview.md            # Detailed MVP feature list
│   ├── Architecture.md            # Technical architecture details
│   ├── MarketInsights.md          # Details for market insights module
│   ├── ProjectStructure.md        # (This file) Overview of folder structure
│   └── CHANGELOG.md               # Version history and updates
├── migrations/                    # Database migration scripts
│   ├── versions/                  # Specific migration files
├── scripts/                       # Scripts for deployment and automation
│   ├── deploy.sh                  # Deployment automation
│   ├── seed_db.py                 # Populate the database with test data
│   └── infra/                     # Infrastructure as code
│       └── terraform/             # Terraform scripts for cloud provisioning
├── src/                           # Source code for the application
│   ├── __init__.py                # Initialization file for the source code
│   ├── main.py                    # Entry point for the FastAPI application
│   ├── config/                    # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py            # Environment and settings configuration
│   ├── database/                  # Database connection and management
│   │   ├── __init__.py
│   │   ├── postgres_manager.py    # PostgreSQL session and connection manager
│   │   ├── redis_manager.py       # Redis connection for caching and rate limiting
│   │   └── search_manager.py      # Elasticsearch/OpenSearch integration
│   ├── models/                    # ORM models
│   │   ├── __init__.py
│   │   ├── user_model.py          # User model
│   │   ├── lead_model.py          # Lead model with geospatial support
│   │   ├── transaction_model.py   # Transaction model for credit tracking
│   │   ├── subscription_model.py  # Subscription tier and billing model
│   │   └── market_insight_model.py# Market insights and analytics data
│   ├── schemas/                   # Request/response validation schemas
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   ├── lead_schema.py
│   │   ├── transaction_schema.py
│   │   ├── subscription_schema.py
│   │   └── market_insight_schema.py
│   ├── services/                  # Business logic and integrations
│   │   ├── __init__.py
│   │   ├── lead_marketplace_service.py
│   │   ├── dynamic_pricing_service.py
│   │   ├── cart_management_service.py
│   │   ├── credit_system_service.py
│   │   ├── lead_review_service.py
│   │   ├── subscription_service.py
│   │   ├── ai_recommendations_service.py
│   │   ├── analytics_service.py
│   │   └── ai_pipeline_manager.py
│   ├── controllers/               # API endpoints
│   │   ├── __init__.py
│   │   ├── lead_marketplace_controller.py
│   │   ├── dynamic_pricing_controller.py
│   │   ├── cart_management_controller.py
│   │   ├── credit_system_controller.py
│   │   ├── subscription_controller.py
│   │   └── ai_recommendations_controller.py
│   ├── aggregator/                # Scraping and normalization
│   │   ├── __init__.py
│   │   ├── pipeline.py            # Data scraping pipeline
│   │   ├── scraper_utils.py       # Shared scraping utilities
│   │   ├── scrapers/
│   │   │   ├── linkedin_scraper.py
│   │   │   ├── facebook_scraper.py
│   │   │   ├── zillow_scraper.py
│   │   │   ├── craigslist_scraper.py
│   │   └── parsers/
│   │       ├── linkedin_parser.py
│   │       └── facebook_parser.py
│   ├── monitoring/                # Monitoring and metrics
│   │   ├── metrics_service.py
│   │   └── alerts_service.py
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── logger.py              # Logging setup
│       ├── validators.py          # Input validation
│       └── common.py              # Shared helpers
└── tests/                         # Test suite
    ├── __init__.py
    ├── unit/                      # Unit tests
    ├── integration/               # Integration tests
    └── e2e/                       # End-to-end tests
```

---

## Proposed Completed Path Tree

The following is a proposed structure for the fully completed and production-ready AIQLeads project:

```
AIQLeads/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       ├── lint.yml
│       └── security_scan.yml
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── UPDATE.md
├── docs/
│   ├── README.md
│   ├── MVP_Overview.md
│   ├── Architecture.md
│   ├── MarketInsights.md
│   ├── ProjectStructure.md
│   ├── CHANGELOG.md
│   └── LEGAL/
│       ├── TermsOfService.md
│       └── PrivacyPolicy.md
├── migrations/
├── scripts/
│   ├── deploy.sh
│   ├── seed_db.py
│   └── infra/
│       └── terraform/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── controllers/
│   ├── aggregator/
│   ├── monitoring/
│   └── utils/
└── tests/
    ├── __init__.py
    ├── mocks/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## Changes Proposed
- Added LinkedIn and Facebook scrapers to `scrapers/`.
- Added missing market insights schema and model files.
- Enhanced the proposed `docs/` folder for legal compliance documents.
- Expanded `tests/` folder for mock data and complete test coverage.
- Suggested Terraform under `scripts/infra/` for scalable infrastructure.

---

## Maintenance Notes
This directory structure is flexible enough to allow the addition of future modules or services, such as CRM integrations, marketing automations, or user activity monitoring.

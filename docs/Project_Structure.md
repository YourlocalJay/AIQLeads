# Project Structure

This document outlines the proposed full directory structure for the **AIQLeads** project. The structure builds upon the existing directory structure to ensure clarity and eliminate any confusion. The proposed layout reflects the final organization for the MVP, incorporating all planned components and enhancements.

## Proposed Directory Structure

```plaintext
AIQLeads/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                   # CI pipeline for testing
│   │   ├── cd.yml                   # CD pipeline for deployment
│   │   └── lint.yml                 # Code formatting checks (Black, isort)
│   ├── scripts/
│   │   └── update_files.py          # GitHub automation scripts
│   └── dependabot.yml               # Dependency monitoring and updates
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py                         # Package setup (or pyproject.toml for modern packaging)
├── Dockerfile                       # Container configuration
├── docker-compose.yml               # Multi-service container management
├── .env.example                     # Environment variable configuration template
├── UPDATE.md                        # Tracks project progress and milestones

├── docs/                            # Project documentation
│   ├── MVP_Overview.md              # Features and goals of the MVP
│   ├── Architecture.md              # Technical architecture
│   ├── MarketInsights.md            # Market-specific insights and trends
│   ├── ProjectStructure.md          # This file
│   ├── API_Reference.md             # API documentation
│   ├── DataFlow.md                  # Overview of data ingestion, storage, and processing
│   └── CHANGELOG.md                 # Version history and updates

├── migrations/                      # Database migration scripts
│   └── versions/

├── scripts/                         # Auxiliary scripts
│   ├── deploy.sh                    # Deployment automation
│   ├── seed_db.py                   # Populate the database with initial data
│   ├── ephemeral_env_setup.sh       # Setup ephemeral test environments
│   └── infra/
│       └── terraform/               # Infrastructure as Code (IaC) for cloud deployments
│           └── main.tf

├── src/                             # Core application code
│   ├── __init__.py
│   ├── main.py                      # FastAPI entry point
│
│   ├── config/                      # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py              # Environment variables and logging
│
│   ├── database/                    # Database and caching layers
│   │   ├── __init__.py
│   │   ├── postgres_manager.py      # PostgreSQL connection manager
│   │   ├── redis_manager.py         # Redis caching and session management
│   │   ├── search_manager.py        # Elasticsearch/OpenSearch integration
│   │   └── geospatial_manager.py    # PostGIS for geospatial queries
│
│   ├── aggregator/                  # Scraping and data ingestion
│   │   ├── __init__.py
│   │   ├── pipeline.py              # Coordinates scraping and normalization
│   │   ├── scraper_utils.py         # Shared scraping utilities
│   │   ├── scrapers/                # Platform-specific scrapers
│   │   │   ├── __init__.py
│   │   │   ├── craigslist_scraper.py
│   │   │   ├── zillow_scraper.py
│   │   │   ├── fsbo_scraper.py
│   │   │   ├── facebook_scraper.py
│   │   │   ├── linkedin_scraper.py
│   │   │   ├── las_vegas_scraper.py
│   │   │   ├── dallas_scraper.py
│   │   │   ├── austin_scraper.py
│   │   │   └── phoenix_scraper.py
│   │   ├── parsers/                 # Data parsers
│   │   │   ├── __init__.py
│   │   │   ├── craigslist_parser.py
│   │   │   ├── zillow_parser.py
│   │   │   ├── fsbo_parser.py
│   │   │   ├── facebook_parser.py
│   │   │   ├── linkedin_parser.py
│   │   │   ├── las_vegas_parser.py
│   │   │   ├── dallas_parser.py
│   │   │   ├── austin_parser.py
│   │   │   └── phoenix_parser.py
│   │   └── exceptions.py            # Custom exceptions for scraping and parsing
│
│   ├── models/                      # Database models
│   │   ├── __init__.py
│   │   ├── user_model.py            # User model
│   │   ├── lead_model.py            # Lead model with fraud detection
│   │   ├── transaction_model.py     # Transaction model
│   │   ├── subscription_model.py    # Subscription model
│   │   ├── market_insights_model.py # Aggregated market data
│   │   └── model_version_model.py   # Tracks AI model versions
│
│   ├── schemas/                     # Request/response validation schemas
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   ├── lead_schema.py
│   │   ├── pricing_schema.py
│   │   ├── subscription_schema.py
│   │   └── market_insight_schema.py
│
│   ├── services/                    # Business logic and integrations
│   │   ├── __init__.py
│   │   ├── lead_marketplace_service.py
│   │   ├── dynamic_pricing_service.py
│   │   ├── cart_management_service.py
│   │   ├── credit_system_service.py
│   │   ├── lead_review_service.py
│   │   ├── subscription_service.py
│   │   ├── ai_recommendations_service.py
│   │   ├── analytics_service.py
│   │   └── data_retention_service.py
│
│   ├── controllers/                 # API route definitions
│   │   ├── __init__.py
│   │   ├── lead_marketplace_controller.py
│   │   ├── dynamic_pricing_controller.py
│   │   ├── cart_management_controller.py
│   │   ├── credit_system_controller.py
│   │   ├── ai_recommendations_controller.py
│   │   └── market_insights_controller.py
│
│   ├── utils/                       # Helper utilities
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── validators.py
│   │   ├── pricing_helpers.py
│   │   └── geospatial_helpers.py
│
│   └── monitoring/                  # Monitoring and alerting tools
│       ├── __init__.py
│       ├── metrics_service.py       # Prometheus metrics integration
│       ├── alerts_service.py        # Slack or PagerDuty alerts
│       └── user_activity_monitor.py # Tracks user behavior

├── tests/                           # Automated tests
│   ├── unit/                        # Unit tests (mirrors src/)
│   ├── integration/                 # Integration tests
│   ├── e2e/                         # End-to-end tests
│   └── mocks/                       # Mock data and fixtures
│       ├── sample_leads.json
│       └── scraper_responses.json

└── frontend/                        # Frontend application (optional)
    ├── package.json
    ├── yarn.lock
    ├── public/
    └── src/
        ├── App.js
        ├── components/
        ├── pages/
        └── utils/

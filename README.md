# AIQLeads

## Overview
AIQLeads is an innovative lead marketplace designed for real estate professionals. It leverages advanced AI features to provide geospatial search, dynamic pricing, and AI-driven recommendations. The platform is optimized for efficient and scalable lead management, targeting high-demand real estate markets.

## Features
- **Geospatial Search**: Locate leads in specific geographic regions with precision.
- **Dynamic Pricing**: Automated pricing adjustments based on demand and availability.
- **AI-Driven Recommendations**: Personalized lead suggestions and fraud detection using advanced embeddings.
- **Cart Management**: Global and item-specific timers for lead reservations.

## Target Markets
- Las Vegas
- Dallas/Ft. Worth
- Austin
- Phoenix

## Folder Structure
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

├── docs/
│   ├── README.md
│   ├── MVP_Overview.md
│   ├── Architecture.md
│   ├── API_Reference.md
│   ├── DataFlow.md
│   ├── MarketInsights.md
│   ├── CHANGELOG.md
│   └── LEGAL/
│       ├── TermsOfService.md
│       └── PrivacyPolicy.md

├── scripts/
│   ├── deploy.sh
│   ├── seed_db.py
│   ├── infra/
│   │   └── terraform/
│   │       └── main.tf
│   └── ephemeral_env_setup.sh

├── migrations/
│   └── versions/
│       └── placeholder

├── src/
│   ├── __init__.py
│   ├── main.py
│
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres_manager.py
│   │   ├── redis_manager.py
│   │   ├── geospatial_manager.py
│   │   └── search_manager.py
│
│   ├── aggregator/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── scraper_utils.py
│   │   ├── scrapers/
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
│   │   ├── parsers/
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
│   │   └── exceptions.py
│
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_model.py
│   │   ├── lead_model.py
│   │   ├── transaction_model.py
│   │   ├── subscription_model.py
│   │   ├── market_insights_model.py
│   │   └── model_version_model.py
│
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   ├── lead_schema.py
│   │   ├── pricing_schema.py
│   │   ├── subscription_schema.py
│   │   └── model_version_schema.py
│
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_marketplace_service.py
│   │   ├── dynamic_pricing_service.py
│   │   ├── cart_management_service.py
│   │   ├── credit_system_service.py
│   │   ├── lead_review_service.py
│   │   ├── subscription_service.py
│   │   ├── ai_recommendations_service.py
│   │   ├── analytics_service.py
│   │   ├── data_retention_service.py
│   │   ├── marketing_service.py
│   │   └── ai_pipeline_manager.py
│
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── lead_marketplace_controller.py
│   │   ├── dynamic_pricing_controller.py
│   │   ├── cart_management_controller.py
│   │   ├── credit_system_controller.py
│   │   ├── subscription_controller.py
│   │   ├── market_insights_controller.py
│   │   └── ai_recommendations_controller.py
│
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── validators.py
│   │   ├── geospatial_helpers.py
│   │   └── pricing_helpers.py
│
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics_service.py
│   │   ├── alerts_service.py
│   │   └── user_activity_monitor.py
│
│   └── gateway/
│       ├── __init__.py
│       └── rate_limiting.py
│
├── tests/
│   ├── __init__.py
│   ├── mocks/
│   │   ├── sample_leads.json
│   │   ├── dummy_users.json
│   │   └── scraper_responses.json
│   ├── unit/
│   │   ├── test_linkedin_scraper.py
│   │   ├── test_linkedin_parser.py
│   │   └── ... (mirrors src structure)
│   ├── integration/
│   │   ├── test_aggregator_pipeline.py
│   │   └── ... (mirrors src structure)
│   └── e2e/
│       ├── test_lead_marketplace.py
│       └── ... (mirrors real user flows)
│
└── frontend/
    ├── package.json
    ├── yarn.lock
    ├── public/
    └── src/
        ├── App.js
        ├── components/
        ├── pages/
        └── utils/
```

## Getting Started

### Prerequisites
- Python 3.10+
- Docker (optional for containerized deployment)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YourlocalJay/AIQLeads.git
   cd AIQLeads
   ```

2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env` and update the values as needed.

### Running the Application
1. Run the FastAPI server locally:
   ```bash
   uvicorn src.main:app --reload
   ```

2. Access the API documentation:
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.

### Docker Deployment
1. Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

## Contribution
We welcome contributions to AIQLeads. Please review our [CONTRIBUTING.md](CONTRIBUTING.md) for details on the code of conduct and submission process.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, contact [YourlocalJay](mailto:your-email@example.com).

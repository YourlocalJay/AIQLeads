# AIQLeads Project Structure
```
AIQLeads/
│
├── backend/
│   ├── api/
│   │   ├── services/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── leads.py
│   │   │   ├── users.py
│   │   │   └── pricing.py
│   │   ├── middlewares/
│   │   │   ├── auth_middleware.py
│   │   │   └── rate_limiter.py
│   │   └── schemas/
│   │       ├── lead_schema.py
│   │       ├── user_schema.py
│   │       └── pricing_schema.py
│   │
│   ├── scrapers/
│   │   ├── zillow_scraper.py
│   │   ├── craigslist_scraper.py
│   │   └── mls_scraper.py
│   │
│   ├── ai/
│   │   ├── lead_scoring.py
│   │   ├── chatbot_nlp.py
│   │   └── recommendations.py
│   │
│   └── database/
│       ├── db_connection.py
│       └── models.py
│
├── frontend/
│   ├── components/
│   │   ├── LeadList.js
│   │   ├── LeadDetails.js
│   │   ├── Chatbot.js
│   │   ├── Dashboard.js
│   │   ├── Home.js
│   │   ├── Search.js
│   │   └── Pricing.js
│   │
│   ├── services/
│   │   ├── apiClient.js
│   │   └── auth.js
│   │
│   └── styles/
│       ├── main.css
│       └── theme.css
│
├── infrastructure/
│   ├── ci_cd/
│   │   └── github_actions.yml
│   ├── monitoring/
│   │   ├── prometheus_config.yml
│   │   └── grafana_dashboard.json
│   └── deployment/
│       ├── dockerfile
│       ├── compose.yml
│       ├── aws_lambda_config.json
│       └── kubernetes_config.yaml
│
├── config/
│   ├── config.py
│   └── settings.py
│
├── tests/
│   ├── backend/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── test_auth.py
│   │   │   │   ├── test_leads.py
│   │   │   │   ├── test_users.py
│   │   │   │   └── test_pricing.py
│   │   │   ├── middlewares/
│   │   │   │   ├── test_auth_middleware.py
│   │   │   │   └── test_rate_limiter.py
│   │   │   └── schemas/
│   │   │       ├── test_lead_schema.py
│   │   │       ├── test_user_schema.py
│   │   │       └── test_pricing_schema.py
│   │   │
│   │   ├── scrapers/
│   │   │   ├── test_zillow_scraper.py
│   │   │   ├── test_craigslist_scraper.py
│   │   │   └── test_mls_scraper.py
│   │   │
│   │   ├── ai/
│   │   │   ├── test_lead_scoring.py
│   │   │   ├── test_chatbot_nlp.py
│   │   │   └── test_recommendations.py
│   │   │
│   │   └── database/
│   │       ├── test_db_connection.py
│   │       └── test_models.py
│   │
│   ├── frontend/
│   │   ├── components/
│   │   │   ├── test_lead_list.py
│   │   │   ├── test_lead_details.py
│   │   │   ├── test_chatbot.py
│   │   │   ├── test_dashboard.py
│   │   │   ├── test_home.py
│   │   │   ├── test_search.py
│   │   │   └── test_pricing.py
│   │   │
│   │   └── services/
│   │       ├── test_api_client.py
│   │       └── test_auth.py
│   │
│   └── config/
│       ├── test_config.py
│       └── test_settings.py
│
├── scripts/
│   ├── data_migration.py
│   └── db_backup.py
│
└── docs/
    ├── README.md
    ├── API_DOCUMENTATION.md
    └── SCRAPING_GUIDE.md
```

## Key Components
- **Backend**: API services, routes, middlewares, scrapers, AI modules
- **Frontend**: React components, services, and styles
- **Infrastructure**: CI/CD, monitoring, and deployment configurations
- **Configuration**: Project settings and environment configs
- **Testing**: Comprehensive test suite with mirrored directory structure
- **Scripts**: Utility scripts for data management
- **Documentation**: Project and API documentation

## Testing Strategy
The test directory now mirrors the project's structure, ensuring:
- Each module has a corresponding test file
- Tests are organized in the same hierarchy as the source code
- Easy navigation and maintenance of test cases
- Clear mapping between source code and its tests
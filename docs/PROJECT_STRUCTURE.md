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
│   ├── test_routes.py
│   ├── test_scrapers.py
│   └── test_ai.py
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
- **Testing**: Comprehensive test suite
- **Scripts**: Utility scripts for data management
- **Documentation**: Project and API documentation

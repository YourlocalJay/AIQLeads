# AIQLeads MVP Implementation Roadmap

## Current Status

AIQLeads is currently ~50% complete. This roadmap outlines the steps required to fully implement the MVP, including a phase-by-phase breakdown and specific file updates/additions. By following this plan, AIQLeads will evolve into a robust real estate lead marketplace with advanced AI, geospatial analytics, dynamic pricing, and more.

## Current File Structure

```
AIQLeads/
├── .github/
│   ├── scripts/
│   │   └── update_files.py         # GitHub automation scripts
│   └── workflows/
│       ├── ci.yml                  # Continuous Integration workflow
│       ├── cd.yml                  # Continuous Deployment workflow
│       └── file-ops.yml            # File Operations workflow
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Environment configuration and logging
│   ├── database/
│   │   ├── __init__.py
│   │   └── postgres_manager.py     # Connection pooling and session management
│   ├── models/
│   │   ├── user_model.py           # User model with password policy
│   │   ├── lead_model.py           # Lead model with geospatial features
│   │   ├── transaction_model.py    # Transaction model with financial validation
│   │   └── subscription_model.py   # Subscription management with billing cycles
│   └── schemas/
│       ├── user_schema.py          # User request/response validation
│       ├── lead_schema.py          # Lead request/response validation
│       ├── transaction_schema.py   # Transaction request/response validation
│       └── subscription_schema.py  # Subscription request/response validation
└── tests/
    ├── database/
    │   └── test_postgres_manager.py
    ├── models/
    │   ├── test_user_model.py
    │   ├── test_lead_model.py
    │   ├── test_transaction_model.py
    │   └── test_subscription_model.py
    ├── scripts/
    │   ├── __init__.py
    │   └── test_update_files.py    # Tests for GitHub automation scripts
    └── workflows/
        ├── __init__.py
        ├── conftest.py             # Shared test fixtures
        ├── test_ci_workflow.py     # CI workflow tests
        └── test_cd_workflow.py     # CD workflow tests
```

---

## Implementation Phases

### PHASE 1: Expand the Aggregator & Data Ingestion

#### Tasks

1. **Add New Scrapers**
   - `src/aggregator/scrapers/linkedin_scraper.py`
   - `src/aggregator/scrapers/facebook_scraper.py`
   - Refine `src/aggregator/scraper_utils.py` with proxy rotation and error handling.
   - Create parsers for new scrapers:
     - `src/aggregator/parsers/linkedin_parser.py`
     - `src/aggregator/parsers/facebook_parser.py`
2. **Integrate New Scrapers**
   - Update `src/aggregator/pipeline.py` to include LinkedIn and Facebook scrapers.
   - Implement scheduling for regular scraper runs.
3. **Testing**
   - Add integration tests in `tests/integration/test_aggregator_pipeline.py`.

---

### PHASE 2: Search & Advanced Filtering

#### Tasks

1. **Search Manager**
   - Add `src/database/search_manager.py` for Elasticsearch/OpenSearch integration.
   - Implement lead indexing and updates for dynamic search results.
2. **Advanced Filtering**
   - Update `src/services/lead_marketplace_service.py` to enable text, filter-based, and geospatial searches.
   - Add new endpoints in `src/controllers/lead_marketplace_controller.py`.
3. **Testing**
   - Create `tests/integration/test_search_manager.py` and `tests/e2e/test_lead_search.py`.

---

### PHASE 3: AI Data Cleaning & Fraud Detection

#### Tasks

1. **LangChain Integration**
   - Implement `src/services/lead_validation_service.py` to normalize scraped data.
   - Integrate data cleaning pipeline into `src/aggregator/pipeline.py`.
2. **Fraud Detection**
   - Add fraud scoring to `src/models/lead_model.py`.
   - Enhance validation service to detect duplicate or suspicious leads.
3. **Testing**
   - Add `tests/unit/test_lead_validation_service.py` for fraud detection and data cleaning logic.

---

### PHASE 4: Dynamic Pricing Engine

#### Tasks

1. **Dynamic Pricing Service**
   - Create `src/services/dynamic_pricing_service.py` to calculate real-time lead prices.
   - Update `src/models/transaction_model.py` to track final sale prices.
2. **Testing**
   - Add unit tests in `tests/unit/test_dynamic_pricing_service.py`.
   - Verify real-time price updates in `tests/integration/test_pricing_logic.py`.

---

### PHASE 5: AI Recommendations

#### Tasks

1. **Embedding-Based Suggestions**
   - Configure Pinecone/Weaviate in `docker-compose.yml` or `.env`.
   - Generate embeddings in `src/services/ai_pipeline_manager.py`.
2. **Recommendation Service**
   - Add `src/services/ai_recommendations_service.py`.
   - Expose recommendations via `src/controllers/ai_recommendations_controller.py`.
3. **Testing**
   - Create `tests/integration/test_ai_recommendations_service.py`.

---

### PHASE 6: Finalize Cart Management

#### Tasks

1. **Per-Item Timers**
   - Update `src/services/cart_management_service.py` to track individual lead timers.
   - Add premium hold logic for Pro and Enterprise users.
2. **Testing**
   - Write tests in `tests/unit/test_cart_management_service.py`.

---

### PHASE 7: Market Insights & Analytics

#### Tasks

1. **Market Insights API**
   - Implement `src/services/analytics_service.py` for regional trends and data aggregation.
   - Create API endpoints in `src/controllers/market_insights_controller.py`.
2. **Testing**
   - Add unit tests in `tests/unit/test_analytics_service.py`.

---

### PHASE 8: Monitoring & Alerts

#### Tasks

1. **Metrics Collection**
   - Add Prometheus metrics in `src/monitoring/metrics_service.py`.
   - Create Grafana dashboards for key metrics (API performance, cart conversions).
2. **Alerting**
   - Add Slack/PagerDuty integration in `src/monitoring/alerts_service.py`.

---

### PHASE 9: Documentation & Deployment

#### Tasks

1. **Update Docs**
   - Revise `docs/Architecture.md`, `docs/MVP_Overview.md`, and OpenAPI specs.
   - Finalize deployment instructions in `docs/Usage.md`.
2. **Staging & Production Deployment**
   - Ensure CI/CD pipelines deploy stable builds to production.

---

## Progress Metrics

### Phase Completion

| Phase | Description                 | Completion |
|-------|-----------------------------|------------|
| 1     | Aggregator Expansion        | **50%**    |
| 2     | Search Integration          | **30%**    |
| 3     | AI Cleaning & Fraud Detection| **20%**    |
| 4     | Dynamic Pricing Engine      | **15%**    |
| 5     | AI Recommendations          | **10%**    |
| 6     | Cart Management             | **10%**    |
| 7     | Market Insights & Analytics | **5%**     |
| 8     | Monitoring & Alerts         | **0%**     |
| 9     | Documentation & Deployment  | **0%**     |

### Overall Project Completion: **45%**

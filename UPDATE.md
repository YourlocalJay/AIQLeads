# Implementation Tracker - AIQLeads Project

## Latest Updates (January 23, 2025)

### User Schema Enhancement Completion
- Implemented market-specific features in `user_schema.py`.
- Added notification preferences structure (JSONB) in `user_model.py`.
- Enhanced security tracking for login attempts and potential account lockouts.
- Integrated subscription and credit system fields into user model and schema.
- Improved phone number validation with format and country code support.

## Currently Implemented Components

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
│   │   ├── init.py
│   │   └── settings.py             # Environment configuration and logging
│   ├── database/
│   │   ├── init.py
│   │   └── postgres_manager.py     # Connection pooling and session management
│   ├── models/
│   │   ├── user_model.py           # User model with password policy
│   │   ├── lead_model.py           # Lead model with geospatial features
│   │   ├── transaction_model.py    # Transaction model with financial validation
│   │   ├── subscription_model.py   # Subscription management with billing cycles
│   │   └── market_insight_model.py # Analytics and insights engine
│   ├── controllers/
│   │   ├── market_insights_controller.py # Market insights API endpoints
│   │   └── lead_management_controller.py # Lead operations endpoints
│   └── schemas/
│       ├── user_schema.py          # User request/response validation with market integration
│       ├── lead_schema.py          # Lead request/response validation
│       ├── transaction_schema.py   # Transaction request/response validation
│       ├── subscription_schema.py  # Subscription request/response validation
│       └── market_insight_schema.py # Analytics data validation
└── tests/
├── database/
│   └── test_postgres_manager.py
├── models/
│   ├── test_user_model.py
│   ├── test_lead_model.py
│   ├── test_transaction_model.py
│   ├── test_subscription_model.py
│   └── test_market_insight_model.py
├── schemas/
│   ├── test_user_schema.py
│   ├── test_lead_schema.py
│   ├── test_transaction_schema.py
│   ├── test_subscription_schema.py
│   └── test_market_insight_schema.py
├── controllers/
│   ├── test_market_insights_controller.py
│   └── test_lead_management_controller.py
├── scripts/
│   ├── init.py
│   └── test_update_files.py   # Tests for GitHub automation scripts
└── workflows/
├── init.py
├── conftest.py            # Shared test fixtures
├── test_ci_workflow.py    # CI workflow tests
└── test_cd_workflow.py    # CD workflow tests

---

## Next Implementation Target

### Database Migration and API Integration

1. **Database Migration Updates**:
   - Create migration for enhanced user schema (add columns for market preferences, notification prefs, etc.).
   - Add indexes for market-specific queries to improve performance.
   - Implement notification preferences table if additional structure is needed.
   - Add security tracking fields (e.g., `failed_login_attempts`, `account_locked_until`).

2. **API Integration**:
   - Update user endpoints for market preferences (`preferred_market`).
   - Implement notification settings endpoints for user preferences.
   - Add subscription status endpoints to reflect fields in `subscription_model.py`.
   - Create market access validation middleware if certain features are region-locked.

3. **Testing Requirements**:
   - Add integration tests for new user features (notifications, market preference).
   - Implement market-specific validation tests in `user_schema.py`.
   - Add subscription integration tests for new fields.
   - Create performance benchmarks for market queries and new indexes.

---

## Progress Metrics

| Phase | Description                  | Completion |
|-------|------------------------------|------------|
| 0     | Scope & Repo Initialization  | 100%       |
| 1     | Infrastructure Setup         | 100%       |
| 2     | Database Models & Schemas    | 100%       |
| 3     | Market Insights Pipeline     | 85%        |
| 4     | API Layer Development        | 30%        |
|       | **Overall Project Completion** | **75%**  |

---

# **Phase-by-Phase & File-by-File Implementation Plan**

Below is the **detailed roadmap** for taking the AIQLeads MVP from ~75% completion to full feature parity, including **advanced scraping**, **dynamic pricing**, **AI recommendations**, **fraud detection**, and **monitoring**.

---

## **PHASE 1: Expand the Aggregator & Data Ingestion**

1. **Add New Scrapers**  
   - **File(s):**  
     - `src/aggregator/scrapers/linkedin_scraper.py`  
     - `src/aggregator/scrapers/facebook_scraper.py`  
   - **Description:**  
     - Implement scraping logic for LinkedIn and Facebook Marketplace.  
     - Reuse patterns from Zillow/Craigslist scrapers in `scraper_utils.py`.

2. **Integrate Scrapers into Pipeline**  
   - **File(s):**  
     - `src/aggregator/pipeline.py`  
   - **Description:**  
     - Add tasks for new scrapers.  
     - Schedule them to run daily or hourly.  
     - Verify aggregator flow in `tests/integration/test_aggregator_pipeline.py`.

---

## **PHASE 2: Search & Advanced Filtering (Elasticsearch/OpenSearch)**

1. **Search Manager & Indexing**  
   - **File(s):**  
     - `src/database/search_manager.py` (create if missing)  
     - `docker-compose.yml` (add Elasticsearch service)  
   - **Description:**  
     - Implement indexing of leads into ES/OpenSearch.  
     - Sync updates when lead prices or availability change.

2. **Advanced Filtering & Radius Searches**  
   - **File(s):**  
     - `src/services/lead_marketplace_service.py`  
     - `src/controllers/lead_management_controller.py`  
   - **Description:**  
     - Integrate ES queries for text/faceted search.  
     - Combine PostGIS or ES geospatial filters for radius-based searching.  
     - Add tests to `tests/e2e/` ensuring queries match expected results.

---

## **PHASE 3: AI Data Cleaning & Fraud Detection**

1. **LangChain Integration for Data Cleaning**  
   - **File(s):**  
     - `src/services/lead_validation_service.py` (new)  
     - `src/aggregator/pipeline.py` (update)  
   - **Description:**  
     - Use LLM (OpenAI) to normalize addresses, correct common data errors.  
     - Log or skip leads with irreparable data.

2. **Fraud Detection & Duplicate Checks**  
   - **File(s):**  
     - `src/services/lead_validation_service.py` (extend)  
     - `src/models/lead_model.py` (ensure `fraud_score` field)  
   - **Description:**  
     - Mark duplicates across multiple scrapers.  
     - Assign a `fraud_score`; hide or flag leads above a threshold.

---

## **PHASE 4: Dynamic Pricing Engine**

1. **Pricing Logic Service**  
   - **File(s):**  
     - `src/services/dynamic_pricing_service.py` (new)  
   - **Description:**  
     - Calculate lead prices based on demand, property quality, time-on-market, subscription tier.  
     - Apply discounts for Pro/Enterprise users.

2. **Real-Time Updates**  
   - **File(s):**  
     - `src/aggregator/pipeline.py` (or separate cron job)  
     - `src/controllers/dynamic_pricing_controller.py` (if needed)  
   - **Description:**  
     - Recompute prices on schedule or aggregator run.  
     - Ensure updated price is visible to users in real-time.

---

## **PHASE 5: AI Recommendations**

1. **Vector Database & Embedding Generation**  
   - **File(s):**  
     - `docker-compose.yml` (add Pinecone/Weaviate if self-hosting)  
     - `src/services/ai_pipeline_manager.py` (new or expand existing)  
   - **Description:**  
     - Generate embeddings (OpenAI or huggingface) for each lead.  
     - Store them in a vector DB for similarity searches.

2. **Recommendation Flow**  
   - **File(s):**  
     - `src/services/ai_recommendations_service.py` (new)  
     - `src/controllers/ai_recommendations_controller.py` (new)  
   - **Description:**  
     - For each user, gather preference vectors from purchase history.  
     - Return top similar leads with geo or tier-based filtering.

---

## **PHASE 6: Finalize Cart Management & Premium Extensions**

1. **Per-Item Timers & Extended Holds**  
   - **File(s):**  
     - `src/services/cart_management_service.py`  
     - `src/controllers/lead_management_controller.py` (or separate `cart_controller.py`)  
   - **Description:**  
     - Store item-level timers in Redis.  
     - Let Pro/Enterprise users extend holds (24 hrs, 3 days, 7 days).

2. **Notifications on Timer Expiry**  
   - **File(s):**  
     - `src/services/cart_management_service.py` (extend)  
   - **Description:**  
     - Email or in-app alerts when timers near expiration.  
     - Log cart events for analytics.

---

## **PHASE 7: Advanced Analytics & Market Insights**

1. **Market Insights API**  
   - **File(s):**  
     - `src/services/analytics_service.py` (new or expand)  
     - `src/controllers/market_insights_controller.py` (extend)  
   - **Description:**  
     - Aggregate median prices, lead demand, popular property features.  
     - Provide region-specific stats (Las Vegas, Austin, etc.).

2. **Geospatial Analytics**  
   - **File(s):**  
     - `src/models/market_insight_model.py` (fields to store aggregates)  
     - `src/utils/geospatial_helpers.py` (optional)  
   - **Description:**  
     - Use PostGIS to compute location-based stats.  
     - Possibly generate heatmaps or neighborhood-level breakdowns.

---

## **PHASE 8: Payment Gateway Enhancements & Refund Handling**

1. **Automated Subscription Renewals**  
   - **File(s):**  
     - `src/services/subscription_service.py` (extend)  
     - `src/controllers/subscription_controller.py`  
   - **Description:**  
     - Handle monthly/annual auto-renew with Stripe/PayPal webhooks.  
     - Update user subscription status, credit balances upon renewal.

2. **Refund Workflows & Invoices**  
   - **File(s):**  
     - `src/services/payment_service.py` (create or expand)  
     - `src/models/transaction_model.py` (refund fields)  
   - **Description:**  
     - Provide partial/full refunds for invalid leads or disputes.  
     - Generate invoices/receipts for user transactions.

---

## **PHASE 9: Monitoring & Alerts**

1. **Metrics & Dashboards**  
   - **File(s):**  
     - `src/monitoring/metrics_service.py` (new)  
     - `docker-compose.yml` (add Prometheus/Grafana)  
   - **Description:**  
     - Collect aggregator throughput, API performance, cart conversion rates.  
     - Visualize data in Grafana dashboards.

2. **Alerting**  
   - **File(s):**  
     - `src/monitoring/alerts_service.py` (new)  
   - **Description:**  
     - Slack or PagerDuty alerts for scraper failures, high error rates, payment gateway issues.  
     - Admin notification if system hits performance thresholds.

---

## **PHASE 10: API Gateway, Rate Limiting & Security**

1. **Public & Private API**  
   - **File(s):**  
     - `src/gateway/rate_limiting.py` (or external Kong/NGINX config)  
   - **Description:**  
     - Implement rate limits (e.g., 100 requests/min for Basic, 500 for Pro).  
     - Add token-based or OAuth2 auth for enterprise integrations.

2. **API Security & Documentation**  
   - **File(s):**  
     - `src/main.py` / `src/controllers/*`  
     - `docs/API_Reference.md` (update)  
   - **Description:**  
     - Ensure JWT-based auth for sensitive routes.  
     - Finalize OpenAPI docs for all endpoints.  
     - Possibly add IP allowlist or advanced firewall rules for private APIs.

---

## **PHASE 11: Final Polish & Documentation**

1. **Code Cleanup & E2E Tests**  
   - **File(s):**  
     - `tests/e2e/` (create or expand end-to-end test files)  
   - **Description:**  
     - Simulate full user workflow: sign up, search leads, add to cart, buy, check recommendations.  
     - Clean up logs, remove dead code, ensure consistent naming.

2. **Documentation & README**  
   - **File(s):**  
     - `docs/MVP_Overview.md`  
     - `docs/Architecture.md`  
     - `CHANGELOG.md`  
   - **Description:**  
     - Update all references with new scrapers, dynamic pricing, AI features.  
     - Record each release or major change in the changelog.

---

## Conclusion

By following this **11-phase** plan, you’ll evolve AIQLeads from its current 75% state to a **fully realized lead marketplace**, complete with:

- **AI-driven recommendations**  
- **Dynamic pricing**  
- **Comprehensive fraud detection**  
- **Advanced analytics**  
- **Robust cart & subscription features**  
- **Secure, monitored APIs**

Each phase includes **file-by-file** guidance to keep implementation organized, tested, and well-documented.

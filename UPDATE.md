### AIQLeads MVP Development Plan and Progress Tracker

#### Overview
This document provides a detailed breakdown of tasks for completing the AIQLeads MVP. It specifies all files being created or modified with their full paths, benchmarks for testing, and clear tracking of completed tasks. Testing information is included for every phase, with paths to test files and specific benchmarks for validation. All contributors must update this document before proceeding with new tasks.

---

### Phase 0: Define Scope & Repository Initialization
**Steps:**
1. Finalize MVP requirements, including:
   - LLM-based pricing and recommendations.
   - Multi-tier credit system.
   - Fraud detection.
   - Geospatial queries.
   - Advanced cart management.
2. Create GitHub repository with initial directory structure:
   - **Full Paths:**
     - `.github/workflows/ci.yml`
     - `.github/workflows/cd.yml`
     - `.gitignore`
     - `LICENSE`
     - `README.md`
     - `docs/MVP_Overview.md`
     - `docs/Architecture.md`
     - `docs/MarketInsights.md`
3. Push an initial commit.

**Testing Information:**
- Ensure initial CI pipeline tests pass.
  - **Full Paths:**
    - `tests/unit/test_ci_pipeline.py`

**Benchmarks:**
- Repository must include all required files.
- CI/CD workflows must pass a basic pipeline test (linting and build).

**Completion Metrics:**
- Tasks Completed: 4/4
- Phase Completion: 100%
- Overall Completion: 8.33%

---

### Phase 1: Environment, CI/CD, and Base Infrastructure
**Steps:**
1. Set up Python environment with necessary libraries.
   - **Full Paths:**
     - `requirements.txt`
     - `.env.example`
2. Create Dockerfile and docker-compose.yml.
   - **Full Paths:**
     - `Dockerfile`
     - `docker-compose.yml`
3. Add GitHub Actions workflows for CI/CD.
   - **Full Paths:**
     - `.github/workflows/ci.yml`
     - `.github/workflows/cd.yml`
4. Test environment setup and container builds.

**Testing Information:**
- Test containerized services and environment setup.
  - **Full Paths:**
    - `tests/integration/test_docker_setup.py`

**Benchmarks:**
- Docker containers must build and run without errors.
- GitHub Actions workflows must successfully execute.

**Completion Metrics:**
- Tasks Completed: 0/4
- Phase Completion: 0%
- Overall Completion: 0%

---

### Phase 2: Database Schema & Core Models
**Steps:**
1. Define database models for:
   - Users
     - **Full Paths:** `src/models/user_model.py`
   - Leads
     - **Full Paths:** `src/models/lead_model.py`
   - Transactions
     - **Full Paths:** `src/models/transaction_model.py`
   - Subscriptions
     - **Full Paths:** `src/models/subscription_model.py`
   - Market Insights
     - **Full Paths:** `src/models/market_insights_model.py`
2. Enable PostGIS and add geospatial fields to LeadModel.
3. Write initial Alembic migrations.
   - **Full Paths:**
     - `migrations/versions/initial_migration.py`
4. Test basic CRUD operations.

**Testing Information:**
- Validate CRUD operations for all models.
  - **Full Paths:**
    - `tests/unit/test_user_model.py`
    - `tests/unit/test_lead_model.py`
    - `tests/unit/test_transaction_model.py`
    - `tests/unit/test_subscription_model.py`
    - `tests/unit/test_market_insights_model.py`
- Test Alembic migrations.
  - **Full Paths:**
    - `tests/integration/test_alembic_migrations.py`

**Benchmarks:**
- Database tables created and verified.
- CRUD tests pass for all models.

**Completion Metrics:**
- Tasks Completed: 0/4
- Phase Completion: 0%
- Overall Completion: 0%

---

### Phase 3: Aggregator Pipeline with Scrapers, Parsers, and AI Data Cleaning
**Steps:**
1. Implement base scraper utilities:
   - **Full Paths:**
     - `src/aggregator/scraper_utils.py`
2. Develop scrapers for:
   - Craigslist
     - **Full Paths:** `src/aggregator/scrapers/craigslist_scraper.py`
   - Zillow
     - **Full Paths:** `src/aggregator/scrapers/zillow_scraper.py`
   - Facebook
     - **Full Paths:** `src/aggregator/scrapers/facebook_scraper.py`
   - LinkedIn
     - **Full Paths:** `src/aggregator/scrapers/linkedin_scraper.py`
3. Create parsers to clean and normalize data:
   - Craigslist Parser
     - **Full Paths:** `src/aggregator/parsers/craigslist_parser.py`
   - Zillow Parser
     - **Full Paths:** `src/aggregator/parsers/zillow_parser.py`
4. Build aggregator pipeline.
   - **Full Paths:** `src/aggregator/pipeline.py`
5. Integrate LangChain/OpenAI for AI-assisted data cleaning.
   - **Full Paths:**
     - `src/services/ai_data_cleaning_service.py`

**Testing Information:**
- Unit test scrapers and parsers.
  - **Full Paths:**
    - `tests/unit/test_craigslist_scraper.py`
    - `tests/unit/test_zillow_scraper.py`
    - `tests/unit/test_facebook_scraper.py`
    - `tests/unit/test_linkedin_scraper.py`
    - `tests/unit/test_parsers.py`
- Test aggregator pipeline end-to-end.
  - **Full Paths:**
    - `tests/e2e/test_aggregator_pipeline.py`

**Benchmarks:**
- Scrapers retrieve data without errors.
- Parsers correctly clean and normalize data.
- Aggregator pipeline processes data end-to-end.

**Completion Metrics:**
- Tasks Completed: 0/5
- Phase Completion: 0%
- Overall Completion: 0%

---

### Phase 4: ElasticSearch & Advanced Search API
**Steps:**
1. Index leads in Elasticsearch.
   - **Full Paths:** `src/services/elasticsearch_service.py`
2. Implement advanced search APIs.
   - **Full Paths:**
     - `src/controllers/search_controller.py`
     - `src/schemas/search_schema.py`
3. Test search functionalities with filters.

**Testing Information:**
- Test Elasticsearch indexing and queries.
  - **Full Paths:**
    - `tests/integration/test_elasticsearch_service.py`
    - `tests/unit/test_search_controller.py`

**Benchmarks:**
- Leads indexed and searchable in Elasticsearch.
- Search APIs return accurate results.

**Completion Metrics:**
- Tasks Completed: 0/3
- Phase Completion: 0%
- Overall Completion: 0%

---

### Usage Instructions
- **Review Before Proceeding:** Use this document to verify progress and identify pending tasks.
- **Update Before Continuing:** Always log completed tasks and adjust completion metrics.
- **Benchmarks:** Ensure all specified benchmarks are tested and verified before advancing.

---


# AIQLeads Technical Architecture

## 1. High-Level Overview
AIQLeads is built on a **microservices-inspired** model within a single repository. It uses:
- **FastAPI** for backend REST and WebSocket endpoints.
- **PostgreSQL** (with PostGIS) for lead storage, user data, and geospatial queries.
- **Redis** for caching cart timers and real-time data (e.g., lead availability).
- **Elasticsearch/OpenSearch** for advanced text and faceted search.
- **LangChain** and LLMs (OpenAI, Anthropic) for AI-based recommendations, data cleaning, and dynamic pricing.

### Core Components
1. **Aggregator**  
   - Scrapers/parsers for Zillow, Craigslist, FSBO, Facebook, plus region-specific scraping logic.  
   - Cleans, validates, and enriches data before storing in PostgreSQL.
2. **Services**  
   - **lead_marketplace_service**: Queries leads, handles filtering, orchestrates geospatial + ES search.  
   - **dynamic_pricing_service**: Uses AI or rules to update lead prices in real time.  
   - **cart_management_service**: Manages timers, reservations, and premium hold extensions.  
   - **credit_system_service**: Handles user credits, purchasing, and subscription tiers.  
   - **ai_recommendations_service**: Embedding-based suggestions for lead personalization.  
   - **lead_validation_service**: Fraud scoring, data cleaning, anomaly detection.
3. **Controllers**  
   - FastAPI endpoints for each business function: leads, pricing, cart, subscriptions, recommendations.
4. **Monitoring**  
   - **metrics_service** for Prometheus/Grafana metrics.  
   - **alerts_service** for Slack/PagerDuty alerts on system failures.

---

## 2. Data Flow

1. **Scraping**  
   - Periodic or on-demand scripts pull raw property data from multiple sources.  
   - Data is partially cleaned at the scraper level (e.g., removing obvious duplicates).

2. **AI Cleaning & Validation**  
   - `lead_validation_service` calls an LLM (via LangChain) to normalize addresses, fix price strings, and detect fraud indicators.  
   - Assigns `fraud_score` and `quality_score`.

3. **Database Ingestion**  
   - Valid leads are stored in PostgreSQL.  
   - Geospatial columns let us run queries like “find leads within 10 miles of downtown Dallas.”

4. **Search Indexing**  
   - Leads are indexed in Elasticsearch for text/faceted searches (e.g., “2 bed, 2 bath condo near UT Austin”).

5. **AI Recommendations**  
   - Embeddings (OpenAI `text-embedding-ada-002`, or similar) are generated.  
   - Stored in Pinecone, Weaviate, or as vectors in Postgres.  
   - `ai_recommendations_service` retrieves similar leads when a user requests personalized suggestions.

6. **Dynamic Pricing**  
   - The system adjusts lead prices based on supply/demand, lead quality, user tier.  
   - Pricing updates are reflected in the front-end UI or returned via API calls.

7. **Cart & Purchase Flow**  
   - Users add leads to their cart, triggering timers (15 min global, 5 min per item).  
   - Premium users can extend hold time.  
   - Credit balances are reduced upon lead purchase.

---

## 3. System Components & Interactions

```mermaid
flowchart LR
    A[Scrapers] -- raw leads --> B[AI Data Cleaning & Fraud Check]
    B -- validated leads --> C[PostgreSQL + PostGIS]
    C -- indexing --> D[Elasticsearch]
    C -- geospatial queries --> E[Lead Marketplace Service]
    D -- text/faceted search --> E
    E -- dynamic pricing requests --> F[Dynamic Pricing Service]
    E -- recommendations --> G[AI Recommendations Service]
    G -- embedding retrieval --> H[Pinecone / Weaviate / Vector DB]
    E -- user requests / cart mgmt --> I[FastAPI Controllers]
    I -- purchase flow --> J[Credit System]
    J -- updates balance --> C
    E -- metrics --> K[Monitoring/Alerts]

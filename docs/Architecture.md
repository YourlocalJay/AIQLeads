# AIQLeads Architecture

## 1. High-Level Design

AIQLeads uses a **modular, service-oriented approach** within a single repository, allowing each major feature to be developed and tested independently. 

### Key Components
1. **Data Aggregation (Scrapers & Parsers)**  
   - Pulls leads from multiple sources (Zillow, Craigslist, Facebook, FSBO, LinkedIn).  
   - Region-specific scrapers for Las Vegas, Dallas/Ft. Worth, Austin, Phoenix.
2. **AI Services**  
   - Data cleaning, fraud detection, dynamic pricing, and lead recommendations using LLMs and vector databases.
3. **Core Services**  
   - **Cart Management**, **Credit System**, **Subscription Tiers**, and **Market Insights**.  
4. **Storage & Search**  
   - **PostgreSQL** with **PostGIS** for geospatial queries.  
   - **Redis** for in-memory caching and cart timers.  
   - **Elasticsearch** (or OpenSearch) for advanced text/faceted search.
5. **Monitoring & Alerts**  
   - **Prometheus/Grafana** for metrics.  
   - **alerts_service.py** for notifications on scraper downtime or system errors.

---

## 2. Data Flow

```mermaid
flowchart LR
    A[Scrapers] --> B[AI Data Cleaning & Fraud Detection]
    B --> C[PostgreSQL + PostGIS]
    C --> D[Elasticsearch] 
    C --> E[Lead Marketplace Service]
    D --> E
    E --> F[Dynamic Pricing Service]
    E --> G[AI Recommendations Service]
    G --> H[Vector DB (Pinecone/Weaviate)]
    E --> I[Cart & Payment Flows]
    I --> J[Credit System Service]
    E --> K[Monitoring & Alerts]

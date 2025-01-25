# AIQLeads: Real Estate Lead Marketplace

AIQLeads is a cutting-edge lead marketplace designed to help real estate professionals efficiently acquire high-quality, region-specific leads. Targeting high-demand regions such as Las Vegas, Austin, Phoenix, and Dallas/Ft. Worth, AIQLeads combines scraping, data validation, geospatial analytics, and credit-based purchasing to provide real estate agents with the tools they need to stay competitive.

## MVP Overview
The AIQLeads MVP prioritizes automation, scalability, and simplicity while minimizing operational overhead. The platform features:

1. **Lead Marketplace**
   - Aggregates leads from multiple sources, including Zillow, Craigslist, FSBO.com, and Facebook Marketplace.
   - Advanced filtering and search capabilities powered by Elasticsearch.
   - Rule-based dynamic pricing and geospatial search functionality.

2. **Dynamic Pricing**
   - Pricing adjusts based on lead quality, demand, and region-specific trends.
   - Rule-based logic replaces ML models in Phase 1 for simplicity.

3. **Credit-Based Purchasing**
   - Multi-tier subscription system (Basic, Pro, Enterprise).
   - Real-time credit tracking and transaction history.

4. **AI-Powered Features**
   - Simplified recommendations based on user behavior and location preferences.
   - Heuristic fraud detection and data validation.

5. **Monitoring and Alerts**
   - Real-time rate limiter metrics and failover handling.
   - Prometheus/Grafana integration for system monitoring.

---

## Core Features

### **Scraping & Data Aggregation**
- **Sources**: Supports Zillow, Craigslist, Facebook Marketplace, FSBO.com, and LinkedIn.
- **Pipeline**: Scraped data flows through a centralized pipeline for parsing, validation, and storage.
- **Rate Limiting**: Built-in rate limiting ensures compliance with source restrictions.

### **Dynamic Pricing System**
- Rule-based adjustments for lead pricing based on:
  - Demand (views, cart additions, purchases).
  - Regional market conditions.
  - Subscription tier discounts.

### **Credit System & Cart Management**
- Users purchase leads using credits.
- Cart timers ensure fairness and encourage timely decisions.
- Premium users can hold leads longer or purchase cart extensions.

### **Geospatial Analytics**
- **PostGIS Integration**:
  - Radius-based and polygon-based lead searches.
  - Visualize leads on an interactive map (front-end dependent).

### **Fraud Detection & Validation**
- Heuristic-based methods for:
  - Duplicate detection (addresses, phone numbers).
  - Mismatched data identification.
- LLM-powered data cleaning for standardizing fields.

### **Monitoring & Metrics**
- Prometheus and Grafana dashboards.
- Metrics include API response times, scraper success rates, and lead purchase conversions.
- Alerts for scraper failures, rate-limiting issues, and payment errors.

---

## Architecture Overview
The AIQLeads architecture is built for scalability and modularity:

- **Backend**:
  - FastAPI for API development.
  - PostgreSQL with PostGIS for relational and geospatial data.
  - Elasticsearch for advanced search and filtering.
  - Redis for caching and cart timers.
- **AI Integration**:
  - LangChain for data cleaning and basic heuristic recommendations.
- **Infrastructure**:
  - Dockerized services.
  - CI/CD pipelines via GitHub Actions.
  - Monitoring with Prometheus/Grafana.

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YourlocalJay/AIQLeads.git
   cd AIQLeads
   ```

2. **Setup Environment**:
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Create a `.env` file based on `.env.example`:
     ```bash
     cp .env.example .env
     ```
   - Configure database and API keys in `.env`.

3. **Run Services**:
   - Start the application:
     ```bash
     docker-compose up --build
     ```
   - Access the FastAPI UI at [http://localhost:8000/docs](http://localhost:8000/docs).

4. **Database Migrations**:
   - Run migrations:
     ```bash
     alembic upgrade head
     ```

---

## Contributing

We welcome contributions to AIQLeads! To get started:
1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

---

## Roadmap

- **Phase 1**:
  - Complete pipeline integration for all supported sources.
  - Finalize dynamic pricing logic.
  - Launch MVP with core features.
- **Phase 2**:
  - Add advanced AI-powered recommendations.
  - Expand geospatial analytics.
  - Introduce API integrations for enterprise clients.

---

## License

AIQLeads is licensed under the MIT License. See `LICENSE` for details.

---

## Contact

For questions or support, please contact:
- **GitHub**: [YourlocalJay](https://github.com/YourlocalJay)
- **Email**: support@aiqleads.com
---

## License
This project is licensed under the MIT License. See `LICENSE` for details.

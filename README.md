# AIQLeads

## Overview
AIQLeads is an advanced lead marketplace designed for real estate professionals, offering AI-driven lead recommendations, dynamic pricing, and geospatial analytics. Targeted at high-demand regions such as Las Vegas, Dallas/Ft. Worth, Austin, and Phoenix, AIQLeads leverages cutting-edge technology to provide high-quality leads tailored to user preferences.

---

## Features
### Lead Marketplace
- Aggregates leads from Zillow, Craigslist, Facebook Marketplace, FSBO.com, and LinkedIn.
- Supports advanced filtering (location, price, property type, features).
- Powered by Elasticsearch for full-text and faceted search.

### AI-Powered Recommendations
- Personalized suggestions using OpenAI embeddings.
- Real-time updates based on user behavior and lead availability.

### Dynamic Pricing
- Prices adapt based on demand, lead quality, and market trends.
- Discounts available for Pro and Enterprise subscription tiers.

### Multi-Tier Credit System
- Credits enable lead purchasing.
- Subscription tiers: Basic, Pro, and Enterprise, offering different features and discounts.

### Advanced Cart Management
- Timed reservations per lead.
- Extended hold options for premium users.

### Fraud Detection & Data Cleaning
- AI-powered validation for lead quality.
- Duplicate and fraudulent lead detection.

### Analytics & Insights
- Real-time regional trends and demand heatmaps.
- Geospatial analytics integrated with PostGIS.

---

## Installation

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL with PostGIS
- Redis
- Elasticsearch or OpenSearch

### Steps
1. **Clone the Repository**
   ```bash
   git clone https://github.com/YourlocalJay/AIQLeads.git
   cd AIQLeads
   ```

2. **Set Up Environment Variables**
   - Copy `.env.example` to `.env` and fill in the necessary values.

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Docker Services**
   ```bash
   docker-compose up --build
   ```

5. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the Application**
   ```bash
   uvicorn src.main:app --reload
   ```

---

## Usage

### Local Development
- Access the API documentation at `http://localhost:8000/docs`.
- Monitor logs for debugging with `docker logs -f <container_name>`.

### Testing
- Run tests using `pytest`:
   ```bash
   pytest
   ```

### Deployment
- Use the provided `ci.yml` and `cd.yml` workflows for continuous integration and deployment.

---

## Roadmap

### Q1 2025
- Complete API integration framework.
- Enhance testing to 95% coverage.
- Finalize monitoring dashboards.

### Q2 2025
- Implement real-time analytics.
- Launch recommendation engine.
- Expand market coverage.

---

## Contributing
We welcome contributions! Please review `CONTRIBUTING.md` for guidelines.

---

## License
This project is licensed under the MIT License. See `LICENSE` for details.

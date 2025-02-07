# AIQLeads MVP Technical Documentation

**Version:** 1.0  
**Date:** February 7, 2025  
**Author:** AIQLeads Dev Team

## 1. System Overview

### 1.1 Purpose & Functionality

**AIQLeads** is a fully automated, AI-powered real estate lead generation and marketplace platform that:
- **Scrapes** various sources (FSBO sites, Craigslist, Facebook Marketplace, MLS, etc.) to gather potential property leads.
- **Enriches & Scores** leads using advanced AI models (e.g., OpenAI GPT-4o, DeepSeek).
- **Dynamically Prices & Lists** leads on an online marketplace for real estate agents and brokers.
- **Automates Lead Distribution** and communication through an AI-powered chatbot (Mistral).

The goal is to minimize operator intervention (aiming for 90%+ automation) while ensuring scalability and efficiency in generating and selling high-quality real estate leads.

### 1.2 High-Level Workflow

1. **Scrape & Ingest:**
   - Asynchronous crawlers fetch data from multiple real estate sources.
   - Data is normalized and deduplicated to ensure uniqueness.

2. **Lead Enrichment & Scoring:**
   - Utilizes DeepSeek for property context and GPT-4o for data interpretation/scoring.
   - Pinecone vector embeddings support quick similarity searches (e.g., duplicate detection or matching leads to agent preferences).

3. **Dynamic Pricing & Marketplace:**
   - AI-based price recommendations adjust pricing based on location, property attributes, and market trends.
   - Leads are listed on the Marketplace with dynamic pricing that adjusts in real time.

4. **Agent Chatbot & Analytics:**
   - An AI chatbot (Mistral + LangChain) provides agents with lead insights and guided tours.
   - Market analytics (DeepSeek + Qwen time-series modeling) offer predictive insights on local real estate trends.

5. **Purchase & Delivery:**
   - Agents purchase leads via Stripe or PayPal; lead details are unlocked upon payment.
   - Automated notifications and engagement scripts help convert leads into actual listings or closed deals.

## 2. Project Directory & File Breakdown

```plaintext
AIQLeads/
├── README.md                    # Overview, Quickstart, and onboarding materials
├── .env.example                 # Environment variable template (copy to .env)
├── backend/                     # FastAPI backend (APIs, business logic)
│   ├── main.py                  # API entry point & app setup
│   ├── dependencies.py          # Dependency injection (DB, AI models, etc.)
│   ├── config.py                # Global configuration (env vars, feature flags)
│   ├── routes/                  # API route definitions
│   │   ├── auth.py              # Authentication (login, registration, MFA)
│   │   ├── leads.py             # Lead creation, retrieval, assignment
│   │   ├── analytics.py         # Reporting, KPI tracking, usage stats
│   │   ├── marketplace.py       # Public listing & dynamic pricing
│   │   └── payments.py          # Payment processing (Stripe/PayPal)
│   ├── models/                  # SQLAlchemy/SQLModel DB models
│   ├── controllers/             # Business logic & orchestration
│   ├── schemas/                 # Pydantic models for validation
│   ├── security/                # Authentication and RBAC utilities
│   ├── database/                # DB connections & migration scripts
│   ├── logging/                 # Structured logging configuration
│   ├── workers/                 # Background tasks (Celery)
│   └── utils/                   # Shared helpers & feature flag logic
├── ai_models/                   # AI/ML components
│   ├── lead_scoring.py          # Lead scoring using GPT-4o + DeepSeek
│   ├── recommendation.py        # Agent-property matching (vector search)
│   ├── chatbot.py               # Mistral-based chatbot with LangChain
│   ├── embeddings.py            # Text embedding functions
│   ├── market_analysis.py       # Predictive analysis (DeepSeek + Qwen)
│   └── training/                # Model training pipeline
├── scraping/                    # Web scraping & data parsing
│   ├── fsbo_scraper.py          # FSBO listings scraper
│   ├── craigslist_scraper.py    # Craigslist scraper
│   ├── facebook_scraper.py      # Facebook Marketplace scraper
│   ├── parser.py                # Data normalization
│   └── deduplication.py         # Duplicate lead removal
├── services/                    # Third-party integrations
│   ├── mls_api.py               # MLS data fetching
│   ├── zillow_api.py            # Zillow market data
│   ├── stripe_service.py        # Payment processing
│   ├── email_service.py         # Transactional emails
│   └── chatbot_service.py       # Chatbot interface
├── deployment/                  # Deployment configurations
│   ├── Dockerfile               # Multi-stage Docker build
│   ├── docker-compose.yml       # Local orchestration
│   ├── k8s/                     # Kubernetes manifests
│   └── github_actions/          # CI/CD workflows
└── tests/                       # Testing suite
```

## 3. AI Model Integration

### 3.1 Lead Scoring
- **Models Used:**
  - GPT-4o for advanced language reasoning
  - DeepSeek for domain-specific real estate intelligence
- **Process:**
  1. Scrape lead data → Parse & Clean → Score using AI models
  2. Categorize leads (premium, standard, low priority)
- **Cost Optimization:**
  - Batch processing every 15 minutes
  - Fallback logic for quota management

### 3.2 Market Analysis
- **Models Used:**
  - DeepSeek for predictive pricing
  - Qwen for time-series modeling
- **Functionality:**
  - Price trend forecasting
  - Dynamic pricing adjustments
- **Processing:**
  - Batch ingestion for macro trends
  - Real-time queries for high-demand areas

### 3.3 Chatbot System
- **Technology Stack:**
  - Mistral base model
  - LangChain for orchestration
- **Features:**
  - Lead insights and guided tours
  - Conversation history tracking
  - Performance monitoring

### 3.4 Vector Storage
- **Platform:** Pinecone
- **Use Cases:**
  - Duplicate detection
  - Lead-agent matching
  - Similar property search
- **Optimization:**
  - Regular embedding updates
  - Query caching
  - Cost monitoring

## 4. Security & Compliance

### 4.1 Authentication & RBAC
- JWT-based authentication
- Role-based access control
- Optional MFA for sensitive operations

### 4.2 Data Protection
- Encryption at rest and in transit
- PII data handling compliance
- Audit logging for sensitive operations

### 4.3 Security Measures
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection
- CORS configuration

## 5. Development Guidelines

### 5.1 Code Standards
- Type hints required
- Docstring documentation
- Unit test coverage
- Code review process

### 5.2 Best Practices
- Async operations where beneficial
- Proper error handling
- Structured logging
- Performance monitoring

### 5.3 Documentation
- API documentation (OpenAPI/Swagger)
- Component documentation
- Architecture decisions
- Deployment guides

## 6. Deployment Strategy

### 6.1 Infrastructure
- Kubernetes-based deployment
- Multi-stage Docker builds
- Horizontal scaling
- Load balancing

### 6.2 CI/CD Pipeline
- Automated testing
- Security scanning
- Container builds
- Deployment automation

### 6.3 Monitoring
- Performance metrics
- Error tracking
- Cost monitoring
- Usage analytics

## 7. Getting Started

### 7.1 Local Development
```bash
# Clone repository
git clone https://github.com/YourlocalJay/AIQLeads.git
cd AIQLeads

# Set up environment
cp .env.example .env
# Update environment variables

# Start services
docker-compose up --build
```

### 7.2 Testing
```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

### 7.3 Documentation
- API docs: http://localhost:8000/docs
- Architecture: /docs/architecture/
- Deployment: /docs/deployment/

## 8. Next Steps

1. **Infrastructure Setup**
   - Deploy basic components
   - Set up monitoring
   - Configure CI/CD

2. **Core Features**
   - Implement authentication
   - Set up data models
   - Create base APIs

3. **AI Integration**
   - Configure model endpoints
   - Set up vector storage
   - Implement scoring logic

4. **Testing & Validation**
   - Write comprehensive tests
   - Perform security audit
   - Validate scalability
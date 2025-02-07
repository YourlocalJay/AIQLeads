# AIQLeads Universal Prompt

## Project Status & Implementation Guide

### Component Status Overview
```python
Status Indicators:
🔴 Not Started  - Component defined but work not yet begun
🟡 In Progress  - Active development ongoing
🟣 In Review    - Code complete, awaiting review
🔵 Testing      - Under testing/validation
🟢 Completed    - Fully implemented and verified
⭕ Blocked      - Development blocked by dependency
```

### Current Implementation Status

#### Backend Core (FastAPI)
- 🔴 Main Application Setup
  - Entry point configuration
  - Middleware setup
  - Route registration
- 🔴 Database Integration
  - SQLAlchemy models
  - Migrations system
  - Connection management
- 🔴 Authentication System
  - JWT implementation
  - Role-based access
  - Security middleware

#### AI Integration
- 🔴 Lead Scoring System
  - GPT-4o integration
  - DeepSeek implementation
  - Scoring logic
- 🔴 Market Analysis
  - DeepSeek predictive pricing
  - Qwen time-series modeling
  - Trend analysis
- 🔴 Chatbot System
  - Mistral integration
  - LangChain orchestration
  - Conversation flows

#### Data Pipeline
- 🔴 Scraping Infrastructure
  - FSBO scraper
  - Craigslist integration
  - Facebook Marketplace
- 🔴 Data Processing
  - Normalization pipeline
  - Deduplication system
  - Data enrichment
- 🔴 Storage & Caching
  - Vector storage (Pinecone)
  - Redis caching
  - S3 integration

### Implementation Guidelines

1. File Location Rules
   ```
   AIQLeads/
   ├── backend/           # FastAPI application
   ├── ai_models/         # AI integration code
   ├── scraping/         # Data collection
   ├── services/         # External services
   ├── deployment/       # Infrastructure
   └── tests/           # Test suites
   ```

2. Development Workflow
   - Validate file locations before creation
   - Update component status after changes
   - Document significant modifications
   - Include tests for new components
   - Follow security best practices

3. Critical Rules
   - Never modify core directory structure
   - Keep documentation in sync with code
   - Follow FastAPI best practices
   - Implement proper error handling
   - Maintain security standards
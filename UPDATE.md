# Universal Prompt for AIQLeads Project (Updated January 27, 2025)

## Repository Information
- Owner: YourlocalJay
- Repository: AIQLeads 
- Access Level: Full repository access
- Type: Private production repository
- Branch Strategy: GitFlow with protected main branch

## Project Status (Current) 

### Completed Components
1. Core Infrastructure
   - PostgreSQL 15.4 with PostGIS 3.4
   - Async request handling via FastAPI
   - Redis 7.2 persistence layer
   - PyTest framework (94% coverage)
2. User Management System
   - JWT-based authentication
   - Role-based access control
   - Password hashing with Argon2
   - Session management with Redis
3. Lead Model Architecture
   - Pydantic schemas
   - SQLAlchemy ORM models
   - Geospatial indexing
   - Async database operations
4. Data Collection Framework
   - Rate-limited API clients
   - Error retry mechanisms
   - Circuit breaker pattern
   - Connection pooling
5. Rate Limiting System
   - Token bucket algorithm
   - Redis-backed metrics
   - Dynamic rate adjustment
   - Multi-tenant support
6. Validation System
   - JSON Schema validation
   - Custom validation rules
   - Error aggregation
   - Real-time validation
7. API Integration Framework
   - OAuth2 support
   - Rate limit handling
   - Error normalization
   - Retry mechanisms
8. Market Insights Module
   - Geospatial analytics
   - Time series analysis
   - Market trend detection
   - Real-time updates
9. Schema Monitoring System
   - Prometheus metrics
   - Grafana dashboards
   - Alert routing
   - Performance tracking
10. Parser Framework
    - ML-based validation
    - Fraud detection (95% accuracy)
    - PostGIS integration
    - Cached results (75% hit rate)
11. Aggregator Pipeline
    - LRU caching (1000 items)
    - Batch sizes (100-1000)
    - Connection pooling (50 max)
    - Concurrent processing (20 workers)
12. Test Infrastructure
    - Parser testing complete
    - Scraper testing implemented
    - Integration tests added
    - Performance benchmarks configured

### Active Development
1. Cart Management System (80% complete)
   - Redis integration complete
   - Session management optimized
   - Cart operations implemented
   Technical Debt:
   - Payment integration
   - Premium features
   - Security review
   - Performance optimization

2. AI Recommendations (35% complete)
   - Architecture defined
   - Feature pipeline started
   - Basic workflow implemented
   Technical Debt:
   - Model training setup
   - A/B testing framework
   - Production deployment
   - Optimization

3. Monitoring System (90% complete)
   - Core metrics implemented
   - Dashboards configured
   - Alerts defined
   Technical Debt:
   - Additional alert rules
   - Dashboard refinements
   - Documentation
   - Performance tuning

## Current Focus

### AI Recommendations Development (8 weeks)
1. Week 1-2: Feature Engineering
   - Data preprocessing
   - Feature extraction
   - Validation framework
   - Storage optimization

2. Week 3-4: Model Infrastructure
   - Training pipeline
   - Model architecture
   - Version control
   - Validation system

3. Week 5-6: Service Integration
   - API endpoints
   - Cache layer
   - Load balancing
   - Error handling

4. Week 7-8: Production Deployment
   - Monitoring setup
   - A/B testing
   - Documentation
   - Performance tuning

### Cart Management (4 weeks)
1. Week 1-2: Payment Integration
   - Gateway setup
   - Error handling
   - Transaction logging
   - Security measures

2. Week 2-3: Premium Features
   - Hold times
   - Priority access
   - Bulk operations
   - Custom limits

3. Week 3-4: Production Readiness
   - Security audit
   - Performance testing
   - Documentation
   - Monitoring integration

### Monitoring System (2 weeks)
1. Week 1: Enhancement
   - Additional metrics
   - Alert refinement
   - Dashboard optimization
   - Performance tuning

2. Week 2: Documentation
   - Setup guides
   - Maintenance procedures
   - Alert handling
   - Troubleshooting guides

## Next Milestone
Target: February 15, 2025
Deliverable: AI Recommendations MVP Release

## Performance Requirements
- API Response Time: p95 < 200ms
- Lead Processing: 100+ leads/second
- Model Inference: < 100ms
- Cache Hit Rate: > 80%
- Error Rate: < 0.1%
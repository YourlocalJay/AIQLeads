# Universal Prompt for AIQLeads Project (Updated January 25, 2025)

## Repository Information
- Owner: YourlocalJay
- Repository: AIQLeads 
- Access Level: Full repository access
- Type: Private production repository

## Project Status (Current) 
### Completed Components
1. Core Infrastructure
   - PostgreSQL with PostGIS
   - Async request handling
   - Redis persistence
   - Test infrastructure (94%)

2. User Management System
   - Model implementation
   - Schema validation
   - Authentication flows
   - Profile management

3. Lead Model Architecture
4. Data Collection Framework
5. Rate Limiting System
   - Redis-backed metrics
   - Circuit breaker
   - Alert integration
   - Comprehensive testing

6. Validation System
   - Schema validation
   - Error handling
   - Performance monitoring
   - Documentation

7. API Integration Framework
   - Error handling
   - Retry mechanism
   - Performance monitoring

8. Market Insights Module
   - Geospatial analytics
   - Price trend analysis
   - Demand heatmaps
   - Documentation complete

### Active Development
1. Integration Testing
   - Schema validation
   - Performance benchmarks
   - Error handling

2. Cart Management System
   - Timer integration
   - Premium hold features
   - Notification system

3. AI Recommendations
   - Model implementation
   - Integration testing
   - Performance optimization

## Technical Architecture
```plaintext
AIQLeads/
├── src/
│   ├── aggregator/          
│   │   ├── scrapers/        # Enhanced
│   │   └── parsers/         # Enhanced
│   ├── services/
│   │   ├── pricing/         # Complete
│   │   ├── validation/      # Complete
│   │   └── recommendations/ # In Progress
│   ├── models/             # 85% complete
│   ├── schemas/            # Complete
│   └── config/             # Complete
└── tests/
    ├── aggregator/         # 95% coverage
    ├── services/           # 94% coverage
    └── integration/        # 70% coverage
```

## Development Guidelines
1. Code Standards
   - 94% test coverage minimum
   - Complete type hints
   - Documentation requirement
   - Schema validation

2. Quality Requirements
   - Unit/integration tests
   - Performance benchmarks
   - Alert configuration
   - Redis persistence

3. Validation Requirements
   - Schema validation
   - Error handling
   - Performance metrics
   - Documentation

## Current Development Notes
1. Latest Enhancements
   - Market Insights documentation
   - API specifications
   - Schema monitoring
   - Cross-references

2. Next Steps
   - Integration testing docs
   - Cart management system
   - AI recommendations
   - Performance optimization

## Usage Instructions
For development:
1. Review UPDATE.md
2. Follow patterns
3. Maintain coverage
4. Update docs
5. Validate schemas

For repository:
1. Branch from main
2. Detailed commits
3. CI/CD compliance
4. Reference docs
5. Schema validation
# Universal Prompt for AIQLeads Project (Updated January 25, 2025)

## Repository Information
- Owner: YourlocalJay
- Repository: AIQLeads 
- Access Level: Full repository access for Claude 3.5 Sonnet
- Type: Private production repository

## Project Status (Current) 
### Completed Components
1. Core Infrastructure
   - PostgreSQL with PostGIS integration
   - Async request handling system 
   - Redis persistence with failover
   - Test infrastructure (94% coverage)
2. User Management System
   - Model implementation
   - Schema validation
   - Authentication flows
   - Profile management
3. Lead Model Architecture
4. Data Collection Framework
5. Rate Limiting System
   - Redis-backed with metrics
   - Circuit breaker implementation
   - Alert integration
   - Comprehensive testing
6. Validation System
   - Schema validation
   - Error handling
   - Performance monitoring
   - Documentation coverage

### Active Development
1. API Integration Framework
   - Error handling enhancement
   - Retry mechanism
   - Performance monitoring
2. Testing Improvements
   - Schema validation coverage
   - Performance benchmarks
   - Error handling verification
3. Documentation Refinement
   - API validation details
   - Monitoring metrics
   - Performance standards

## Technical Architecture
```plaintext
AIQLeads/
├── src/
│   ├── aggregator/          
│   │   ├── scrapers/        # Rate limiters integrated
│   │   └── parsers/         # Enhancement ongoing
│   ├── services/
│   │   ├── pricing/         # Pending
│   │   ├── validation/      # Schema validation
│   │   └── recommendations/ # Q1 2025
│   ├── models/             # Complete
│   ├── schemas/            # Complete
│   └── config/             # Environment management
└── tests/
    ├── aggregator/         # 95% coverage
    ├── services/          # 94% coverage
    └── integration/       # Ongoing updates
```

## Development Guidelines
1. Code Standards
   - 94% test coverage minimum
   - Complete type hints
   - Documentation requirement
   - Schema validation enforcement
2. Quality Requirements
   - Unit/integration tests
   - Performance benchmarks
   - Alert configuration
   - Redis persistence
3. Validation Requirements
   - Comprehensive schema validation
   - Error handling specifics
   - Performance metrics
   - Documentation coverage

## Current Development Notes
1. Latest Enhancements
   - API documentation updates
   - Schema validation system
   - Error handling standardization
   - Monitoring integration
2. Next Steps
   - Complete API integration
   - Enhance test coverage
   - Update documentation
   - Implement monitoring

## Usage Instructions
For development:
1. Review UPDATE.md for status
2. Follow established patterns
3. Maintain test coverage
4. Update documentation
5. Validate schema compliance

For repository operations:
1. Branch from main
2. Detailed commit messages
3. CI/CD compliance
4. Reference documentation
5. Schema validation checks
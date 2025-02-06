# Universal Prompt for AIQLeads Project (Updated February 05, 2025)

## Repository Information
* Owner: YourlocalJay
* Repository: AIQLeads
* Access Level: Full repository access
* Type: Private production repository
* Branch Strategy: GitFlow with protected main branch
* Current Branch: Optimization
* Status Tracking: Implemented in core/project_tracking.py

## Project Status
Status indicators:
- 🔴 Not Started
- 🟡 In Progress
- 🟣 In Review
- 🔵 Testing
- 🟢 Completed
- ⭕ Blocked

### Core AI Components (Status: 🟡 In Progress)
1. AI Model Integration:
   - Mistral Small 3 chatbot service
   - DeepSeek R1 lead scoring
   - Core AI configuration
   - Monitoring setup

2. Infrastructure:
   - Docker configuration with CUDA support
   - Docker Compose services setup
   - Repository cleanup automation
   - Replit synchronization

### API Development (Status: 🔴 Not Started)
Located in `aiqleads/api/v1/endpoints/`:
- leads.py: AI-driven Lead Management API
- users.py: User Authentication & Credits API
- analytics.py: AI-Powered Insights
- chatbot.py: AI Chatbot for Lead Queries
- market_trends.py: AI Market Predictions API

### Core Functionality (Status: 🟡 In Progress)
Located in `aiqleads/core/`:
- ai_lead_scoring.py: AI-Based Lead Valuation
- ai_pricing_engine.py: AI-Powered Dynamic Pricing
- ai_recommendation.py: AI Lead Matching & Suggestions
- ai_market_analysis.py: Market Trends & AI Predictions
- ai_monitoring.py: AI Performance & Debugging
- config.py: Centralized Configuration File
- project_tracking.py: Project Status Management

### Models & Database (Status: 🔴 Not Started)
Located in `aiqleads/models/`:
- lead_model.py
- user_model.py
- market_trends_model.py
- transaction_model.py

### Services (Status: 🔴 Not Started)
Located in `aiqleads/services/`:
- lead_service.py
- user_service.py
- analytics_service.py
- chatbot_service.py
- market_trends_service.py
- transaction_service.py

### Data Collection (Status: 🔴 Not Started)
Located in `aiqleads/scrapers/` and `aiqleads/parsers/`:
- Facebook integration
- FSBO data collection
- LinkedIn processing
- Zillow integration
- Craigslist processing
- City-specific implementations

## Project Structure
```
AIQLeads/
├── aiqleads/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── leads.py           # AI-driven Lead Management API
│   │   │   │   ├── users.py           # User Authentication & Credits API
│   │   │   │   ├── analytics.py       # AI-Powered Insights
│   │   │   │   ├── chatbot.py         # AI Chatbot for Lead Queries
│   │   │   │   ├── market_trends.py   # AI Market Predictions API
│   │   │   │   └── __init__.py
[... rest of structure as in reference ...]
```
Full structure maintained in `docs/PROJECT_STRUCTURE.md`

## Development Guidelines

### Status Tracking
```python
from aiqleads.core.project_tracking import ProjectTracker

# Initialize tracker
tracker = ProjectTracker()

# Register new component
tracker.register_component(
    component_type="api",
    component_id="api/v1/endpoints/leads.py",
    component_def={
        "purpose": "AI-driven Lead Management API",
        "functionality": ["lead_scoring", "lead_routing"]
    }
)

# Update status
tracker.update_status(
    component_id="api/v1/endpoints/leads.py",
    status="🟡 In Progress",
    notes="Implementing core lead scoring integration"
)

# Get status report
report = tracker.generate_report()
```

### Component Registration
- All new components must be registered through ProjectTracker
- Functionality hash prevents duplicate implementations
- Path validation ensures adherence to structure
- Status updates maintain development history

### Implementation Rules
1. Core AI Components:
   - Follow AI model integration guidelines
   - Implement monitoring hooks
   - Include performance metrics
   - Document model parameters

2. API Development:
   - Follow RESTful principles
   - Include authentication
   - Implement rate limiting
   - Add request validation

3. Data Management:
   - Use type hints
   - Implement data validation
   - Include error handling
   - Add logging

## Next Development Phase
1. Complete AI model integration
2. Implement remaining API endpoints
3. Set up comprehensive testing
4. Add monitoring dashboards
5. Optimize AI performance

## Notes
- Development continues in Optimization branch
- Focus on preventing duplicate implementations
- Maintain strict structure adherence
- Track all component statuses

## Repository Health
* All scripts executable
* Replit sync configured
* GitHub Actions established
* Monitoring in place
* Status tracking implemented
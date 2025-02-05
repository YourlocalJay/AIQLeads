# Repository Structure Optimization & Cleanup Strategy

## Overview
This document details the optimized structure for AIQLeads, ensuring automation, scalability, and efficiency. The new structure enhances modularity, improves maintainability, and provides a clear organization of scrapers, parsers, AI processing, and marketplace logic.

Additionally, this document outlines the cleanup strategy for outdated files, redundant directories, and best practices for maintaining a streamlined repository.

---

## **Optimized Repository Structure**

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
│   │   │   ├── dependencies.py        # API Dependencies
│   │   │   ├── security.py            # Authentication & Authorization
│   │   │   └── __init__.py
│   ├── core/
│   │   ├── ai_lead_scoring.py         # AI-Based Lead Valuation
│   │   ├── ai_pricing_engine.py       # AI-Powered Dynamic Pricing
│   │   ├── ai_recommendation.py       # AI Lead Matching & Suggestions
│   │   ├── ai_market_analysis.py      # Market Trends & AI Predictions
│   │   ├── ai_monitoring.py           # AI Performance & Debugging
│   │   └── config.py                  # Centralized Configuration File
│   ├── models/
│   │   ├── lead_model.py
│   │   ├── user_model.py
│   │   ├── market_trends_model.py
│   │   ├── transaction_model.py       # Credit-Based Transactions Model
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── lead_schema.py
│   │   ├── user_schema.py
│   │   ├── market_trends_schema.py
│   │   ├── transaction_schema.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── lead_service.py
│   │   ├── user_service.py
│   │   ├── analytics_service.py
│   │   ├── chatbot_service.py
│   │   ├── market_trends_service.py
│   │   ├── transaction_service.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── rate_limiter.py
│   │   ├── logging.py
│   │   ├── validation.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── __init__.py
│   ├── scrapers/
│   │   ├── facebook_scraper.py
│   │   ├── fsbo_scraper.py
│   │   ├── linkedin_scraper.py
│   │   ├── zillow_scraper.py
│   │   ├── craigslist_scraper.py
│   │   ├── city_scrapers/
│   │   │   ├── las_vegas.py
│   │   │   ├── dallas_ft_worth.py
│   │   │   ├── austin.py
│   │   │   ├── phoenix.py
│   │   │   └── __init__.py
│   │   ├── scraper_utils.py           # Common scraping utilities
│   │   └── __init__.py
│   ├── parsers/
│   │   ├── facebook_parser.py
│   │   ├── fsbo_parser.py
│   │   ├── linkedin_parser.py
│   │   ├── zillow_parser.py
│   │   ├── craigslist_parser.py
│   │   ├── city_parsers/
│   │   │   ├── las_vegas_parser.py
│   │   │   ├── dallas_ft_worth_parser.py
│   │   │   ├── austin_parser.py
│   │   │   ├── phoenix_parser.py
│   │   │   └── __init__.py
│   │   ├── parser_utils.py             # Common parsing utilities
│   │   └── __init__.py
│   ├── main.py
├── tests/
├── scripts/
├── infrastructure/
├── docs/
│   ├── README.md
│   ├── API_REFERENCE.md
│   ├── PROJECT_STRUCTURE.md
│   ├── repository-cleanup-strategy.md
│   ├── architecture/
│   ├── monitoring/
├── requirements.txt
├── .gitignore
├── .env
└── README.md
```

---

## **Repository Cleanup Strategy**
### **Files & Directories to Remove**
✅ Remove any redundant directories (`app/`, `src/`, `backend/`).
✅ Delete old/unused migration files under `database/migrations/`.
✅ Remove any outdated scripts under `scripts/` that no longer serve a purpose.

### **Refactoring & Optimization**
✅ Ensure all modules use a consistent naming structure.
✅ Merge duplicate utilities into `utils/` to avoid redundancy.
✅ Organize database models to align with AI-powered lead processing.

---

## **Next Steps**
✅ Implement cleanup based on this strategy.
✅ Refactor repository structure.
✅ Automate repository maintenance checks.
✅ Document any new changes in the `docs/` folder.


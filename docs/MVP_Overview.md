# AIQLeads MVP Overview

## 1. Introduction
AIQLeads is an AI-driven lead marketplace designed to streamline real estate lead acquisition and management. The platform aggregates leads from multiple sources—like Zillow, Craigslist, FSBO, Facebook, LinkedIn, and more—then enriches them with AI-powered data cleaning, dynamic pricing, and fraud detection.

### Key Objectives
1. **High-Quality Leads**  
   - Leverage advanced scrapers, AI data cleaning, and fraud detection to ensure only the best leads are shown.
2. **Efficient Purchasing Flow**  
   - Implement credit-based transactions, cart timers, and geospatial filters for a frictionless user experience.
3. **AI-Driven Personalization**  
   - Provide customized lead recommendations and dynamic pricing that adapt to user preferences and market conditions.
4. **Scalability & Regional Focus**  
   - Target high-demand real estate markets (Las Vegas, Dallas/Ft. Worth, Austin, Phoenix) with modular, extensible scrapers.

---

## 2. Core MVP Features

1. **Lead Aggregation & Scraping**  
   - Collect property listings from Zillow, Craigslist, FSBO, Facebook, and LinkedIn job/housing groups.  
   - Region-specific scrapers (e.g., `las_vegas_scraper.py`, `austin_scraper.py`) ensure localized coverage.

2. **AI-Powered Data Cleaning & Fraud Detection**  
   - Use LLMs (OpenAI, Anthropic, etc.) for data normalization, addressing incomplete or inconsistent fields.  
   - Assign fraud and quality scores to each lead (e.g., detecting duplicates or suspicious patterns).

3. **Dynamic Pricing**  
   - Calculate real-time lead prices based on:
     - **Demand** (number of views, cart additions).  
     - **Lead Quality** (property size, verified details).  
     - **Market Trends** (regional demand surges).  
   - Premium users may see discounted pricing or priority access.

4. **Multi-Tier Credit System**  
   - **Basic**, **Pro**, and **Enterprise** tiers with different credit purchase rates.  
   - Credits deducted when purchasing or reserving leads.

5. **Cart Management & Timers**  
   - **Global Timer**: Restricts total cart duration (e.g., 15 minutes).  
   - **Item-Level Timers**: Each lead can have its own countdown for reservation.  
   - **Premium Extensions**: Users can hold leads for 24 hours, 3 days, or 7 days depending on tier.

6. **Geospatial Search & Market Insights**  
   - PostGIS integration for advanced location queries (e.g., within X miles of downtown).  
   - Market-specific data (e.g., Dallas suburbs, Phoenix retirement communities) for better recommendations.

7. **AI Recommendations**  
   - Embedding-based system (OpenAI embeddings, Pinecone/Weaviate) to suggest leads based on user history, property similarities, and region.

---

## 3. Goals & Success Criteria

- **High Conversion**: Users purchase a large portion of recommended or searched leads.  
- **Accurate & Clean Data**: Minimal time wasted on fraudulent or incomplete listings.  
- **Scalability**: System can handle thousands of leads added daily across multiple markets.  
- **Positive User Feedback**: Agents find the platform’s cart timers, dynamic pricing, and personalization valuable.

---

## 4. Future Enhancements

1. **Enterprise Integrations**: Sync leads with CRMs or marketing platforms.  
2. **More Markets**: Expand beyond the initial four cities using the modular scraper architecture.  
3. **Reinforcement Learning**: Continually refine pricing models based on purchase outcomes.  
4. **User Behavior Analytics**: Track detailed user interactions for deeper personalization and ad targeting.

---

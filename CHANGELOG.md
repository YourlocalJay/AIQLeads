# CHANGELOG

## AIQLeads MVP Development

This changelog documents major updates, enhancements, and fixes for the AIQLeads project.

---

## [Unreleased]
### Added
- Complete `Usage.md` guide with setup, usage, and troubleshooting details.
- Advanced fraud detection integration into `lead_validation_service.py`.
- Circuit breaker mechanisms for rate limiters in `rate_limiter.py`.

### Updated
- Enhanced `craigslist_scraper.py` to improve parsing reliability and handling of pagination.
- Elasticsearch integration for full-text search across leads.
- Schema documentation in `README.md` for all database models.

### Fixed
- Resolved intermittent Redis connection failures in the rate limiter service.
- Addressed pagination bugs in the Facebook Marketplace scraper.

---

## [1.0.0] - 2025-01-20
### Added
- Initial release of the AIQLeads MVP.
- Implemented core features:
  - Lead marketplace with filtering by price, location, and property type.
  - Dynamic pricing service integrated with subscription tiers.
  - Credit-based purchasing system with Stripe and PayPal support.
  - AI-powered recommendations using Pinecone for vector search.
- Geospatial queries powered by PostgreSQL + PostGIS.
- Redis-based cart management with per-item timers.
- Initial scrapers for Zillow, Craigslist, FSBO, and Facebook Marketplace.
- Fraud detection service for validating leads during ingestion.

### Updated
- Improved test coverage across core services (lead marketplace, dynamic pricing).
- Optimized PostgreSQL queries for geospatial filtering.

---

## [0.9.0] - 2024-12-15
### Added
- Initial database schema with models for `User`, `Lead`, `Transaction`, and `Subscription`.
- FastAPI application setup with OpenAPI documentation.
- CI/CD pipelines using GitHub Actions for testing and deployment.

### Updated
- Implemented Dockerfile and `docker-compose.yml` for containerized deployment.
- Integrated Prometheus and Grafana for monitoring and alerting.

---

## [0.8.0] - 2024-11-30
### Added
- Scraping framework with modular scrapers for different platforms.
- Redis integration for caching and session management.
- Basic recommendation engine using rule-based logic.

---

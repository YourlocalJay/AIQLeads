# AIQLeads

## Overview
AIQLeads is an innovative lead marketplace designed for real estate professionals. It leverages advanced AI features to provide geospatial search, dynamic pricing, and AI-driven recommendations. The platform is optimized for efficient and scalable lead management, targeting high-demand real estate markets.

For detailed documentation, please refer to:
- [MVP Overview](docs/MVP_Overview.md) - Current features and development roadmap
- [Architecture](docs/Architecture.md) - Technical design and system architecture
- [Market Insights](docs/MarketInsights.md) - Target markets and data sources
- [Full Documentation](docs/README.md) - Complete documentation index

---

## Features
- **Geospatial Search**: Locate leads in specific geographic regions with precision.
- **Dynamic Pricing**: Automated pricing adjustments based on demand, lead quality, and availability.
- **AI-Driven Recommendations**: Personalized lead suggestions using embeddings and fraud detection to ensure quality.
- **Cart Management**: Global and item-specific timers for lead reservations.
- **Fraud Detection**: AI-powered algorithms detect duplicate or suspicious listings, improving data reliability.

---

## Target Markets
- Las Vegas
- Dallas/Ft. Worth
- Austin
- Phoenix

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL with PostGIS
- Redis (for caching and timers)
- Docker (optional for containerized deployment)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YourlocalJay/AIQLeads.git
   cd AIQLeads

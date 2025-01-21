# AIQLeads

## Overview
AIQLeads is an innovative lead marketplace designed for real estate professionals. It leverages advanced AI features to provide geospatial search, dynamic pricing, and AI-driven recommendations. The platform is optimized for efficient and scalable lead management, targeting high-demand real estate markets.

For detailed documentation, please refer to:
- [MVP Overview](docs/MVP_Overview.md) - Current features and development roadmap
- [Architecture](docs/Architecture.md) - Technical design and system architecture
- [Market Insights](docs/MarketInsights.md) - Target markets and data sources
- [Full Documentation](docs/README.md) - Complete documentation index

## Features
- **Geospatial Search**: Locate leads in specific geographic regions with precision
- **Dynamic Pricing**: Automated pricing adjustments based on demand and availability
- **AI-Driven Recommendations**: Personalized lead suggestions and fraud detection using advanced embeddings
- **Cart Management**: Global and item-specific timers for lead reservations

## Target Markets
- Las Vegas
- Dallas/Ft. Worth
- Austin
- Phoenix

## Getting Started

### Prerequisites
- Python 3.10+
- Docker (optional for containerized deployment)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YourlocalJay/AIQLeads.git
   cd AIQLeads
   ```

2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env` and update the values as needed.

### Running the Application
1. Run the FastAPI server locally:
   ```bash
   uvicorn src.main:app --reload
   ```

2. Access the API documentation:
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.

### Docker Deployment
1. Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

## Contribution
We welcome contributions to AIQLeads. Please review our [Contributing Guidelines](docs/CONTRIBUTING.md) for details on the code of conduct and submission process.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, contact [YourlocalJay](mailto:your-email@example.com).
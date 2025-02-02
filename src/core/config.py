"""
MVP Configuration for AIQLeads
"""
from typing import Dict, Any
import os

# Fireworks AI Configuration
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
FIREWORKS_MODEL = "llama-v2-7b-chat"
FIREWORKS_MAX_TOKENS = 500

# BrightData Configuration
BRIGHTDATA_USERNAME = os.getenv("BRIGHTDATA_USERNAME")
BRIGHTDATA_PASSWORD = os.getenv("BRIGHTDATA_PASSWORD")
BRIGHTDATA_ZONE = "residential"
BRIGHTDATA_COUNTRY = "us"

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_TTL = 3600  # 1 hour cache

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
MAX_CONNECTIONS = 20
POOL_SIZE = 5

# API Configuration
API_RATE_LIMIT = 100  # requests per minute
API_TIMEOUT = 30  # seconds

# Scraping Configuration
SCRAPING_BATCH_SIZE = 50
SCRAPING_DELAY = 1  # seconds between requests
MAX_RETRIES = 3

# Lead Scoring Configuration
SCORING_WEIGHTS: Dict[str, float] = {
    "property_value": 0.3,
    "location_score": 0.3,
    "market_trend": 0.2,
    "listing_age": 0.2
}

# Cache Configuration
CACHE_CONFIG: Dict[str, Any] = {
    "lead_scores": {"ttl": 3600},
    "market_data": {"ttl": 7200},
    "property_details": {"ttl": 86400}
}

# Feature Flags
FEATURES = {
    "websocket": False,  # Defer WebSocket implementation
    "advanced_analytics": False,  # Basic analytics only
    "multi_region": False,  # Single region for MVP
    "economic_indicators": False  # Basic market data only
}
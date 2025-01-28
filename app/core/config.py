from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    """Application settings"""
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Feature Extraction Settings
    FEATURE_CACHE_TTL: int = 3600  # 1 hour
    DEFAULT_BATCH_SIZE: int = 100
    
    # Lead Behavior Settings
    LEAD_BEHAVIOR_CONFIG: Dict[str, Any] = {
        'min_interactions': 1,
        'max_interaction_gap_hours': 72,
        'engagement_weights': {
            'view': 1.0,
            'click': 2.0,
            'inquiry': 3.0,
            'message': 4.0,
            'schedule': 5.0
        },
        'business_hours': {
            'start': 9,  # 9 AM
            'end': 17,   # 5 PM
        },
        'cache_ttl': 3600
    }
    
    # Monitoring Settings
    PROMETHEUS_PUSH_GATEWAY: str = "http://localhost:9091"
    METRICS_PUSH_INTERVAL: int = 60  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
from typing import Dict, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class AISettings(BaseSettings):
    # Mistral Small 3 Configuration
    MISTRAL_API_KEY: str
    MISTRAL_API_BASE_URL: str = "https://api.mistral.ai/v1"
    MISTRAL_MODEL_NAME: str = "mistral-small-3"
    MISTRAL_MAX_TOKENS: int = 1024
    MISTRAL_TEMPERATURE: float = 0.7
    MISTRAL_CACHE_TTL: int = 3600  # Cache responses for 1 hour
    
    # DeepSeek R1 Configuration
    DEEPSEEK_API_KEY: str
    DEEPSEEK_API_BASE_URL: str = "https://api.deepseek.ai/v1"
    DEEPSEEK_MODEL_NAME: str = "deepseek-r1"
    DEEPSEEK_EMBEDDING_DIM: int = 768
    DEEPSEEK_BATCH_SIZE: int = 32
    
    # Vector Search Configuration
    VECTOR_STORE: str = "pinecone"  # Options: pinecone, weaviate, chroma
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "aiqleads-leads"
    
    # Caching Configuration
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_ENABLED: bool = True
    
    # Cost Control Settings
    MAX_DAILY_API_CALLS: int = 1000
    COST_PER_TOKEN: float = 0.000001
    BUDGET_ALERT_THRESHOLD: float = 50.0  # Alert when daily cost exceeds $50
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_ai_settings() -> AISettings:
    """Get cached AI settings instance."""
    return AISettings()

# Model-specific configurations
MISTRAL_CHAT_PARAMS: Dict = {
    "max_new_tokens": get_ai_settings().MISTRAL_MAX_TOKENS,
    "temperature": get_ai_settings().MISTRAL_TEMPERATURE,
    "stop_sequences": ["Human:", "Assistant:"],
    "repeat_penalty": 1.1
}

DEEPSEEK_SCORING_PARAMS: Dict = {
    "embedding_dim": get_ai_settings().DEEPSEEK_EMBEDDING_DIM,
    "batch_size": get_ai_settings().DEEPSEEK_BATCH_SIZE,
    "similarity_threshold": 0.85,
    "min_confidence_score": 0.7
}

# Error messages
ERROR_MESSAGES = {
    "api_key_missing": "AI model API key not configured",
    "rate_limit_exceeded": "Daily API call limit exceeded",
    "budget_exceeded": "Daily budget threshold exceeded",
    "model_error": "AI model failed to process request",
    "invalid_input": "Invalid input format for AI processing"
}

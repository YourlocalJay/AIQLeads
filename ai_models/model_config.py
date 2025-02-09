from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

class ModelCapability(Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class ModelConfig:
    model_id: str
    capability: ModelCapability
    max_hourly_requests: int
    max_tokens: int
    cost_per_1k_tokens: float
    typical_latency_ms: int
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

MODEL_CONFIGS = {
    "claude-3-5-sonnet-20241022": ModelConfig(
        model_id="claude-3-5-sonnet-20241022",
        capability=ModelCapability.EXPERT,
        max_hourly_requests=100,
        max_tokens=200000,
        cost_per_1k_tokens=0.015,
        typical_latency_ms=800,
        additional_params={
            "temperature": 0.7,
            "top_p": 0.9,
        }
    ),
    "claude-3-opus": ModelConfig(
        model_id="claude-3-opus",
        capability=ModelCapability.EXPERT,
        max_hourly_requests=80,
        max_tokens=300000,
        cost_per_1k_tokens=0.025,
        typical_latency_ms=1200,
        additional_params={
            "temperature": 0.7,
            "top_p": 0.9,
        }
    ),
    "claude-3-haiku": ModelConfig(
        model_id="claude-3-haiku",
        capability=ModelCapability.ADVANCED,
        max_hourly_requests=150,
        max_tokens=100000,
        cost_per_1k_tokens=0.008,
        typical_latency_ms=300,
        additional_params={
            "temperature": 0.7,
            "top_p": 0.9,
        }
    )
}

def get_model_config(model_id: str) -> ModelConfig:
    """Get configuration for specified model"""
    if model_id not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model ID: {model_id}")
    return MODEL_CONFIGS[model_id]

def get_fallback_model(current_model: str) -> str:
    """Get appropriate fallback model based on current model"""
    fallback_chain = {
        "claude-3-5-sonnet-20241022": "claude-3-opus",
        "claude-3-opus": "claude-3-haiku",
        "claude-3-haiku": "claude-3-5-sonnet-20241022"
    }
    return fallback_chain.get(current_model)
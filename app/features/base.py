"""
Base class and utilities for feature extraction.

This module provides the foundation for all feature extractors in the system,
including caching, validation, monitoring, and error handling infrastructure.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypedDict, Union, Literal
import asyncio
import hashlib
import json
import logging
from prometheus_client import Counter, Histogram

from app.core.cache import RedisCache
from app.core.config import settings
from app.core.metrics import (
    FEATURE_EXTRACTION_TIME,
    CACHE_HIT_COUNTER,
    CACHE_MISS_COUNTER,
    VALIDATION_ERROR_COUNTER,
    COMPUTATION_ERROR_COUNTER,
)

logger = logging.getLogger(__name__)

# Type definitions for improved type safety
FeatureValue = Union[int, float]
FeatureDict = Dict[str, FeatureValue]
ExtractionMode = Literal["sync", "async"]

class FeatureConfig(TypedDict, total=False):
    """Configuration options for feature extractors"""
    # Cache settings
    cache_ttl: int  # Cache time-to-live in seconds
    cache_enabled: bool  # Whether to use caching
    
    # Batch processing
    batch_size: int  # Size of batches for processing
    batch_timeout: float  # Timeout for batch operations in seconds
    
    # Validation
    validation_enabled: bool  # Whether to validate features
    strict_validation: bool  # Whether to use strict validation
    
    # Performance
    extraction_timeout: float  # Timeout for feature extraction in seconds
    retry_count: int  # Number of retries for failed extractions
    retry_delay: float  # Delay between retries in seconds
    
    # Processing mode
    mode: ExtractionMode  # Extraction mode (sync/async)

class FeatureExtractionError(Exception):
    """Base exception for feature extraction errors"""
    pass

class ValidationError(FeatureExtractionError):
    """Raised when feature validation fails"""
    pass

class ComputationError(FeatureExtractionError):
    """Raised when feature computation fails"""
    pass

class CacheError(FeatureExtractionError):
    """Raised when cache operations fail"""
    pass
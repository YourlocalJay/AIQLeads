from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import hashlib
import json
import logging
from prometheus_client import Counter, Histogram

from app.core.cache import RedisCache
from app.core.config import settings
from app.core.metrics import FEATURE_EXTRACTION_TIME, CACHE_HIT_COUNTER, CACHE_MISS_COUNTER

logger = logging.getLogger(__name__)

class FeatureExtractionError(Exception):
    """Base exception for feature extraction errors"""
    pass

class ValidationError(FeatureExtractionError):
    """Raised when feature validation fails"""
    pass

class ComputationError(FeatureExtractionError):
    """Raised when feature computation fails"""
    pass

class BaseFeatureExtractor(ABC):
    """
    Base class for feature extractors.
    
    Provides caching, validation, and monitoring infrastructure for feature extraction.
    Subclasses must implement _compute_features method.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature extractor with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.cache = RedisCache()
        self.cache_ttl = self.config.get('cache_ttl', settings.FEATURE_CACHE_TTL)
        self.batch_size = self.config.get('batch_size', settings.DEFAULT_BATCH_SIZE)
        
    async def extract(self, lead_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features from lead data with caching and monitoring.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            Dictionary mapping feature names to float values
            
        Raises:
            FeatureExtractionError: If feature extraction fails
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(lead_data)
            
            # Check cache first
            if cached := await self.cache.get(cache_key):
                CACHE_HIT_COUNTER.inc()
                return cached
                
            CACHE_MISS_COUNTER.inc()
            
            # Compute features and measure time
            with FEATURE_EXTRACTION_TIME.time():
                features = await self._compute_features(lead_data)
            
            # Validate features
            self._validate_features(features)
            
            # Cache results
            await self.cache.set(
                cache_key,
                features,
                expire=self.cache_ttl
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}", exc_info=True)
            raise FeatureExtractionError(f"Feature extraction failed: {str(e)}") from e
            
    async def extract_batch(self, leads_data: list[Dict[str, Any]]) -> list[Dict[str, float]]:
        """
        Extract features for a batch of leads.
        
        Args:
            leads_data: List of lead data dictionaries
            
        Returns:
            List of feature dictionaries
        """
        results = []
        for i in range(0, len(leads_data), self.batch_size):
            batch = leads_data[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[self.extract(lead) for lead in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
        return results
            
    def _generate_cache_key(self, lead_data: Dict[str, Any]) -> str:
        """
        Generate a cache key for the lead data.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            Cache key string
        """
        # Sort keys for consistent hashing
        serialized = json.dumps(lead_data, sort_keys=True)
        # Include extractor class name in key
        key_base = f"{self.__class__.__name__}:{serialized}"
        return hashlib.sha256(key_base.encode()).hexdigest()
        
    def _validate_features(self, features: Dict[str, float]) -> None:
        """
        Validate extracted features.
        
        Args:
            features: Dictionary of extracted features
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(features, dict):
            raise ValidationError("Features must be a dictionary")
            
        for name, value in features.items():
            if not isinstance(name, str):
                raise ValidationError(f"Feature name must be string, got {type(name)}")
            if not isinstance(value, (int, float)):
                raise ValidationError(f"Feature value must be numeric, got {type(value)}")
                
    @abstractmethod
    async def _compute_features(self, lead_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute features from lead data. Must be implemented by subclasses.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            Dictionary mapping feature names to float values
        """
        raise NotImplementedError
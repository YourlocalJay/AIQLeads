"""
Advanced caching system for AIQLeads.
Implements multi-level caching with distributed support and intelligent warming strategies.
"""
from typing import Any, Optional, Dict, List, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    warm_loads: int = 0
    last_warm_time: Optional[datetime] = None

class CacheLayer(ABC):
    """Abstract base class for cache layers."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve item from cache."""
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store item in cache."""
        pass
    
    @abstractmethod
    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all items from cache."""
        pass

class MemoryCache(CacheLayer):
    """L1 memory cache implementation."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Tuple[Any, Optional[datetime]]] = {}
        self._max_size = max_size
        self._lock = threading.Lock()
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or expiry > datetime.now():
                    self.stats.hits += 1
                    return value
                self.remove(key)
            self.stats.misses += 1
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict()
            
            expiry = None if ttl is None else datetime.now() + ttl
            self._cache[key] = (value, expiry)
            return True

    def remove(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            
    def _evict(self) -> None:
        """Evict least recently used items."""
        # Implementation of eviction strategy
        if not self._cache:
            return
            
        # For now, simple LRU implementation
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k][1] or datetime.min)
        self.remove(oldest_key)
        self.stats.evictions += 1

class DistributedCache(CacheLayer):
    """L2 distributed cache implementation."""
    
    def __init__(self, nodes: List[str], replication_factor: int = 2):
        self.nodes = nodes
        self.replication_factor = min(replication_factor, len(nodes))
        self._local_cache = MemoryCache()
        self.stats = CacheStats()
        
    def get(self, key: str) -> Optional[Any]:
        # First check local cache
        value = self._local_cache.get(key)
        if value is not None:
            return value
            
        # Then check distributed nodes
        # TODO: Implement actual distributed get logic
        return None
        
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        # Store in local cache
        self._local_cache.put(key, value, ttl)
        
        # TODO: Implement distributed put logic
        return True
        
    def remove(self, key: str) -> bool:
        # Remove from local cache
        self._local_cache.remove(key)
        
        # TODO: Implement distributed remove logic
        return True
        
    def clear(self) -> None:
        self._local_cache.clear()
        # TODO: Implement distributed clear logic

class CacheWarmer:
    """Intelligent cache warming system."""
    
    def __init__(self, cache: CacheLayer):
        self.cache = cache
        self.access_patterns: Dict[str, int] = {}
        self._lock = threading.Lock()
        
    def record_access(self, key: str) -> None:
        """Record cache key access for pattern analysis."""
        with self._lock:
            self.access_patterns[key] = self.access_patterns.get(key, 0) + 1
            
    def warm_cache(self, loader_func: callable) -> None:
        """Warm cache based on access patterns."""
        with self._lock:
            # Sort keys by access frequency
            sorted_keys = sorted(
                self.access_patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Warm most frequently accessed keys
            for key, _ in sorted_keys[:100]:  # Warm top 100 items
                try:
                    value = loader_func(key)
                    if value is not None:
                        self.cache.put(key, value)
                        if hasattr(self.cache, 'stats'):
                            self.cache.stats.warm_loads += 1
                except Exception as e:
                    logger.error(f"Error warming cache for key {key}: {e}")

class MultiLevelCache:
    """Multi-level cache coordinator."""
    
    def __init__(
        self, 
        l1_cache: Optional[CacheLayer] = None,
        l2_cache: Optional[CacheLayer] = None,
        warmer: Optional[CacheWarmer] = None
    ):
        self.l1_cache = l1_cache or MemoryCache()
        self.l2_cache = l2_cache
        self.warmer = warmer or CacheWarmer(self.l1_cache)
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache hierarchy."""
        # Try L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            self.warmer.record_access(key)
            return value
            
        # Try L2 cache if available
        if self.l2_cache is not None:
            value = self.l2_cache.get(key)
            if value is not None:
                # Populate L1 cache
                self.l1_cache.put(key, value)
                self.warmer.record_access(key)
                return value
                
        return None
        
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in cache hierarchy."""
        success = self.l1_cache.put(key, value, ttl)
        
        if success and self.l2_cache is not None:
            success = success and self.l2_cache.put(key, value, ttl)
            
        return success
        
    def remove(self, key: str) -> bool:
        """Remove value from cache hierarchy."""
        success = self.l1_cache.remove(key)
        
        if self.l2_cache is not None:
            success = success and self.l2_cache.remove(key)
            
        return success
        
    def clear(self) -> None:
        """Clear all cache layers."""
        self.l1_cache.clear()
        if self.l2_cache is not None:
            self.l2_cache.clear()
            
    def warm(self, loader_func: callable) -> None:
        """Trigger cache warming."""
        self.warmer.warm_cache(loader_func)

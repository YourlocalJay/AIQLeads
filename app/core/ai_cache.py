"""
AI-optimized caching system for AIQLeads.
Implements adaptive caching with LLM usage patterns and predictive prefetching.
"""
from typing import Any, Optional, Dict, List, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import logging
import json
import sqlite3
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class AIUsageMetrics:
    """Metrics for AI operation monitoring."""
    token_count: int = 0
    processing_time: float = 0.0
    cost: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_access: Optional[datetime] = None
    lead_id: Optional[str] = None
    region: Optional[str] = None

class AICacheStats:
    """Enhanced statistics for AI cache performance monitoring."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.token_usage = 0
        self.total_cost = 0.0
        self.access_patterns: Dict[str, int] = defaultdict(int)
        self.region_stats: Dict[str, Dict] = defaultdict(lambda: {
            'hits': 0, 'misses': 0, 'costs': 0.0
        })
        self._lock = threading.Lock()

    def record_hit(self, key: str, region: Optional[str] = None):
        with self._lock:
            self.hits += 1
            self.access_patterns[key] += 1
            if region:
                self.region_stats[region]['hits'] += 1

    def record_miss(self, key: str, region: Optional[str] = None):
        with self._lock:
            self.misses += 1
            if region:
                self.region_stats[region]['misses'] += 1

    def record_cost(self, cost: float, region: Optional[str] = None):
        with self._lock:
            self.total_cost += cost
            if region:
                self.region_stats[region]['costs'] += cost

class AICache:
    """AI-optimized cache implementation with predictive prefetching."""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,  # Default 1 hour TTL
        cost_threshold: float = 0.05,  # Cost threshold for caching decision
        sqlite_path: str = "ai_cache.db"
    ):
        self._memory_cache: Dict[str, Tuple[Any, datetime, AIUsageMetrics]] = {}
        self._max_size = max_size
        self._default_ttl = ttl
        self._cost_threshold = cost_threshold
        self._lock = threading.Lock()
        self.stats = AICacheStats()
        
        # Initialize SQLite for persistent storage
        self._init_sqlite(sqlite_path)
        
    def _init_sqlite(self, path: str):
        """Initialize SQLite database for persistent cache storage."""
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS ai_cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                expiry TIMESTAMP,
                metrics TEXT
            )
        """)
        self._db.commit()

    async def get(
        self,
        key: str,
        region: Optional[str] = None,
        lead_id: Optional[str] = None
    ) -> Optional[Any]:
        """Get value from cache with AI-optimized retrieval."""
        with self._lock:
            # Check memory cache first
            if key in self._memory_cache:
                value, expiry, metrics = self._memory_cache[key]
                if datetime.now() < expiry:
                    self.stats.record_hit(key, region)
                    metrics.cache_hits += 1
                    metrics.last_access = datetime.now()
                    metrics.lead_id = lead_id
                    metrics.region = region
                    return value
                else:
                    del self._memory_cache[key]

            # Check persistent storage
            try:
                cur = self._db.execute(
                    "SELECT value, expiry, metrics FROM ai_cache WHERE key = ?",
                    (key,)
                )
                result = cur.fetchone()
                if result:
                    value, expiry_str, metrics_json = result
                    expiry = datetime.fromisoformat(expiry_str)
                    if datetime.now() < expiry:
                        self.stats.record_hit(key, region)
                        metrics = AIUsageMetrics(**json.loads(metrics_json))
                        metrics.cache_hits += 1
                        metrics.last_access = datetime.now()
                        metrics.lead_id = lead_id
                        metrics.region = region
                        
                        # Promote to memory cache if frequently accessed
                        if metrics.cache_hits > 5:
                            self._memory_cache[key] = (
                                json.loads(value),
                                expiry,
                                metrics
                            )
                        return json.loads(value)
                    else:
                        cur.execute(
                            "DELETE FROM ai_cache WHERE key = ?",
                            (key,)
                        )
                        self._db.commit()
            except Exception as e:
                logger.error(f"Error reading from persistent cache: {e}")

            self.stats.record_miss(key, region)
            return None

    async def put(
        self,
        key: str,
        value: Any,
        metrics: AIUsageMetrics,
        ttl: Optional[int] = None,
        region: Optional[str] = None
    ) -> bool:
        """Store value in cache with AI-optimized storage decisions."""
        expiry = datetime.now() + timedelta(
            seconds=ttl if ttl is not None else self._default_ttl
        )
        
        # Only cache if cost exceeds threshold (worth caching)
        if metrics.cost < self._cost_threshold:
            return False

        with self._lock:
            # Evict if needed
            while len(self._memory_cache) >= self._max_size:
                self._evict_lru()

            try:
                # Store in memory cache
                self._memory_cache[key] = (value, expiry, metrics)
                
                # Store in persistent cache
                self._db.execute(
                    """
                    INSERT OR REPLACE INTO ai_cache
                    (key, value, expiry, metrics)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        key,
                        json.dumps(value),
                        expiry.isoformat(),
                        json.dumps(metrics.__dict__)
                    )
                )
                self._db.commit()
                
                self.stats.record_cost(metrics.cost, region)
                return True
            except Exception as e:
                logger.error(f"Error writing to cache: {e}")
                return False

    def _evict_lru(self):
        """Evict least recently used items with AI cost considerations."""
        if not self._memory_cache:
            return

        # Consider both access time and cost when evicting
        def eviction_score(item):
            _, expiry, metrics = item[1]
            time_factor = (datetime.now() - metrics.last_access).total_seconds() \
                if metrics.last_access else float('inf')
            cost_factor = metrics.cost if metrics.cost else 0
            return time_factor / (1 + cost_factor)  # Lower score = keep in cache

        # Find item with highest eviction score
        key_to_evict = max(
            self._memory_cache.items(),
            key=lambda x: eviction_score(x)
        )[0]

        del self._memory_cache[key_to_evict]
        self.stats.evictions += 1

    async def prefetch(
        self,
        keys: List[str],
        loader_func: callable,
        region: Optional[str] = None
    ):
        """Predictively fetch and cache AI responses."""
        async def fetch_single(key: str):
            try:
                value, metrics = await loader_func(key)
                if value is not None:
                    await self.put(key, value, metrics, region=region)
            except Exception as e:
                logger.error(f"Error prefetching key {key}: {e}")

        # Fetch in parallel with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent prefetches
        async with semaphore:
            await asyncio.gather(*[fetch_single(key) for key in keys])

    def get_region_stats(self, region: str) -> Dict:
        """Get cache statistics for a specific region."""
        return self.stats.region_stats.get(region, {
            'hits': 0,
            'misses': 0,
            'costs': 0.0
        })

    def clear(self):
        """Clear all cache data."""
        with self._lock:
            self._memory_cache.clear()
            self._db.execute("DELETE FROM ai_cache")
            self._db.commit()

    def __del__(self):
        """Cleanup database connection."""
        try:
            self._db.close()
        except:
            pass
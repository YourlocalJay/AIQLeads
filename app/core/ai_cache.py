from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis
import sqlite3
import threading
from dataclasses import dataclass
from collections import OrderedDict

@dataclass
class CacheItem:
    value: Any
    created_at: datetime
    ttl: Optional[int] = None
    weight: float = 1.0
    access_count: int = 0

class AIOptimizedCache:
    def __init__(self, max_size: int = 1000, redis_url: Optional[str] = None):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
        self._redis = redis.from_url(redis_url) if redis_url else None
        self._setup_sqlite()

    def _setup_sqlite(self):
        self._conn = sqlite3.connect('cache_stats.db', check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_stats (
                key TEXT PRIMARY KEY,
                access_count INTEGER,
                last_access TIMESTAMP,
                weight REAL
            )
        """)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item.ttl and datetime.now() - item.created_at > timedelta(seconds=item.ttl):
                    del self._cache[key]
                    return None
                self._update_stats(key)
                return item.value
            return self._get_from_persistent(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None, weight: float = 1.0):
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict()
            self._cache[key] = CacheItem(
                value=value,
                created_at=datetime.now(),
                ttl=ttl,
                weight=weight
            )
            self._persist(key, value, ttl, weight)

    def _evict(self):
        if not self._cache:
            return
        
        # Use weighted scoring for eviction
        scores = []
        for key, item in self._cache.items():
            age = (datetime.now() - item.created_at).total_seconds()
            score = (item.access_count * item.weight) / (age + 1)
            scores.append((score, key))
        
        # Remove item with lowest score
        scores.sort()
        del self._cache[scores[0][1]]

    def _update_stats(self, key: str):
        item = self._cache[key]
        item.access_count += 1
        self._conn.execute(
            "UPDATE cache_stats SET access_count = access_count + 1, last_access = ? WHERE key = ?",
            (datetime.now(), key)
        )

    def _persist(self, key: str, value: Any, ttl: Optional[int], weight: float):
        if self._redis:
            self._redis.set(key, value, ex=ttl)
        
        self._conn.execute("""
            INSERT OR REPLACE INTO cache_stats (key, access_count, last_access, weight)
            VALUES (?, 0, ?, ?)
        """, (key, datetime.now(), weight))

    def _get_from_persistent(self, key: str) -> Optional[Any]:
        if self._redis:
            value = self._redis.get(key)
            if value:
                return value
        return None

    def clear(self):
        with self._lock:
            self._cache.clear()
            if self._redis:
                self._redis.flushdb()
            self._conn.execute("DELETE FROM cache_stats")

    def __del__(self):
        self._conn.close()
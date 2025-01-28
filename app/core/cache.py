import json
from typing import Any, Optional
import aioredis
import logging
from prometheus_client import Counter, Histogram

from app.core.config import settings

logger = logging.getLogger(__name__)

# Metrics
CACHE_OPERATION_TIME = Histogram(
    'cache_operation_seconds',
    'Time spent on cache operations',
    ['operation']
)
CACHE_ERROR_COUNTER = Counter(
    'cache_errors_total',
    'Number of cache operation errors',
    ['operation']
)

class RedisCache:
    """Redis cache implementation with monitoring and error handling."""
    
    def __init__(self):
        """Initialize Redis connection pool."""
        self._redis = None
        self._connection_pool = None
        
    async def _get_redis(self) -> aioredis.Redis:
        """
        Get Redis connection, creating pool if needed.
        
        Returns:
            Redis connection from pool
        """
        if self._redis is None:
            try:
                self._connection_pool = aioredis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    encoding='utf-8',
                    decode_responses=True
                )
                self._redis = aioredis.Redis(
                    connection_pool=self._connection_pool,
                    retry_on_timeout=True
                )
            except Exception as e:
                logger.error(f"Failed to create Redis connection: {str(e)}")
                raise
                
        return self._redis
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        try:
            with CACHE_OPERATION_TIME.labels(operation='get').time():
                redis = await self._get_redis()
                value = await redis.get(key)
                
                if value is None:
                    return None
                    
                return json.loads(value)
                
        except Exception as e:
            CACHE_ERROR_COUNTER.labels(operation='get').inc()
            logger.error(f"Cache get failed for key {key}: {str(e)}")
            return None
            
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Optional expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with CACHE_OPERATION_TIME.labels(operation='set').time():
                redis = await self._get_redis()
                serialized = json.dumps(value)
                
                if expire:
                    await redis.setex(key, expire, serialized)
                else:
                    await redis.set(key, serialized)
                    
                return True
                
        except Exception as e:
            CACHE_ERROR_COUNTER.labels(operation='set').inc()
            logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with CACHE_OPERATION_TIME.labels(operation='delete').time():
                redis = await self._get_redis()
                await redis.delete(key)
                return True
                
        except Exception as e:
            CACHE_ERROR_COUNTER.labels(operation='delete').inc()
            logger.error(f"Cache delete failed for key {key}: {str(e)}")
            return False
            
    async def clear(self, pattern: str = "*") -> bool:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern to match
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with CACHE_OPERATION_TIME.labels(operation='clear').time():
                redis = await self._get_redis()
                cursor = 0
                while True:
                    cursor, keys = await redis.scan(cursor, pattern, 100)
                    if keys:
                        await redis.delete(*keys)
                    if cursor == 0:
                        break
                return True
                
        except Exception as e:
            CACHE_ERROR_COUNTER.labels(operation='clear').inc()
            logger.error(f"Cache clear failed for pattern {pattern}: {str(e)}")
            return False
            
    async def close(self):
        """Close Redis connections."""
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._redis = None
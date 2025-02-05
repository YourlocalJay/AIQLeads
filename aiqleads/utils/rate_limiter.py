import asyncio
from typing import Optional
from src.utils.errors import RateLimitExceeded
from app.services.cache.redis_service import AIQRedisCache


class RateLimiter:
    """Token bucket rate limiter with queue-based management."""
    
    def __init__(self, rate_limit: int, window_size: int, redis_url: Optional[str] = None):
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.redis = AIQRedisCache(redis_url) if redis_url else None
        self._request_queue = asyncio.Queue(maxsize=1000)

    async def acquire(self, endpoint: str, tokens: int = 1) -> bool:
        """Attempts to acquire tokens for an API request."""
        if await self._can_proceed(endpoint, tokens):
            return True
        await self._request_queue.put((endpoint, tokens))
        return False

    async def _can_proceed(self, endpoint: str, tokens: int) -> bool:
        """Checks if the rate limit allows a new request."""
        count = await self.redis.get(endpoint) or 0
        if count + tokens <= self.rate_limit:
            await self.redis.increment(endpoint, tokens, expire=self.window_size)
            return True
        return False

    async def process_queue(self):
        """Handles queued requests dynamically."""
        while True:
            endpoint, tokens = await self._request_queue.get()
            if await self._can_proceed(endpoint, tokens):
                self._request_queue.task_done()
            else:
                await asyncio.sleep(1)
                await self._request_queue.put((endpoint, tokens))

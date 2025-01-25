from typing import Dict, Optional
from datetime import datetime
from src.aggregator.scrapers.rate_limiters.base_limiter import BaseRateLimiter

class RateLimiter(BaseRateLimiter):
    """Redis-backed rate limiter for general application use.
    
    Inherits core functionality from BaseRateLimiter and adds:
    - Automatic key prefix management
    - Request batching
    - Enhanced metrics
    """
    
    def __init__(
        self,
        requests_per_minute: int,
        redis_url: str,
        key_prefix: str = "app",
        batch_size: int = 10
    ):
        super().__init__(
            requests_per_minute=requests_per_minute,
            redis_url=redis_url
        )
        self.key_prefix = key_prefix
        self.batch_size = batch_size
        self._batch_queue: Dict[str, list] = {}
    
    def _get_redis_key(self, endpoint: str) -> str:
        return f"{self.key_prefix}:{endpoint}"
    
    async def acquire_batch(self, endpoint: str, items: list) -> list:
        """Acquire rate limit tokens for a batch of items.
        
        Returns list of items that were allowed through rate limit.
        """
        allowed_items = []
        key = self._get_redis_key(endpoint)
        
        # Process in batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            if await self.acquire(key, len(batch)):
                allowed_items.extend(batch)
            else:
                break
                
        return allowed_items
    
    async def get_enhanced_metrics(self, endpoint: str) -> Dict:
        """Get detailed metrics including batching stats."""
        base_metrics = await self.get_metrics(self._get_redis_key(endpoint))
        
        return {
            **base_metrics,
            "batch_queue_size": len(self._batch_queue.get(endpoint, [])),
            "batch_size": self.batch_size,
            "key_prefix": self.key_prefix
        }

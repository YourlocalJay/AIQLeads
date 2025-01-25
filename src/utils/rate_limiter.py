from typing import Dict, Optional
from redis import asyncio as aioredis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.default_expiry = 3600  # 1 hour
        
    async def get_requests(self, key: str, window: int) -> int:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        
        async with self.redis.pipeline() as pipe:
            # Remove expired entries
            await pipe.zremrangebyscore(
                f"rate_limit:{key}:requests",
                "-inf",
                window_start.timestamp()
            )
            # Count remaining entries
            await pipe.zcard(f"rate_limit:{key}:requests")
            # Add current request
            await pipe.zadd(
                f"rate_limit:{key}:requests",
                {str(now.timestamp()): now.timestamp()}
            )
            # Set expiry
            await pipe.expire(f"rate_limit:{key}:requests", self.default_expiry)
            results = await pipe.execute()
        
        return results[1]  # Return count after cleanup
    
    async def allow_request(self, key: str, max_requests: int, window: int) -> bool:
        count = await self.get_requests(key, window)
        allowed = count <= max_requests
        
        async with self.redis.pipeline() as pipe:
            # Update metrics
            await pipe.hincrby(f"rate_limit:{key}:metrics", "total_requests", 1)
            if not allowed:
                await pipe.hincrby(f"rate_limit:{key}:metrics", "blocked_requests", 1)
            # Set metric expiry
            await pipe.expire(f"rate_limit:{key}:metrics", self.default_expiry)
            await pipe.execute()
        
        return allowed
    
    async def get_metrics(self, key: str) -> Dict[str, int]:
        metrics = await self.redis.hgetall(f"rate_limit:{key}:metrics")
        return {k: int(v) for k, v in metrics.items()}
    
    async def reset(self, key: str) -> None:
        async with self.redis.pipeline() as pipe:
            await pipe.delete(f"rate_limit:{key}:requests")
            await pipe.delete(f"rate_limit:{key}:metrics")
            await pipe.execute()
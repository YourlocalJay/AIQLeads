from redis import Redis
from datetime import datetime
from typing import Optional


class RateLimiter:
    def __init__(self, redis_client: Redis, prefix: str = "rate_limit"):
        self.redis = redis_client
        self.prefix = prefix

    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        current = int(datetime.now().timestamp())
        window_key = f"{self.prefix}:{key}:{current // window}"

        pipeline = self.redis.pipeline()
        pipeline.incr(window_key)
        pipeline.expire(window_key, window)
        count = pipeline.execute()[0]

        return count <= limit

    def get_remaining(self, key: str, window: int) -> Optional[int]:
        current = int(datetime.now().timestamp())
        window_key = f"{self.prefix}:{key}:{current // window}"
        count = self.redis.get(window_key)
        return int(count) if count else None

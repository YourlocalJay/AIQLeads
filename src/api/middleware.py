from fastapi import Request, HTTPException
from typing import Callable
from src.utils.rate_limiter import RateLimiter
from src.utils.metrics import MetricsCollector

class RateLimitMiddleware:
    def __init__(self, config: dict):
        self.config = config
        self.metrics = MetricsCollector()

    async def __call__(self, request: Request, call_next: Callable):
        endpoint = request.url.path
        limiter = RateLimiter(
            key=endpoint,
            **self.config.get(endpoint, self.config["default"])
        )

        try:
            if not await limiter.allow_request():
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            response = await call_next(request)
            await self.metrics.record_success(endpoint)
            return response

        except Exception as e:
            await self.metrics.record_error(endpoint, str(e))
            raise
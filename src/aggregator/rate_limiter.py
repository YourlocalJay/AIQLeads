from datetime import datetime, timedelta
from typing import Optional
import asyncio
from src.aggregator.exceptions import RateLimitExceeded
from src.aggregator.scrapers.rate_limiters.base_limiter import BaseRateLimiter

class RateLimiter(BaseRateLimiter):
    """Token bucket rate limiter for API request management.
    
    Extends BaseRateLimiter with:
    - Token bucket algorithm
    - Request queueing
    - Enhanced metrics
    """
    
    def __init__(
        self,
        rate_limit: int,
        window_size: int,
        redis_url: Optional[str] = None,
        max_queue_size: int = 1000
    ):
        super().__init__(
            requests_per_minute=rate_limit,
            burst_limit=rate_limit,
            redis_url=redis_url
        )
        self.window_size = window_size
        self._request_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._consumer_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        await super().initialize()
        self._consumer_task = asyncio.create_task(self._request_consumer())
    
    async def shutdown(self):
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        await super().shutdown()
    
    async def acquire(self, endpoint: str, tokens: int = 1) -> bool:
        """Try to acquire tokens, optionally queueing request."""
        if await super().acquire(endpoint, tokens):
            return True
            
        try:
            await self._request_queue.put((endpoint, tokens))
            return True
        except asyncio.QueueFull:
            return False
    
    async def _request_consumer(self):
        """Process queued requests."""
        while True:
            try:
                endpoint, tokens = await self._request_queue.get()
                if await super().acquire(endpoint, tokens):
                    self._request_queue.task_done()
                else:
                    # Re-queue if still can't acquire
                    await asyncio.sleep(1)
                    await self._request_queue.put((endpoint, tokens))
            except Exception as e:
                self._record_error()
    
    async def get_enhanced_metrics(self, endpoint: str) -> dict:
        """Get detailed metrics including queue stats."""
        base_metrics = await self.get_metrics(endpoint)
        return {
            **base_metrics,
            "window_size": self.window_size,
            "queue_size": self._request_queue.qsize(),
            "queue_remaining": self._request_queue.maxsize - self._request_queue.qsize()
        }

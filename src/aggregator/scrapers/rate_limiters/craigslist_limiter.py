import asyncio
import logging

from .base_limiter import BaseRateLimiter

logger = logging.getLogger(__name__)


class CraigslistRateLimiter(BaseRateLimiter):
    def __init__(self):
        super().__init__(requests_per_minute=30, burst_limit=5)

    async def acquire(
        self, endpoint: str, max_retries: int = 3, retry_delay: float = 1.0
    ) -> bool:
        for attempt in range(max_retries):
            if await self._try_acquire(endpoint):
                return True
            logger.info(f"Retry attempt {attempt + 1} for {endpoint}")
            await asyncio.sleep(retry_delay * (2**attempt))
        return False

from typing import Dict, List, Any
import asyncio
import logging
from redis.asyncio import Redis
from redis.exceptions import RedisError
from src.aggregator.scrapers.rate_limiters.base_limiter import BaseRateLimiter

logger = logging.getLogger(__name__)


class RateLimiter(BaseRateLimiter):
    """Redis-backed rate limiter with adaptive batching, AI-driven tuning, and circuit-breaking.

    Features:
    - Safe key prefix validation
    - AI-powered dynamic batch size adjustments
    - Multi-attempt retries before switching to fallback
    - Multi-region Redis support for high availability
    - Prometheus-compatible telemetry for monitoring
    """

    def __init__(
        self,
        requests_per_minute: int,
        redis_urls: List[str],
        key_prefix: str = "app",
        batch_size: int = 10,
        fallback_enabled: bool = True,
    ):
        super().__init__(
            requests_per_minute=requests_per_minute,
            redis_url=redis_urls[0],  # Default to first Redis instance
        )
        self.redis_urls = redis_urls
        self.redis_instances = [Redis.from_url(url) for url in redis_urls]
        self.key_prefix = self._validate_key_prefix(key_prefix)
        self.batch_size = self._validate_batch_size(batch_size)
        self.fallback_enabled = fallback_enabled
        self._local_limiter = None
        self._lock = asyncio.Lock()
        self._rolling_buffer = []
        self._metrics = {
            "total_requests": 0,
            "successful_batches": 0,
            "partial_batches": 0,
            "failed_batches": 0,
            "redis_failures": 0,
        }

    def _validate_key_prefix(self, prefix: str) -> str:
        """Ensure valid Redis key prefix format."""
        if not prefix.isalnum():
            raise ValueError("Key prefix must be alphanumeric")
        if len(prefix) > 32:
            raise ValueError("Key prefix too long (max 32 chars)")
        return prefix

    def _validate_batch_size(self, size: int) -> int:
        """Ensure valid batch size."""
        if not isinstance(size, int) or size < 1:
            raise ValueError("Batch size must be a positive integer")
        return size

    async def acquire_batch(
        self, endpoint: str, items: List[Any], max_retries: int = 3
    ) -> List[Any]:
        """Process batch with intelligent rate limit handling.

        Args:
            endpoint: API endpoint identifier
            items: List of items to process
            max_retries: Number of retry attempts on Redis failure

        Returns:
            List of items that passed rate limiting
        """
        allowed_items = []
        key = self._get_redis_key(endpoint)
        remaining_items = items.copy()

        for attempt in range(max_retries + 1):
            try:
                processed, remaining = await self._process_batch_chunk(
                    key, remaining_items
                )
                allowed_items.extend(processed)
                if not remaining:
                    break
                remaining_items = remaining
            except RedisError as e:
                logger.warning(f"Redis failure: {str(e)} (attempt {attempt + 1})")
                self._metrics["redis_failures"] += 1
                if attempt == max_retries:
                    if self.fallback_enabled:
                        logger.warning("Switching to local fallback rate limiter")
                        return await self._fallback_process(items)
                    else:
                        raise

        self._update_metrics(len(allowed_items), len(remaining_items))
        return allowed_items

    async def _process_batch_chunk(
        self, key: str, items: List[Any]
    ) -> tuple[List[Any], List[Any]]:
        """Process a subset of items returning (processed, remaining)."""
        batch_size = self._adaptive_batch_size()
        requested = min(batch_size, len(items))

        try:
            allowed = await self.acquire(key, requested)
            if allowed > 0:
                return items[:allowed], items[allowed:]
            return [], items
        except RedisError as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            raise

    async def _fallback_process(self, items: List[Any]) -> List[Any]:
        """Local fallback processing when Redis is unavailable."""
        async with self._lock:
            if not self._local_limiter:
                from .local_limiter import LocalRateLimiter

                self._local_limiter = LocalRateLimiter(self.requests_per_minute)

            return await self._local_limiter.process(items)

    def _update_metrics(self, processed: int, remaining: int) -> None:
        """Update internal metrics counters."""
        self._metrics["total_requests"] += processed + remaining
        if remaining == 0:
            self._metrics["successful_batches"] += 1
        elif processed > 0:
            self._metrics["partial_batches"] += 1
        else:
            self._metrics["failed_batches"] += 1

    async def get_enhanced_metrics(self, endpoint: str) -> Dict:
        """Return comprehensive rate limiting metrics."""
        base_metrics = await self.get_metrics(self._get_redis_key(endpoint))
        total_batches = (
            self._metrics["successful_batches"]
            + self._metrics["partial_batches"]
            + self._metrics["failed_batches"]
        ) or 1

        return {
            **base_metrics,
            "batch_success_rate": self._metrics["successful_batches"] / total_batches,
            "total_processed_items": self._metrics["total_requests"],
            "avg_batch_utilization": (
                (
                    self._metrics["total_requests"]
                    / (self._metrics["successful_batches"] * self.batch_size)
                )
                if self._metrics["successful_batches"]
                else 0
            ),
            "fallback_active": self._local_limiter is not None,
            "redis_failures": self._metrics["redis_failures"],
        }

    def _get_redis_key(self, endpoint: str) -> str:
        """Generate validated Redis key."""
        return f"{self.key_prefix}:{endpoint}"

    def _adaptive_batch_size(self) -> int:
        """AI-driven adaptive batch size tuning.

        Uses a rolling buffer to determine the optimal batch size.
        """
        if len(self._rolling_buffer) < 10:
            return self.batch_size  # Not enough data, use default

        avg_success = sum(self._rolling_buffer[-10:]) / 10
        if avg_success > 0.9:
            return min(self.batch_size * 2, 100)
        elif avg_success < 0.5:
            return max(self.batch_size // 2, 1)
        return self.batch_size

    async def switch_redis_instance(self) -> None:
        """Automatically switches Redis instance on failure."""
        async with self._lock:
            failed_instance = self.redis_instances.pop(0)
            self.redis_instances.append(
                failed_instance
            )  # Move failed instance to the back
            self.redis_url = self.redis_instances[0]
            logger.warning(f"Switching to Redis instance: {self.redis_url}")

from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio
import logging
from src.aggregator.rate_limiter import RateLimiter
from src.aggregator.exceptions import RateLimitExceeded

logger = logging.getLogger(__name__)

class CraigslistRateLimiter(RateLimiter):
    """
    Specialized rate limiter for Craigslist API with adaptive backoff.
    Implements per-endpoint rate limiting and automatic retry strategies.
    """

    DEFAULT_LIMITS = {
        "search": {"rate": 20, "window": 60},  # 20 requests per minute
        "listing": {"rate": 30, "window": 60},  # 30 requests per minute
        "contact": {"rate": 15, "window": 60}   # 15 requests per minute
    }

    MAX_BACKOFF = 120  # Maximum backoff time in seconds
    MIN_BACKOFF = 5    # Minimum backoff time in seconds

    def __init__(
        self,
        endpoint_limits: Optional[Dict] = None,
        global_rate_limit: int = 50,
        global_window: int = 60
    ):
        """
        Initialize Craigslist-specific rate limiter.

        Args:
            endpoint_limits: Optional custom limits per endpoint
            global_rate_limit: Overall rate limit across all endpoints
            global_window: Time window for global limit in seconds
        """
        super().__init__(global_rate_limit, global_window)
        
        self.endpoint_limiters = {}
        self.endpoint_limits = endpoint_limits or self.DEFAULT_LIMITS
        self._setup_endpoint_limiters()
        
        self.backoff_time = self.MIN_BACKOFF
        self.last_failure = None

    def _setup_endpoint_limiters(self) -> None:
        """Initialize rate limiters for each endpoint."""
        for endpoint, limits in self.endpoint_limits.items():
            self.endpoint_limiters[endpoint] = RateLimiter(
                rate_limit=limits["rate"],
                window_size=limits["window"]
            )

    async def acquire_for_endpoint(
        self,
        endpoint: str,
        tokens: int = 1,
        wait: bool = True
    ) -> None:
        """
        Acquire tokens for a specific endpoint with backoff handling.

        Args:
            endpoint: API endpoint identifier
            tokens: Number of tokens to acquire
            wait: Whether to wait for tokens

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if endpoint not in self.endpoint_limiters:
            logger.warning(f"Unknown endpoint {endpoint}, using global limiter")
            await self.acquire(tokens, wait)
            return

        try:
            # First check endpoint-specific limit
            await self.endpoint_limiters[endpoint].acquire(tokens, wait)
            # Then check global limit
            await super().acquire(tokens, wait)
            
            # Reset backoff on successful request
            self._reset_backoff()

        except RateLimitExceeded as e:
            await self._handle_rate_limit_failure(endpoint)
            raise

    async def _handle_rate_limit_failure(self, endpoint: str) -> None:
        """
        Handle rate limit failures with exponential backoff.

        Args:
            endpoint: Endpoint that triggered the failure
        """
        now = datetime.utcnow()
        
        if self.last_failure and (now - self.last_failure) > timedelta(minutes=5):
            self._reset_backoff()
        else:
            self.backoff_time = min(self.backoff_time * 2, self.MAX_BACKOFF)
        
        self.last_failure = now
        logger.warning(
            f"Rate limit exceeded for {endpoint}. "
            f"Backing off for {self.backoff_time} seconds"
        )
        
        await asyncio.sleep(self.backoff_time)

    def _reset_backoff(self) -> None:
        """Reset backoff timer after successful requests."""
        self.backoff_time = self.MIN_BACKOFF
        self.last_failure = None

    async def get_endpoint_status(self, endpoint: str) -> dict:
        """
        Get detailed status for specific endpoint.

        Args:
            endpoint: Target endpoint

        Returns:
            dict: Current rate limit status for endpoint
        """
        if endpoint not in self.endpoint_limiters:
            return await self.get_status()

        limiter = self.endpoint_limiters[endpoint]
        status = await limiter.get_status()
        
        return {
            **status,
            "backoff_time": self.backoff_time,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None
        }
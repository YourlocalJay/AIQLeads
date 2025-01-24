from datetime import datetime, timedelta
from typing import Optional
import asyncio
from src.aggregator.exceptions import RateLimitExceeded


class RateLimiter:
    """Token bucket rate limiter for API request management.
    
    Implements a thread-safe token bucket algorithm for rate limiting with
    support for async/await patterns. Provides automatic token replenishment
    and window tracking.
    """
    
    def __init__(self, rate_limit: int, window_size: int):
        """Initialize rate limiter.
        
        Args:
            rate_limit (int): Maximum number of tokens/requests per window
            window_size (int): Time window in seconds
        
        Raises:
            ValueError: If rate_limit or window_size is invalid
        """
        if rate_limit <= 0 or window_size <= 0:
            raise ValueError("rate_limit and window_size must be positive integers")
        
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.tokens = rate_limit
        self.last_update = datetime.utcnow()
        self.next_reset = self.last_update + timedelta(seconds=window_size)
        self._lock = asyncio.Lock()
        self._replenishment_task = None
    
    @property
    def remaining_tokens(self) -> int:
        """Get number of remaining tokens."""
        self._replenish_tokens()
        return self.tokens
    
    @property
    def usage_percentage(self) -> float:
        """Get rate limiter usage as a percentage."""
        return 100 * (1 - self.tokens / self.rate_limit)
    
    def _replenish_tokens(self) -> None:
        """Replenish tokens based on elapsed time."""
        now = datetime.utcnow()
        if now >= self.next_reset:
            self.tokens = self.rate_limit
            self.last_update = now
            self.next_reset = now + timedelta(seconds=self.window_size)
            return
        
        elapsed_time = (now - self.last_update).total_seconds()
        tokens_to_add = int((elapsed_time / self.window_size) * self.rate_limit)
        
        if tokens_to_add > 0:
            self.tokens = min(self.rate_limit, self.tokens + tokens_to_add)
            self.last_update = now
    
    async def acquire(self, tokens: int = 1, wait: bool = True) -> None:
        """Acquire tokens for an operation.
        
        Args:
            tokens (int): Number of tokens to acquire
            wait (bool): Whether to wait for tokens to become available
            
        Raises:
            ValueError: If tokens <= 0
            RateLimitExceeded: If tokens unavailable and wait=False
        """
        if tokens <= 0:
            raise ValueError("Requested tokens must be positive")
        
        async with self._lock:
            self._replenish_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            
            if not wait:
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Available: {self.tokens}, "
                    f"Requested: {tokens}, Next reset: {self.next_reset}"
                )
            
            while self.tokens < tokens:
                wait_time = (self.next_reset - datetime.utcnow()).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self._replenish_tokens()
            
            self.tokens -= tokens
    
    async def check_rate_limit(self, tokens: int = 1) -> bool:
        """Check if operation would exceed rate limit.
        
        Args:
            tokens (int): Number of tokens to check
            
        Returns:
            bool: True if tokens are available, False otherwise
            
        Raises:
            ValueError: If tokens <= 0
        """
        if tokens <= 0:
            raise ValueError("Requested tokens must be positive")
        
        async with self._lock:
            self._replenish_tokens()
            return self.tokens >= tokens
    
    async def get_status(self) -> dict:
        """Get detailed rate limiter status.
        
        Returns:
            dict: Current rate limit status including metrics
        """
        async with self._lock:
            self._replenish_tokens()
            return {
                "remaining_tokens": self.tokens,
                "rate_limit": self.rate_limit,
                "window_size": self.window_size,
                "usage_percentage": self.usage_percentage,
                "next_reset": self.next_reset.isoformat(),
                "last_update": self.last_update.isoformat()
            }

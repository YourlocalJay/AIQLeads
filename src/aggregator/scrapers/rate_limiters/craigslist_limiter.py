import base64

# Create Python code content
code = '''from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
from src.aggregator.rate_limiter import RateLimiter
from src.aggregator.exceptions import RateLimitExceeded

logger = logging.getLogger(__name__)

class CraigslistRateLimiter:
    """Specialized rate limiter for Craigslist API with endpoint-specific tracking."""
    
    ENDPOINT_LIMITS = {
        "search": {"rate": 20, "window": 60},   # 20 requests per minute
        "listing": {"rate": 30, "window": 60},  # 30 requests per minute
        "contact": {"rate": 15, "window": 60}   # 15 requests per minute
    }
    
    def __init__(self, global_rate: int = 50, global_window: int = 60):
        """Initialize rate limiters for each endpoint and global usage.
        
        Args:
            global_rate: Overall requests per window across all endpoints
            global_window: Time window in seconds for global limit
        """
        self.endpoint_limiters = {}
        self.global_limiter = RateLimiter(global_rate, global_window)
        self._initialize_limiters()
        
        self._last_request = {}
        self._locks = {}
        
    def _initialize_limiters(self) -> None:
        """Set up individual rate limiters for each endpoint."""
        for endpoint, config in self.ENDPOINT_LIMITS.items():
            self.endpoint_limiters[endpoint] = RateLimiter(
                config["rate"],
                config["window"]
            )
            self._last_request[endpoint] = None
            self._locks[endpoint] = asyncio.Lock()
            
    async def acquire(self, endpoint: str) -> None:
        """Acquire permission for an API request.
        
        Args:
            endpoint: Target API endpoint identifier
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if endpoint not in self.endpoint_limiters:
            logger.warning(f"Unknown endpoint {endpoint}, using global limiter only")
            await self.global_limiter.acquire()
            return
            
        async with self._locks[endpoint]:
            # Check endpoint-specific limit
            await self.endpoint_limiters[endpoint].acquire()
            # Check global limit
            await self.global_limiter.acquire()
            
            self._last_request[endpoint] = datetime.utcnow()
            
    async def get_status(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Args:
            endpoint: Optional specific endpoint to check
            
        Returns:
            Dict containing rate limit metrics
        """
        status = {
            "global": await self.global_limiter.get_status()
        }
        
        if endpoint:
            if endpoint not in self.endpoint_limiters:
                raise ValueError(f"Unknown endpoint: {endpoint}")
            status["endpoint"] = await self.endpoint_limiters[endpoint].get_status()
            
        else:
            status["endpoints"] = {}
            for ep, limiter in self.endpoint_limiters.items():
                status["endpoints"][ep] = await limiter.get_status()
                
        return status
        
    async def check_limit(self, endpoint: str) -> bool:
        """Check if a request would exceed rate limits.
        
        Args:
            endpoint: Target API endpoint
            
        Returns:
            bool: True if request is allowed, False if it would exceed limits
        """
        if endpoint not in self.endpoint_limiters:
            return await self.global_limiter.check_rate_limit()
            
        endpoint_allowed = await self.endpoint_limiters[endpoint].check_rate_limit()
        global_allowed = await self.global_limiter.check_rate_limit()
        
        return endpoint_allowed and global_allowed
        
    def get_wait_time(self, endpoint: str) -> float:
        """Calculate time until next request is allowed.
        
        Args:
            endpoint: Target API endpoint
            
        Returns:
            float: Seconds until next request is allowed
        """
        if endpoint not in self._last_request:
            return 0.0
            
        last_req = self._last_request[endpoint]
        if not last_req:
            return 0.0
            
        config = self.ENDPOINT_LIMITS[endpoint]
        next_allowed = last_req + timedelta(seconds=config["window"])
        
        wait_time = (next_allowed - datetime.utcnow()).total_seconds()
        return max(0.0, wait_time)
'''

# Convert to base64
content_bytes = code.encode('utf-8')
base64_bytes = base64.b64encode(content_bytes)
base64_string = base64_bytes.decode('utf-8')

# Return the properly formatted content
{"encoding": "base64", "content": base64_string}
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import logging
import signal
import json
from dataclasses import dataclass, asdict
import aioredis
import backoff

logger = logging.getLogger(__name__)

@dataclass
class RateLimitState:
    requests_per_minute: int
    burst_limit: int
    request_times: Dict[str, list[datetime]]
    
    def to_json(self) -> str:
        data = asdict(self)
        data["request_times"] = {
            k: [t.isoformat() for t in v]
            for k, v in self.request_times.items()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, data: str) -> "RateLimitState":
        parsed = json.loads(data)
        parsed["request_times"] = {
            k: [datetime.fromisoformat(t) for t in v]
            for k, v in parsed["request_times"].items()
        }
        return cls(**parsed)

class BaseRateLimiter(ABC):
    def __init__(
        self,
        requests_per_minute: int,
        burst_limit: Optional[int] = None,
        redis_url: Optional[str] = None
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit or requests_per_minute
        self._request_times: Dict[str, list[datetime]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._redis: Optional[aioredis.Redis] = None
        self._redis_url = redis_url
        
        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
            
    async def initialize(self):
        """Initialize rate limiter and restore state if available"""
        if self._redis_url:
            self._redis = await aioredis.from_url(self._redis_url)
            state = await self._load_state()
            if state:
                self.requests_per_minute = state.requests_per_minute
                self.burst_limit = state.burst_limit
                self._request_times = state.request_times
                
        self._cleanup_task = asyncio.create_task(self._start_periodic_cleanup())
        
    async def shutdown(self):
        """Gracefully shutdown the rate limiter"""
        self._shutdown_event.set()
        if self._cleanup_task:
            await self._cleanup_task
        if self._redis:
            await self._save_state()
            await self._redis.close()
            
    def _signal_handler(self, signum: int, frame: Any):
        """Handle shutdown signals"""
        asyncio.create_task(self.shutdown())
            
    async def _save_state(self):
        """Save rate limiter state to Redis"""
        if not self._redis:
            return
            
        state = RateLimitState(
            requests_per_minute=self.requests_per_minute,
            burst_limit=self.burst_limit,
            request_times=self._request_times
        )
        await self._redis.set("rate_limiter_state", state.to_json())
        
    async def _load_state(self) -> Optional[RateLimitState]:
        """Load rate limiter state from Redis"""
        if not self._redis:
            return None
            
        state_data = await self._redis.get("rate_limiter_state")
        if state_data:
            return RateLimitState.from_json(state_data.decode())
        return None
        
    async def _start_periodic_cleanup(self, interval: int = 60):
        """Start periodic cleanup task"""
        while not self._shutdown_event.is_set():
            try:
                await self._periodic_cleanup()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                
    async def _periodic_cleanup(self):
        """Clean up old requests across all endpoints"""
        for endpoint in list(self._request_times.keys()):
            await self._cleanup_endpoint(endpoint)
            
    async def _cleanup_endpoint(self, endpoint: str):
        """Clean up old requests for specific endpoint"""
        async with self._locks.get(endpoint, asyncio.Lock()):
            self._cleanup_old_requests(endpoint)
            if self._redis:
                await self._save_state()
                
    def _cleanup_old_requests(self, endpoint: str) -> None:
        """Remove requests older than 1 minute"""
        if endpoint not in self._request_times:
            return
            
        current_time = datetime.now()
        self._request_times[endpoint] = [
            timestamp for timestamp in self._request_times[endpoint]
            if current_time - timestamp < timedelta(minutes=1)
        ]
        
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        max_time=30
    )
    async def acquire(
        self,
        endpoint: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """Acquire rate limit token with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                if await self._try_acquire(endpoint):
                    return True
                    
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)
                    logger.info(f"Rate limit retry for {endpoint} in {delay}s")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error acquiring rate limit: {e}")
                raise
                
        return False
        
    async def _try_acquire(self, endpoint: str) -> bool:
        """Try to acquire rate limit token"""
        if endpoint not in self._locks:
            self._locks[endpoint] = asyncio.Lock()
            
        async with self._locks[endpoint]:
            current_requests = len(self._request_times.get(endpoint, []))
            if current_requests >= self.burst_limit:
                logger.warning(f"Rate limit exceeded for {endpoint}")
                return False
                
            self._request_times.setdefault(endpoint, []).append(datetime.now())
            if self._redis:
                await self._save_state()
                
            logger.info(f"Token acquired for {endpoint}")
            return True
            
    async def release(self, endpoint: str) -> None:
        """Release rate limit token"""
        if endpoint in self._locks:
            async with self._locks[endpoint]:
                self._cleanup_old_requests(endpoint)
                if self._redis:
                    await self._save_state()

    async def get_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get rate limit metrics for endpoint"""
        async with self._locks.get(endpoint, asyncio.Lock()):
            self._cleanup_old_requests(endpoint)
            current_requests = len(self._request_times.get(endpoint, []))
            return {
                "requests_per_minute": self.requests_per_minute,
                "burst_limit": self.burst_limit,
                "current_requests": current_requests,
                "remaining": self.burst_limit - current_requests
            }
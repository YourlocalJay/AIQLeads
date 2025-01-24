from abc import ABC, abstractmethod
from typing import Optional, Dict
import asyncio
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class BaseRateLimiter(ABC):
    def __init__(self, requests_per_minute: int, burst_limit: Optional[int] = None):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit or requests_per_minute
        self._request_times: Dict[str, list[datetime]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        asyncio.create_task(self._start_periodic_cleanup())
        
    async def _start_periodic_cleanup(self, interval: int = 60):
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup(interval))
        
    async def _periodic_cleanup(self, interval: int):
        while True:
            try:
                for endpoint in list(self._request_times.keys()):
                    await self._cleanup_endpoint(endpoint)
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                
    async def _cleanup_endpoint(self, endpoint: str):
        async with self._locks.get(endpoint, asyncio.Lock()):
            self._cleanup_old_requests(endpoint)
            
    def _cleanup_old_requests(self, endpoint: str) -> None:
        if endpoint not in self._request_times:
            return
        
        current_time = datetime.now()
        self._request_times[endpoint] = [
            timestamp for timestamp in self._request_times[endpoint]
            if current_time - timestamp < timedelta(minutes=1)
        ]

    @abstractmethod
    async def acquire(self, endpoint: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        pass
        
    async def _try_acquire(self, endpoint: str) -> bool:
        if endpoint not in self._locks:
            self._locks[endpoint] = asyncio.Lock()
            
        async with self._locks[endpoint]:
            current_requests = len(self._request_times.get(endpoint, []))
            if current_requests >= self.burst_limit:
                logger.warning(f"Rate limit exceeded for {endpoint}")
                return False
                
            self._request_times.setdefault(endpoint, []).append(datetime.now())
            logger.info(f"Token acquired for {endpoint}")
            return True
            
    async def release(self, endpoint: str) -> None:
        if endpoint in self._locks:
            async with self._locks[endpoint]:
                self._cleanup_old_requests(endpoint)
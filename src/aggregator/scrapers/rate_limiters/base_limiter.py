from abc import ABC
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
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
    circuit_breaker_trips: int = 0
    last_error_time: Optional[datetime] = None

    def to_json(self) -> str:
        data = asdict(self)
        data["request_times"] = {
            k: [t.isoformat() for t in v] for k, v in self.request_times.items()
        }
        if self.last_error_time:
            data["last_error_time"] = self.last_error_time.isoformat()
        return json.dumps(data)

    @classmethod
    def from_json(cls, data: str) -> "RateLimitState":
        parsed = json.loads(data)
        parsed["request_times"] = {
            k: [datetime.fromisoformat(t) for t in v]
            for k, v in parsed["request_times"].items()
        }
        if parsed.get("last_error_time"):
            parsed["last_error_time"] = datetime.fromisoformat(
                parsed["last_error_time"]
            )
        return cls(**parsed)


class BaseRateLimiter(ABC):
    def __init__(
        self,
        requests_per_minute: int,
        burst_limit: Optional[int] = None,
        redis_url: Optional[str] = None,
        redis_failover_urls: Optional[list[str]] = None,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit or requests_per_minute
        self._request_times: Dict[str, list[datetime]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._redis: Optional[aioredis.Redis] = None
        self._redis_url = redis_url
        self._redis_failover_urls = redis_failover_urls or []
        self._circuit_breaker = {
            "trips": 0,
            "threshold": circuit_breaker_threshold,
            "timeout": circuit_breaker_timeout,
            "last_error": None,
        }

        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    async def initialize(self):
        if self._redis_url:
            await self._connect_redis()
            state = await self._load_state()
            if state:
                self.requests_per_minute = state.requests_per_minute
                self.burst_limit = state.burst_limit
                self._request_times = state.request_times
                self._circuit_breaker["trips"] = state.circuit_breaker_trips
                self._circuit_breaker["last_error"] = state.last_error_time

        self._cleanup_task = asyncio.create_task(self._start_periodic_cleanup())

    @backoff.on_exception(backoff.expo, aioredis.RedisError, max_tries=3)
    async def _connect_redis(self):
        if not self._redis or not await self._redis.ping():
            for url in [self._redis_url] + self._redis_failover_urls:
                try:
                    self._redis = await aioredis.from_url(
                        url, max_connections=10, socket_timeout=5.0
                    )
                    if await self._redis.ping():
                        logger.info(f"Connected to Redis at {url}")
                        break
                except:
                    continue
            else:
                raise aioredis.RedisError("Failed to connect to any Redis instance")

    async def shutdown(self):
        self._shutdown_event.set()
        if self._cleanup_task:
            await self._cleanup_task
        if self._redis:
            await self._save_state()
            await self._redis.close()

    async def _save_state(self):
        if not self._redis:
            return

        state = RateLimitState(
            requests_per_minute=self.requests_per_minute,
            burst_limit=self.burst_limit,
            request_times=self._request_times,
            circuit_breaker_trips=self._circuit_breaker["trips"],
            last_error_time=self._circuit_breaker["last_error"],
        )
        async with self._redis.pipeline() as pipe:
            await pipe.set("rate_limiter_state", state.to_json())
            await pipe.expire("rate_limiter_state", 3600)
            await pipe.execute()

    async def acquire(self, endpoint: str, max_retries: int = 3) -> bool:
        if self._is_circuit_open():
            return False

        try:
            async with self._locks.get(endpoint, asyncio.Lock()):
                current_requests = len(self._request_times.get(endpoint, []))
                if current_requests >= self.burst_limit:
                    return False

                self._request_times.setdefault(endpoint, []).append(datetime.now())
                if self._redis:
                    await self._save_state()
                return True

        except Exception as e:
            self._record_error()
            logger.error(f"Error acquiring rate limit: {e}")
            return False

    def _is_circuit_open(self) -> bool:
        if self._circuit_breaker["trips"] >= self._circuit_breaker["threshold"]:
            if self._circuit_breaker["last_error"]:
                elapsed = datetime.now() - self._circuit_breaker["last_error"]
                if elapsed.total_seconds() < self._circuit_breaker["timeout"]:
                    return True
            self._circuit_breaker["trips"] = 0
        return False

    def _record_error(self) -> None:
        self._circuit_breaker["trips"] += 1
        self._circuit_breaker["last_error"] = datetime.now()

    async def get_metrics(self, endpoint: str) -> Dict[str, Any]:
        async with self._locks.get(endpoint, asyncio.Lock()):
            self._cleanup_old_requests(endpoint)
            current_requests = len(self._request_times.get(endpoint, []))
            return {
                "requests_per_minute": self.requests_per_minute,
                "burst_limit": self.burst_limit,
                "current_requests": current_requests,
                "remaining": self.burst_limit - current_requests,
                "circuit_breaker_trips": self._circuit_breaker["trips"],
                "circuit_status": "open" if self._is_circuit_open() else "closed",
            }

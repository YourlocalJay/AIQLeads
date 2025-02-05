from typing import Dict, Optional, Any
from datetime import datetime
import logging
import asyncio
from fastapi import Request

from src.config.settings import get_settings
from src.utils.decorators import async_timed
from src.utils.retry import with_retry_decorator, CircuitBreaker, with_circuit_breaker

logger = logging.getLogger(__name__)


class HealthService:
    """Service for checking health status of system components with retry logic"""

    def __init__(self, request: Request):
        self.settings = get_settings()
        self._last_check: Optional[Dict[str, Any]] = None
        self._cache_duration = 60
        self.request = request

        # Initialize circuit breakers for each service
        self.db_circuit = CircuitBreaker(
            failure_threshold=3, reset_timeout=30.0, half_open_timeout=15.0
        )
        self.cache_circuit = CircuitBreaker(
            failure_threshold=3, reset_timeout=30.0, half_open_timeout=15.0
        )
        self.search_circuit = CircuitBreaker(
            failure_threshold=3, reset_timeout=30.0, half_open_timeout=15.0
        )

    def _on_retry(self, error: Exception, attempt: int) -> None:
        """Callback for retry attempts"""
        logger.warning(f"Retry attempt {attempt} failed with error: {str(error)}")

    async def _get_fallback_status(self) -> Dict[str, Any]:
        """Fallback status when service is unavailable"""
        return {
            "status": "unavailable",
            "message": "Service temporarily unavailable due to circuit breaker",
            "circuit_state": "open",
        }

    @async_timed()
    @with_retry_decorator(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        backoff_factor=2.0,
        on_retry=_on_retry,
    )
    @with_circuit_breaker(db_circuit, fallback=_get_fallback_status)
    async def check_database(self) -> Dict[str, Any]:
        """Check database connection and basic functionality with retry logic"""
        try:
            pool = self.request.app.state.db_pool
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

                pool_stats = {
                    "size": pool.get_size(),
                    "free_size": pool.get_free_size(),
                }

                return {
                    "status": "healthy",
                    "pool_stats": pool_stats,
                    "latency_ms": (
                        self.request.state.process_time * 1000
                        if hasattr(self.request.state, "process_time")
                        else None
                    ),
                }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e), "type": type(e).__name__}

    @async_timed()
    @with_retry_decorator(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        backoff_factor=2.0,
        on_retry=_on_retry,
    )
    @with_circuit_breaker(cache_circuit, fallback=_get_fallback_status)
    async def check_cache(self) -> Dict[str, Any]:
        """Check Redis cache connection and functionality with retry logic"""
        try:
            redis = self.request.app.state.redis_pool
            await redis.ping()

            info = await redis.info()
            memory_stats = info.get("memory", {})

            return {
                "status": "healthy",
                "used_memory": memory_stats.get("used_memory_human"),
                "peak_memory": memory_stats.get("used_memory_peak_human"),
                "latency_ms": (
                    self.request.state.process_time * 1000
                    if hasattr(self.request.state, "process_time")
                    else None
                ),
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e), "type": type(e).__name__}

    @async_timed()
    @with_retry_decorator(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        backoff_factor=2.0,
        on_retry=_on_retry,
    )
    @with_circuit_breaker(search_circuit, fallback=_get_fallback_status)
    async def check_search(self) -> Dict[str, Any]:
        """Check Elasticsearch connection and cluster health with retry logic"""
        try:
            es = self.request.app.state.es_client
            health = await es.cluster.health()
            stats = await es.nodes.stats()
            nodes_stats = stats.get("nodes", {})

            return {
                "status": "healthy",
                "cluster_status": health["status"],
                "active_shards": health["active_shards"],
                "nodes": len(nodes_stats),
                "latency_ms": (
                    self.request.state.process_time * 1000
                    if hasattr(self.request.state, "process_time")
                    else None
                ),
            }
        except Exception as e:
            logger.error(f"Search health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e), "type": type(e).__name__}

    async def check_all_services(self) -> Dict[str, Any]:
        """Perform health check of all services with caching and retry logic"""
        now = datetime.now()

        if (
            self._last_check
            and (now - self._last_check["timestamp"]).seconds < self._cache_duration
        ):
            return self._last_check["status"]

        results = await asyncio.gather(
            self.check_database(),
            self.check_cache(),
            self.check_search(),
            return_exceptions=True,
        )

        status = {
            "database": (
                results[0]
                if not isinstance(results[0], Exception)
                else {"status": "unhealthy", "error": str(results[0])}
            ),
            "cache": (
                results[1]
                if not isinstance(results[1], Exception)
                else {"status": "unhealthy", "error": str(results[1])}
            ),
            "search": (
                results[2]
                if not isinstance(results[2], Exception)
                else {"status": "unhealthy", "error": str(results[2])}
            ),
            "timestamp": now.isoformat(),
            "environment": self.settings.ENV,
        }

        status["overall_health"] = all(
            service["status"] == "healthy"
            for service in [status["database"], status["cache"], status["search"]]
        )

        status["circuit_breakers"] = {
            "database": {
                "state": self.db_circuit.state,
                "failures": self.db_circuit.failures,
            },
            "cache": {
                "state": self.cache_circuit.state,
                "failures": self.cache_circuit.failures,
            },
            "search": {
                "state": self.search_circuit.state,
                "failures": self.search_circuit.failures,
            },
        }

        self._last_check = {"timestamp": now, "status": status}

        return status

    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed health metrics for all services"""
        basic_status = await self.check_all_services()

        return {
            **basic_status,
            "api_version": "1.0.0",
            "settings": {
                "environment": self.settings.ENV,
                "debug_mode": self.settings.DEBUG,
                "database": {
                    "host": self.settings.DB_HOST,
                    "port": self.settings.DB_PORT,
                    "pool_size": self.settings.DB_POOL_SIZE,
                    "max_overflow": self.settings.DB_MAX_OVERFLOW,
                },
                "cache": {
                    "host": self.settings.REDIS_HOST,
                    "port": self.settings.REDIS_PORT,
                },
                "search": {
                    "host": self.settings.ELASTICSEARCH_HOST,
                    "port": self.settings.ELASTICSEARCH_PORT,
                },
            },
        }

from typing import Dict, Optional, Any
from datetime import datetime
import logging
from fastapi import Request
from elasticsearch import AsyncElasticsearch
from src.config.settings import get_settings
from src.utils.decorators import async_timed

logger = logging.getLogger(__name__)

class HealthService:
    """Service for checking health status of system components"""

    def __init__(self, request: Request):
        self.settings = get_settings()
        self._last_check: Optional[Dict[str, Any]] = None
        self._cache_duration = 60
        self.request = request

    @async_timed()
    async def check_database(self) -> Dict[str, Any]:
        """Check database connection and basic functionality"""
        try:
            pool = self.request.app.state.db_pool
            async with pool.acquire() as conn:
                # Check basic query execution
                await conn.fetchval('SELECT 1')
                
                # Get connection pool stats
                pool_stats = {
                    'size': pool.get_size(),
                    'free_size': pool.get_free_size(),
                }
                
                return {
                    'status': 'healthy',
                    'pool_stats': pool_stats,
                    'latency_ms': self.request.state.process_time * 1000 if hasattr(self.request.state, 'process_time') else None
                }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'type': type(e).__name__
            }

    @async_timed()
    async def check_cache(self) -> Dict[str, Any]:
        """Check Redis cache connection and functionality"""
        try:
            redis = self.request.app.state.redis_pool
            
            # Check basic operations
            await redis.ping()
            
            # Get Redis info
            info = await redis.info()
            memory_stats = info.get('memory', {})
            
            return {
                'status': 'healthy',
                'used_memory': memory_stats.get('used_memory_human'),
                'peak_memory': memory_stats.get('used_memory_peak_human'),
                'latency_ms': self.request.state.process_time * 1000 if hasattr(self.request.state, 'process_time') else None
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'type': type(e).__name__
            }

    @async_timed()
    async def check_search(self) -> Dict[str, Any]:
        """Check Elasticsearch connection and cluster health"""
        try:
            es = self.request.app.state.es_client
            
            # Get cluster health
            health = await es.cluster.health()
            
            # Get node stats
            stats = await es.nodes.stats()
            nodes_stats = stats.get('nodes', {})
            
            return {
                'status': 'healthy',
                'cluster_status': health['status'],
                'active_shards': health['active_shards'],
                'nodes': len(nodes_stats),
                'latency_ms': self.request.state.process_time * 1000 if hasattr(self.request.state, 'process_time') else None
            }
        except Exception as e:
            logger.error(f"Search health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'type': type(e).__name__
            }

    async def check_all_services(self) -> Dict[str, Any]:
        """
        Perform health check of all services with caching
        Returns:
            Dict containing health status of all services
        """
        now = datetime.now()
        
        # Return cached result if available and fresh
        if self._last_check and \
           (now - self._last_check['timestamp']).seconds < self._cache_duration:
            return self._last_check['status']

        # Perform health checks
        status = {
            'database': await self.check_database(),
            'cache': await self.check_cache(),
            'search': await self.check_search(),
            'timestamp': now.isoformat(),
            'environment': self.settings.ENV
        }

        # Calculate overall status
        status['overall_health'] = all(
            service['status'] == 'healthy'
            for service in [status['database'], status['cache'], status['search']]
        )

        # Cache the result
        self._last_check = {
            'timestamp': now,
            'status': status
        }

        return status

    async def get_detailed_status(self) -> Dict[str, Any]:
        """
        Get detailed health metrics for all services
        Returns:
            Dict containing detailed health metrics
        """
        basic_status = await self.check_all_services()
        
        # Add system configuration details
        detailed_status = {
            **basic_status,
            'api_version': '1.0.0',
            'settings': {
                'environment': self.settings.ENV,
                'debug_mode': self.settings.DEBUG,
                'database': {
                    'host': self.settings.DB_HOST,
                    'port': self.settings.DB_PORT,
                    'pool_size': self.settings.DB_POOL_SIZE,
                    'max_overflow': self.settings.DB_MAX_OVERFLOW
                },
                'cache': {
                    'host': self.settings.REDIS_HOST,
                    'port': self.settings.REDIS_PORT
                },
                'search': {
                    'host': self.settings.ELASTICSEARCH_HOST,
                    'port': self.settings.ELASTICSEARCH_PORT
                }
            }
        }

        return detailed_status
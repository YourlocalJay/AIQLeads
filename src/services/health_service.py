from typing import Dict, Optional
from datetime import datetime
import asyncpg
import aioredis
from elasticsearch import AsyncElasticsearch
from src.config.settings import get_settings

class HealthService:
    def __init__(self):
        self.settings = get_settings()
        self._last_check: Optional[Dict] = None
        self._cache_duration = 60

    async def check_database(self) -> Dict:
        try:
            conn = await asyncpg.connect(
                host=self.settings.DB_HOST,
                port=self.settings.DB_PORT,
                user=self.settings.DB_USER,
                password=self.settings.DB_PASSWORD,
                database=self.settings.DB_NAME
            )
            await conn.execute('SELECT 1')
            await conn.close()
            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def check_cache(self) -> Dict:
        try:
            redis = await aioredis.create_redis_pool(
                f'redis://{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}'
            )
            await redis.ping()
            redis.close()
            await redis.wait_closed()
            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def check_search(self) -> Dict:
        try:
            es = AsyncElasticsearch([
                f'http://{self.settings.ELASTICSEARCH_HOST}:'
                f'{self.settings.ELASTICSEARCH_PORT}'
            ])
            health = await es.cluster.health()
            await es.close()
            return {'status': 'healthy', 'cluster_status': health['status']}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def check_all_services(self) -> Dict:
        """Perform basic health check of all services"""
        now = datetime.now()
        
        if self._last_check and \
           (now - self._last_check['timestamp']).seconds < self._cache_duration:
            return self._last_check['status']

        status = {
            'database': await self.check_database(),
            'cache': await self.check_cache(),
            'search': await self.check_search(),
            'timestamp': now.isoformat()
        }

        self._last_check = {
            'timestamp': now,
            'status': status
        }

        return status

    async def get_detailed_status(self) -> Dict:
        """Get detailed health metrics for all services"""
        basic_status = await self.check_all_services()
        
        return {
            **basic_status,
            'environment': self.settings.ENV,
            'api_version': '1.0.0',
            'detailed_checks': {
                'database': {
                    'host': self.settings.DB_HOST,
                    'port': self.settings.DB_PORT,
                    'pool_size': self.settings.DB_POOL_SIZE
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
from typing import Dict
from fastapi import FastAPI, Request, Response
from datetime import datetime
import asyncpg
import aioredis
from elasticsearch import AsyncElasticsearch
from src.config.settings import get_settings

class HealthCheck:
    def __init__(self):
        self.settings = get_settings()
        self._last_check = {}
        self._cache_duration = 60  # Cache health check results for 60 seconds

    async def check_postgres(self) -> Dict:
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
            return {'status': 'healthy', 'latency': 'ok'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def check_redis(self) -> Dict:
        try:
            redis = await aioredis.create_redis_pool(
                f'redis://{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}'
            )
            await redis.ping()
            redis.close()
            await redis.wait_closed()
            return {'status': 'healthy', 'latency': 'ok'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def check_elasticsearch(self) -> Dict:
        try:
            es = AsyncElasticsearch([
                f'http://{self.settings.ELASTICSEARCH_HOST}:'
                f'{self.settings.ELASTICSEARCH_PORT}'
            ])
            health = await es.cluster.health()
            await es.close()
            return {
                'status': 'healthy',
                'cluster_status': health['status']
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def get_health_status(self) -> Dict:
        now = datetime.now()
        if self._last_check.get('timestamp'):
            time_diff = (now - self._last_check['timestamp']).seconds
            if time_diff < self._cache_duration:
                return self._last_check['status']

        status = {
            'postgres': await self.check_postgres(),
            'redis': await self.check_redis(),
            'elasticsearch': await self.check_elasticsearch(),
            'timestamp': now.isoformat()
        }

        self._last_check = {
            'timestamp': now,
            'status': status
        }

        return status

async def health_check_middleware(request: Request, call_next) -> Response:
    if request.url.path == '/health':
        health_check = HealthCheck()
        return Response(
            content=str(await health_check.get_health_status()),
            media_type='application/json'
        )
    return await call_next(request)

def init_health_check(app: FastAPI) -> None:
    app.middleware('http')(health_check_middleware)
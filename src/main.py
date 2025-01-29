from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncpg
import aioredis
from elasticsearch import AsyncElasticsearch
from contextlib import asynccontextmanager

from src.config.settings import get_settings
from src.api.v1.endpoints import api_router
from src.core.middleware import RequestLoggingMiddleware, ResponseTimeMiddleware

async def create_db_pool():
    """Create and configure database connection pool"""
    settings = get_settings()
    try:
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=settings.DB_POOL_SIZE,
            max_inactive_connection_lifetime=300
        )
        logging.info("Database pool created successfully")
        return pool
    except Exception as e:
        logging.error(f"Failed to create database pool: {e}")
        raise

async def create_redis_pool():
    """Create and configure Redis connection pool"""
    settings = get_settings()
    try:
        redis = await aioredis.create_redis_pool(
            f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
            password=settings.REDIS_PASSWORD,
            maxsize=20
        )
        logging.info("Redis pool created successfully")
        return redis
    except Exception as e:
        logging.error(f"Failed to create Redis pool: {e}")
        raise

async def create_elasticsearch_client():
    """Create and configure Elasticsearch client"""
    settings = get_settings()
    try:
        es = AsyncElasticsearch([
            f'http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}'
        ])
        await es.info()
        logging.info("Elasticsearch client created successfully")
        return es
    except Exception as e:
        logging.error(f"Failed to create Elasticsearch client: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and resource connections"""
    settings = get_settings()
    
    # Startup
    try:
        # Create connection pools
        app.state.db_pool = await create_db_pool()
        app.state.redis_pool = await create_redis_pool()
        app.state.es_client = await create_elasticsearch_client()
        
        logging.info("All service connections established")
        yield
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        raise
    finally:
        # Shutdown
        if hasattr(app.state, 'db_pool'):
            await app.state.db_pool.close()
            logging.info("Database pool closed")
            
        if hasattr(app.state, 'redis_pool'):
            app.state.redis_pool.close()
            await app.state.redis_pool.wait_closed()
            logging.info("Redis pool closed")
            
        if hasattr(app.state, 'es_client'):
            await app.state.es_client.close()
            logging.info("Elasticsearch client closed")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title='AIQLeads API',
        description='Lead marketplace for real estate professionals',
        version='1.0.0',
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ResponseTimeMiddleware)
    
    # Add routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    return app

app = create_app()

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
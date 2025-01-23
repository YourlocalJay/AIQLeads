from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.api.middleware.health_check import init_health_check
from src.api.v1.endpoints import health

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title='AIQLeads API',
        description='Lead marketplace for real estate professionals',
        version='1.0.0',
        debug=settings.DEBUG
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    
    # Initialize health check
    init_health_check(app)
    
    # Register routers
    app.include_router(
        health.router,
        prefix=f'{settings.API_V1_PREFIX}',
        tags=['Health']
    )
    
    return app

app = create_app()

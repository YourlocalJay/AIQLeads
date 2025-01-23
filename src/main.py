from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.api.v1.endpoints import api_router

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
    
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    return app

app = create_app()
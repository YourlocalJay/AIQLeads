from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from datetime import datetime
from src.config.settings import get_settings
from src.services.health_service import HealthService

router = APIRouter(prefix='/health', tags=['Health'])
settings = get_settings()

@router.get('/')
async def check_health() -> Dict:
    """Check health status of all system components"""
    health_service = HealthService()
    return await health_service.check_all_services()

@router.get('/detailed')
async def detailed_health() -> Dict:
    """Get detailed health metrics for all services"""
    health_service = HealthService()
    return await health_service.get_detailed_status()
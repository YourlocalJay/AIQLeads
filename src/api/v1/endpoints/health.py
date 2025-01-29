from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
from datetime import datetime

from src.config.settings import get_settings
from src.services.health_service import HealthService

router = APIRouter(prefix='/health', tags=['Health'])
settings = get_settings()

async def get_health_service(request: Request) -> HealthService:
    """Dependency for creating HealthService instance"""
    return HealthService(request)

@router.get('/')
async def check_health(
    health_service: HealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Check health status of all system components
    Returns:
        Dict containing health status of all services
    """
    return await health_service.check_all_services()

@router.get('/detailed')
async def detailed_health(
    health_service: HealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Get detailed health metrics for all services
    Returns:
        Dict containing detailed health metrics and system information
    """
    return await health_service.get_detailed_status()
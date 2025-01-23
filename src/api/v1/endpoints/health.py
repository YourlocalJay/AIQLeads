from fastapi import APIRouter, Depends
from typing import Dict
from src.api.middleware.health_check import HealthCheck

router = APIRouter()

@router.get('/health')
async def health_check() -> Dict:
    """Get system health status"""
    health_check = HealthCheck()
    return await health_check.get_health_status()

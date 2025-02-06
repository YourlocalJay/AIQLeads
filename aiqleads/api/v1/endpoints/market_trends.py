from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.user_service import UserService
from aiqleads.services.market_trends_service import MarketTrendsService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/market-trends", tags=["market-trends"])

# Initialize services
market_trends_service = MarketTrendsService()
user_service = UserService()
tracker = ProjectTracker()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class MarketTrend(BaseModel):
    id: str
    name: str
    confidence: float = Field(..., ge=0, le=1)
    impact: str
    timeframe: str
    metrics: Dict[str, float]

class Forecast(BaseModel):
    id: str
    metric: str
    predicted_value: float
    probability: float = Field(..., ge=0, le=1)
    confidence_interval: Dict[str, float]

class Opportunity(BaseModel):
    id: str
    name: str
    value: float
    probability: float = Field(..., ge=0, le=1)
    timeframe: str
    risk_level: str

@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    try:
        yield
        tracker.log_operation(
            component_id=component_id,
            operation=operation_name,
            status="success",
            details=kwargs
        )
    except Exception as e:
        tracker.log_operation(
            component_id=component_id,
            operation=operation_name,
            status="error",
            details={**kwargs, "error": str(e)}
        )
        logger.error(f"Operation failed: {operation_name}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/trends", response_model=List[MarketTrend], dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)
async def get_market_trends(token: str = Depends(oauth2_scheme)):
    async with track_operation("market-trends/trends", "Get Market Trends"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return await market_trends_service.analyze_trends(user_id=user.id)

@router.get("/forecasts", response_model=List[Forecast], dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=600)
async def get_forecasts(token: str = Depends(oauth2_scheme)):
    async with track_operation("market-trends/forecasts", "Get Forecasts"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return await market_trends_service.generate_forecasts(user_id=user.id)

@router.get("/opportunities", response_model=List[Opportunity], dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=1800)
async def get_opportunities(token: str = Depends(oauth2_scheme)):
    async with track_operation("market-trends/opportunities", "Get Opportunities"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return await market_trends_service.identify_opportunities(user_id=user.id)

@router.post("/subscribe", dependencies=[Depends(RateLimiter(requests_per_minute=10))], status_code=status.HTTP_201_CREATED)
async def subscribe_to_alerts(alert_types: List[str], frequency: str, token: str = Depends(oauth2_scheme)):
    async with track_operation("market-trends/subscribe", "Subscribe to Alerts", alert_types=alert_types, frequency=frequency):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        subscription = await market_trends_service.create_alert_subscription(user_id=user.id, alert_types=alert_types, frequency=frequency)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"status": "success", "subscription_id": subscription.id}
        )

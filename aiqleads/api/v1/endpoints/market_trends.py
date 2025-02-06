from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.market_trends_service import MarketTrendsService
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from contextlib import asynccontextmanager
from enum import Enum

router = APIRouter(prefix="/api/v1/market-trends", tags=["market-trends"])

# Initialize services
market_trends_service = MarketTrendsService()
user_service = UserService()
tracker = ProjectTracker()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 📌 Enums and Constants
class TrendImpact(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class CompetitionLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TimeGranularity(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

# 📌 Base Models
class TimeRange(BaseModel):
    start_date: datetime
    end_date: datetime = Field(default_factory=datetime.utcnow)
    granularity: TimeGranularity = Field(TimeGranularity.DAY)

    @validator("end_date")
    def end_date_not_in_future(cls, v):
        if v > datetime.utcnow():
            raise ValueError("end_date cannot be in the future")
        return v

    @validator("start_date")
    def start_date_not_after_end_date(cls, v, values):
        if "end_date" in values and v > values["end_date"]:
            raise ValueError("start_date must be before end_date")
        if v < datetime.utcnow() - timedelta(days=365):
            raise ValueError("start_date cannot be more than 1 year ago")
        return v

class DataPoint(BaseModel):
    date: datetime
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MarketTrend(BaseModel):
    id: str
    name: str
    description: str
    confidence: float = Field(..., ge=0, le=1)
    impact: TrendImpact
    affected_segments: List[str]
    predicted_duration: Optional[int] = Field(None, description="Duration in days")
    data_points: List[DataPoint]
    recommendations: List[str]

class Forecast(BaseModel):
    id: str
    metric: str
    current_value: float
    predicted_value: float
    confidence_interval: List[float] = Field(..., min_items=2, max_items=2)
    factors: List[Dict[str, Any]]
    timeline: str
    probability: float = Field(..., ge=0, le=1)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Opportunity(BaseModel):
    id: str
    name: str
    description: str
    value: float = Field(..., ge=0)
    probability: float = Field(..., ge=0, le=1)
    market_size: float = Field(..., ge=0)
    competition_level: CompetitionLevel
    required_resources: List[str]
    timeline: str
    risk_factors: List[Dict[str, float]]

class MarketAlert(BaseModel):
    id: str
    type: str
    severity: AlertSeverity
    title: str
    description: str
    probability: float = Field(..., ge=0, le=1)
    detection_time: datetime = Field(default_factory=datetime.utcnow)
    recommended_actions: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

# 📌 Helper Functions
@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Context manager for operation tracking"""
    try:
        yield
        tracker.update_status(
            component_id=component_id,
            status="🟢 Active",
            notes=f"{operation_name} completed successfully: {kwargs}"
        )
    except Exception as e:
        tracker.update_status(
            component_id=component_id,
            status="⭕ Error",
            notes=f"Error during {operation_name}: {str(e)}"
        )
        logger.error(f"Operation failed: {operation_name}", exc_info=True)
        raise

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token"""
    user = await user_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user.id

# 📌 API Endpoints
@router.get(
    "/trends",
    response_model=List[MarketTrend],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Market Trends"
)
@cache(expire=300)  # Cache for 5 minutes
async def get_market_trends(
    time_range: TimeRange,
    sector: Optional[str] = None,
    min_confidence: float = Field(0.7, ge=0, le=1),
    user_id: str = Depends(get_current_user_id)
):
    """Get AI-identified market trends and patterns"""
    async with track_operation("market-trends/trends", "Get Market Trends", sector=sector):
        try:
            return await market_trends_service.analyze_trends(
                user_id=user_id,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                granularity=time_range.granularity,
                sector=sector,
                min_confidence=min_confidence
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to analyze trends: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze market trends"
            )

@router.get(
    "/forecasts",
    response_model=List[Forecast],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Market Forecasts"
)
@cache(expire=600)  # Cache for 10 minutes
async def get_forecasts(
    time_range: TimeRange,
    metrics: List[str] = Query(..., min_items=1, max_items=10),
    sector: Optional[str] = None,
    min_probability: float = Field(0.7, ge=0, le=1),
    user_id: str = Depends(get_current_user_id)
):
    """Get AI-generated forecasts for specified metrics"""
    async with track_operation("market-trends/forecasts", "Get Forecasts", metrics=metrics):
        try:
            return await market_trends_service.generate_forecasts(
                user_id=user_id,
                metrics=metrics,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                sector=sector,
                min_probability=min_probability
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to generate forecasts: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate market forecasts"
            )

@router.get(
    "/opportunities",
    response_model=List[Opportunity],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Market Opportunities"
)
@cache(expire=1800)  # Cache for 30 minutes
async def get_opportunities(
    time_range: TimeRange,
    min_value: Optional[float] = None,
    min_probability: float = Field(0.6, ge=0, le=1),
    sector: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get AI-identified market opportunities"""
    async with track_operation("market-trends/opportunities", "Get Opportunities", sector=sector):
        try:
            return await market_trends_service.identify_opportunities(
                user_id=user_id,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                min_value=min_value,
                min_probability=min_probability,
                sector=sector
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to identify opportunities: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to identify market opportunities"
            )

@router.get(
    "/alerts",
    response_model=List[MarketAlert],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Market Alerts"
)
@cache(expire=300)  # Cache for 5 minutes
async def get_market_alerts(
    time_range: TimeRange,
    alert_types: Optional[List[str]] = Query(None, max_items=10),
    min_severity: AlertSeverity = AlertSeverity.MEDIUM,
    sector: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get AI-generated market alerts and warnings"""
    async with track_operation("market-trends/alerts", "Get Market Alerts"):
        try:
            return await market_trends_service.generate_alerts(
                user_id=user_id,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                alert_types=alert_types,
                min_severity=min_severity,
                sector=sector
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to generate alerts: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate market alerts"
            )

@router.post(
    "/subscribe",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))],
    summary="Subscribe to Market Alerts"
)
async def subscribe_to_alerts(
    alert_types: List[str] = Query(..., min_items=1, max_items=10),
    frequency: str = Query("daily", regex="^(hourly|daily|weekly)$"),
    min_severity: AlertSeverity = AlertSeverity.MEDIUM,
    user_id: str = Depends(get_current_user_id)
):
    """Subscribe to AI-generated market alerts"""
    async with track_operation("market-trends/subscribe", "Subscribe to Alerts"):
        try:
            subscription = await market_trends_service.create_alert_subscription(
                user_id=user_id,
                alert_types=alert_types,
                frequency=frequency,
                min_severity=min_severity
            )
            return {
                "status": "success",
                "subscription_id": subscription.id,
                "message": "Successfully subscribed to market alerts"
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create alert subscription"
            )

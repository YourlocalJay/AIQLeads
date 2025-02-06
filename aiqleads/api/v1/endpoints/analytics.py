from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.analytics_service import AnalyticsService
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Initialize services
analytics_service = AnalyticsService()
user_service = UserService()
tracker = ProjectTracker()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 📌 Base Models
class TimeRange(BaseModel):
    start_date: datetime
    end_date: datetime = Field(default_factory=datetime.utcnow)
    granularity: str = Field("day", regex="^(hour|day|week|month)$")

    @validator("end_date")
    def end_date_not_in_future(cls, v):
        if v > datetime.utcnow():
            raise ValueError("end_date cannot be in the future")
        return v

    @validator("start_date")
    def start_date_not_after_end_date(cls, v, values):
        if "end_date" in values and v > values["end_date"]:
            raise ValueError("start_date must be before end_date")
        return v

class MetricValue(BaseModel):
    value: float
    change: float
    trend: str = Field(..., regex="^(up|down|stable)$")
    confidence: float = Field(..., ge=0, le=1)

class PerformanceMetrics(BaseModel):
    conversion_rate: MetricValue
    response_time: MetricValue
    lead_quality: MetricValue
    engagement_rate: MetricValue
    roi: MetricValue
    period: str
    last_updated: datetime

class LeadMetrics(BaseModel):
    total_leads: int = Field(..., ge=0)
    qualified_leads: int = Field(..., ge=0)
    conversion_rate: float = Field(..., ge=0, le=1)
    average_deal_size: float = Field(..., ge=0)
    top_sources: List[Dict[str, Any]]
    period: str
    last_updated: datetime

class CustomMetric(BaseModel):
    name: str
    value: float
    metadata: Dict[str, Any] = {}

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

@router.get(
    "/performance",
    response_model=PerformanceMetrics,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))]
)
@cache(expire=300)  # Cache for 5 minutes
async def get_performance_metrics(
    time_range: TimeRange,
    segment: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get key performance metrics for specified time range"""
    async with track_operation("analytics/performance", "Get Performance Metrics", segment=segment):
        try:
            return await analytics_service.get_performance_metrics(
                user_id=user_id,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                granularity=time_range.granularity,
                segment=segment
            )
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve performance metrics"
            )

@router.get(
    "/leads",
    response_model=LeadMetrics,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))]
)
@cache(expire=300)
async def get_lead_metrics(
    time_range: TimeRange,
    source: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get lead-related metrics and analytics"""
    async with track_operation("analytics/leads", "Get Lead Metrics"):
        try:
            return await analytics_service.get_lead_metrics(
                user_id=user_id,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                granularity=time_range.granularity,
                source=source,
                status=status
            )
        except Exception as e:
            logger.error(f"Failed to get lead metrics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve lead metrics"
            )

@router.post(
    "/custom",
    response_model=List[CustomMetric],
    dependencies=[Depends(RateLimiter(requests_per_minute=20))]
)
async def get_custom_metrics(
    time_range: TimeRange,
    metrics: List[str] = Query(..., min_items=1, max_items=10),
    filters: Dict[str, Any] = {},
    user_id: str = Depends(get_current_user_id)
):
    """Get custom metrics based on specified parameters"""
    async with track_operation("analytics/custom", "Get Custom Metrics", metrics=metrics):
        try:
            return await analytics_service.get_custom_metrics(
                user_id=user_id,
                metrics=metrics,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                granularity=time_range.granularity,
                filters=filters
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to get custom metrics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve custom metrics"
            )

@router.get(
    "/export",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))]
)
async def export_analytics(
    time_range: TimeRange,
    metrics: List[str] = Query(..., min_items=1, max_items=20),
    format: str = Query("csv", regex="^(csv|xlsx|json)$"),
    user_id: str = Depends(get_current_user_id)
):
    """Export analytics data in specified format"""
    async with track_operation("analytics/export", "Export Analytics", format=format):
        try:
            return await analytics_service.export_analytics(
                user_id=user_id,
                metrics=metrics,
                start_date=time_range.start_date,
                end_date=time_range.end_date,
                format=format
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to export analytics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export analytics data"
            )

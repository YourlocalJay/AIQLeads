from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
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

# Context Manager for Operation Tracking
@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Tracks operation status in `ProjectTracker`."""
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
        logger.error(f"Operation failed: {operation_name} | Error: {e}")
        raise

# 📌 TimeRange Model
class TimeRange(BaseModel):
    start_date: datetime
    end_date: datetime = Field(default_factory=datetime.utcnow)
    granularity: str = Field("day", regex="^(hour|day|week|month)$")

# 📌 PerformanceMetrics Model
class PerformanceMetrics(BaseModel):
    conversion_rate: float = Field(..., ge=0, le=1)
    average_response_time: float = Field(..., ge=0)
    lead_quality_score: float = Field(..., ge=0, le=100)
    engagement_rate: float = Field(..., ge=0, le=1)
    roi: float

# 📌 Lead Insights Model
class LeadInsights(BaseModel):
    total_leads: int = Field(..., ge=0)
    qualified_leads: int = Field(..., ge=0)
    conversion_rate: float = Field(..., ge=0, le=1)
    average_deal_size: float = Field(..., ge=0)
    top_sources: List[Dict[str, Any]]
    growth_rate: float

# 📌 Predictive Analytics Model
class PredictiveAnalytics(BaseModel):
    lead_scoring_accuracy: float = Field(..., ge=0, le=1)
    churn_risk_factors: List[Dict[str, float]]
    growth_opportunities: List[Dict[str, Any]]
    market_trends: List[Dict[str, Any]]
    recommendations: List[str]

# 📌 Market Segment Model
class MarketSegment(BaseModel):
    segment_name: str
    size: int = Field(..., ge=0)
    average_budget: float = Field(..., ge=0)
    conversion_rate: float = Field(..., ge=0, le=1)
    lifetime_value: float = Field(..., ge=0)
    growth_potential: float = Field(..., ge=0, le=1)

# 📌 Get Performance Metrics
@router.get(
    "/performance",
    response_model=PerformanceMetrics,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Performance Metrics"
)
@cache(expire=300)  # Cache for 5 minutes
async def get_performance_metrics(time_range: TimeRange, token: str = Depends(oauth2_scheme)):
    """Fetch performance metrics including conversion rates, response times, and ROI."""
    async with track_operation("api/v1/analytics/performance", "Get Performance Metrics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")
        
        return await analytics_service.calculate_performance_metrics(
            user_id=user.id, start_date=time_range.start_date, end_date=time_range.end_date, granularity=time_range.granularity
        )

# 📌 Get Lead Insights
@router.get(
    "/leads",
    response_model=LeadInsights,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Lead Insights"
)
@cache(expire=300)
async def get_lead_insights(time_range: TimeRange, token: str = Depends(oauth2_scheme)):
    """Fetch insights including total leads, conversion rates, and growth trends."""
    async with track_operation("api/v1/analytics/leads", "Get Lead Insights"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        return await analytics_service.analyze_leads(user.id, time_range.start_date, time_range.end_date)

# 📌 Get Predictive Analytics
@router.get(
    "/predictive",
    response_model=PredictiveAnalytics,
    dependencies=[Depends(RateLimiter(requests_per_minute=20))],
    summary="Get Predictive Analytics"
)
@cache(expire=1800)  # Cache for 30 minutes
async def get_predictive_analytics(time_range: TimeRange, token: str = Depends(oauth2_scheme)):
    """Generate AI-powered insights including churn risks, growth factors, and recommendations."""
    async with track_operation("api/v1/analytics/predictive", "Get Predictive Analytics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        return await analytics_service.generate_predictions(user.id, time_range.start_date, time_range.end_date)

# 📌 Get Market Segments
@router.get(
    "/market-segments",
    response_model=List[MarketSegment],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Analyze Market Segments"
)
@cache(expire=600)
async def get_market_segments(time_range: TimeRange, token: str = Depends(oauth2_scheme)):
    """Fetch performance metrics for market segments based on size, conversion rates, and budget."""
    async with track_operation("api/v1/analytics/market-segments", "Get Market Segments"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        return await analytics_service.analyze_market_segments(user.id, time_range.start_date, time_range.end_date)

# 📌 Export Analytics
@router.get(
    "/export",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))],
    summary="Export Analytics Data"
)
async def export_analytics(time_range: TimeRange, format: str = Query("csv", regex="^(csv|xlsx|json)$"), token: str = Depends(oauth2_scheme)):
    """Export analytics data in CSV, XLSX, or JSON format."""
    async with track_operation("api/v1/analytics/export", "Export Analytics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        return await analytics_service.export_analytics(user.id, time_range.start_date, time_range.end_date, format)

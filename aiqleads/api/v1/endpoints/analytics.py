from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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

class TimeRange(BaseModel):
    start_date: datetime
    end_date: datetime = Field(default_factory=lambda: datetime.utcnow())
    granularity: str = Field("day", regex="^(hour|day|week|month)$")

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-02-01T00:00:00Z",
                "granularity": "day"
            }
        }

class PerformanceMetrics(BaseModel):
    conversion_rate: float = Field(..., ge=0, le=1)
    average_response_time: float = Field(..., ge=0)
    lead_quality_score: float = Field(..., ge=0, le=100)
    engagement_rate: float = Field(..., ge=0, le=1)
    roi: float

    class Config:
        schema_extra = {
            "example": {
                "conversion_rate": 0.35,
                "average_response_time": 2.5,
                "lead_quality_score": 85.5,
                "engagement_rate": 0.75,
                "roi": 3.2
            }
        }

class LeadInsights(BaseModel):
    total_leads: int = Field(..., ge=0)
    qualified_leads: int = Field(..., ge=0)
    conversion_rate: float = Field(..., ge=0, le=1)
    average_deal_size: float = Field(..., ge=0)
    top_sources: List[Dict[str, Any]]
    growth_rate: float

    class Config:
        schema_extra = {
            "example": {
                "total_leads": 1250,
                "qualified_leads": 450,
                "conversion_rate": 0.36,
                "average_deal_size": 25000.0,
                "top_sources": [
                    {"source": "website", "count": 500, "conversion_rate": 0.4},
                    {"source": "referral", "count": 300, "conversion_rate": 0.35}
                ],
                "growth_rate": 0.15
            }
        }

class MarketSegment(BaseModel):
    segment_name: str
    size: int = Field(..., ge=0)
    average_budget: float = Field(..., ge=0)
    conversion_rate: float = Field(..., ge=0, le=1)
    lifetime_value: float = Field(..., ge=0)
    growth_potential: float = Field(..., ge=0, le=1)

class PredictiveAnalytics(BaseModel):
    lead_scoring_accuracy: float = Field(..., ge=0, le=1)
    churn_risk_factors: List[Dict[str, float]]
    growth_opportunities: List[Dict[str, Any]]
    market_trends: List[Dict[str, Any]]
    recommendations: List[str]

    class Config:
        schema_extra = {
            "example": {
                "lead_scoring_accuracy": 0.92,
                "churn_risk_factors": [
                    {"factor": "response_time", "impact": 0.8},
                    {"factor": "engagement", "impact": 0.6}
                ],
                "growth_opportunities": [
                    {
                        "segment": "enterprise",
                        "potential": 0.85,
                        "estimated_value": 500000
                    }
                ],
                "market_trends": [
                    {
                        "trend": "increased_digital_adoption",
                        "impact": "positive",
                        "probability": 0.9
                    }
                ],
                "recommendations": [
                    "Focus on enterprise segment expansion",
                    "Improve response time automation"
                ]
            }
        }

@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Context manager for tracking operations and logging"""
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

@router.get("/performance", 
    response_model=PerformanceMetrics,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)  # Cache for 5 minutes
async def get_performance_metrics(
    time_range: TimeRange,
    token: str = Depends(oauth2_scheme)
):
    """
    Get key performance metrics for the specified time range.
    """
    async with track_operation("api/v1/analytics/performance", "Get Performance Metrics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        metrics = await analytics_service.calculate_performance_metrics(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            granularity=time_range.granularity
        )
        return metrics

@router.get("/leads", 
    response_model=LeadInsights,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)
async def get_lead_insights(
    time_range: TimeRange,
    segment: Optional[str] = None,
    source: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Get detailed insights about lead performance and trends.
    """
    async with track_operation("api/v1/analytics/leads", "Get Lead Insights"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        insights = await analytics_service.analyze_leads(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            segment=segment,
            source=source
        )
        return insights

@router.get("/market-segments",
    response_model=List[MarketSegment],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=600)  # Cache for 10 minutes
async def get_market_segments(
    time_range: TimeRange,
    min_size: Optional[int] = None,
    min_value: Optional[float] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Analyze market segments and their performance metrics.
    """
    async with track_operation("api/v1/analytics/market-segments", "Get Market Segments"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        segments = await analytics_service.analyze_market_segments(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            min_size=min_size,
            min_value=min_value
        )
        return segments

@router.get("/predictive",
    response_model=PredictiveAnalytics,
    dependencies=[Depends(RateLimiter(requests_per_minute=20))])
@cache(expire=1800)  # Cache for 30 minutes
async def get_predictive_analytics(
    time_range: TimeRange,
    confidence_threshold: float = Field(0.8, ge=0, le=1),
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-powered predictive analytics and recommendations.
    """
    async with track_operation("api/v1/analytics/predictive", "Get Predictive Analytics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        predictions = await analytics_service.generate_predictions(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            confidence_threshold=confidence_threshold
        )
        return predictions

@router.get("/custom",
    dependencies=[Depends(RateLimiter(requests_per_minute=20))])
async def get_custom_analytics(
    metrics: List[str],
    time_range: TimeRange,
    filters: Optional[Dict[str, Any]] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Generate custom analytics based on specified metrics and filters.
    """
    async with track_operation("api/v1/analytics/custom", "Get Custom Analytics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        results = await analytics_service.generate_custom_analytics(
            user_id=user.id,
            metrics=metrics,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            filters=filters or {}
        )
        return results

@router.get("/export",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def export_analytics(
    time_range: TimeRange,
    metrics: List[str],
    format: str = Field("csv", regex="^(csv|xlsx|json)$"),
    token: str = Depends(oauth2_scheme)
):
    """
    Export analytics data in specified format.
    """
    async with track_operation("api/v1/analytics/export", "Export Analytics"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        export_data = await analytics_service.export_analytics(
            user_id=user.id,
            metrics=metrics,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            format=format
        )
        return export_data

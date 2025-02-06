from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.market_trends_service import MarketTrendsService
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api/v1/market-trends", tags=["market-trends"])

# Initialize services
market_trends_service = MarketTrendsService()
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

class MarketTrend(BaseModel):
    trend_id: str
    name: str
    description: str
    confidence: float = Field(..., ge=0, le=1)
    impact: str = Field(..., regex="^(positive|negative|neutral)$")
    affected_segments: List[str]
    predicted_duration: Optional[int] = None
    data_points: List[Dict[str, Any]]
    recommendations: List[str]

    class Config:
        schema_extra = {
            "example": {
                "trend_id": "trend_123",
                "name": "Rising Digital Marketing ROI",
                "description": "Increasing effectiveness of digital marketing...",
                "confidence": 0.85,
                "impact": "positive",
                "affected_segments": ["SMB", "Enterprise"],
                "predicted_duration": 90,
                "data_points": [
                    {"date": "2025-01-01", "value": 1.2},
                    {"date": "2025-01-02", "value": 1.3}
                ],
                "recommendations": [
                    "Increase digital marketing budget",
                    "Focus on content marketing"
                ]
            }
        }

class Forecast(BaseModel):
    forecast_id: str
    metric: str
    current_value: float
    predicted_value: float
    confidence_interval: List[float]
    factors: List[Dict[str, Any]]
    timeline: str
    probability: float = Field(..., ge=0, le=1)

    class Config:
        schema_extra = {
            "example": {
                "forecast_id": "forecast_123",
                "metric": "lead_conversion_rate",
                "current_value": 0.25,
                "predicted_value": 0.35,
                "confidence_interval": [0.30, 0.40],
                "factors": [
                    {"name": "market_growth", "impact": 0.6},
                    {"name": "competition", "impact": -0.2}
                ],
                "timeline": "3_months",
                "probability": 0.85
            }
        }

class Opportunity(BaseModel):
    opportunity_id: str
    title: str
    description: str
    potential_value: float
    success_probability: float = Field(..., ge=0, le=1)
    market_size: float
    competition_level: str = Field(..., regex="^(low|medium|high)$")
    required_resources: List[str]
    timeline: str
    risk_factors: List[Dict[str, Any]]

    class Config:
        schema_extra = {
            "example": {
                "opportunity_id": "opp_123",
                "title": "Expand into Healthcare Sector",
                "description": "Growing demand for AI solutions...",
                "potential_value": 1000000.0,
                "success_probability": 0.75,
                "market_size": 5000000.0,
                "competition_level": "medium",
                "required_resources": ["domain_expertise", "sales_team"],
                "timeline": "6_months",
                "risk_factors": [
                    {"factor": "regulation", "impact": "high"},
                    {"factor": "adoption_rate", "impact": "medium"}
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

@router.get("/trends",
    response_model=List[MarketTrend],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)  # Cache for 5 minutes
async def get_market_trends(
    time_range: TimeRange,
    segment: Optional[str] = None,
    min_confidence: float = Field(0.7, ge=0, le=1),
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-identified market trends and patterns.
    """
    async with track_operation("api/v1/market-trends/trends", "Get Market Trends"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        trends = await market_trends_service.analyze_trends(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            segment=segment,
            min_confidence=min_confidence
        )
        return trends

@router.get("/forecasts",
    response_model=List[Forecast],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=600)  # Cache for 10 minutes
async def get_forecasts(
    time_range: TimeRange,
    metrics: List[str],
    segment: Optional[str] = None,
    min_probability: float = Field(0.7, ge=0, le=1),
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-generated forecasts for specified metrics.
    """
    async with track_operation("api/v1/market-trends/forecasts", "Get Forecasts"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        forecasts = await market_trends_service.generate_forecasts(
            user_id=user.id,
            metrics=metrics,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            segment=segment,
            min_probability=min_probability
        )
        return forecasts

@router.get("/opportunities",
    response_model=List[Opportunity],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=1800)  # Cache for 30 minutes
async def get_opportunities(
    time_range: TimeRange,
    min_value: Optional[float] = None,
    min_probability: float = Field(0.6, ge=0, le=1),
    sector: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-identified market opportunities.
    """
    async with track_operation("api/v1/market-trends/opportunities", "Get Opportunities"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        opportunities = await market_trends_service.identify_opportunities(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            min_value=min_value,
            min_probability=min_probability,
            sector=sector
        )
        return opportunities

@router.get("/competitive-analysis",
    dependencies=[Depends(RateLimiter(requests_per_minute=20))])
@cache(expire=3600)  # Cache for 1 hour
async def get_competitive_analysis(
    time_range: TimeRange,
    sector: Optional[str] = None,
    competitors: Optional[List[str]] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-powered competitive market analysis.
    """
    async with track_operation("api/v1/market-trends/competitive", "Get Competitive Analysis"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        analysis = await market_trends_service.analyze_competition(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            sector=sector,
            competitors=competitors
        )
        return analysis

@router.get("/sentiment-analysis",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=1800)  # Cache for 30 minutes
async def get_market_sentiment(
    time_range: TimeRange,
    sector: Optional[str] = None,
    sources: Optional[List[str]] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-analyzed market sentiment from various sources.
    """
    async with track_operation("api/v1/market-trends/sentiment", "Get Market Sentiment"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        sentiment = await market_trends_service.analyze_sentiment(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            sector=sector,
            sources=sources
        )
        return sentiment

@router.get("/alerts",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def get_market_alerts(
    time_range: TimeRange,
    alert_types: Optional[List[str]] = None,
    min_severity: str = Field("medium", regex="^(low|medium|high)$"),
    token: str = Depends(oauth2_scheme)
):
    """
    Get AI-generated market alerts and warnings.
    """
    async with track_operation("api/v1/market-trends/alerts", "Get Market Alerts"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        alerts = await market_trends_service.generate_alerts(
            user_id=user.id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            alert_types=alert_types,
            min_severity=min_severity
        )
        return alerts

@router.post("/subscribe",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def subscribe_to_alerts(
    alert_types: List[str],
    frequency: str = Field("daily", regex="^(hourly|daily|weekly)$"),
    token: str = Depends(oauth2_scheme)
):
    """
    Subscribe to AI-generated market alerts.
    """
    async with track_operation("api/v1/market-trends/subscribe", "Subscribe to Alerts"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        subscription = await market_trends_service.create_alert_subscription(
            user_id=user.id,
            alert_types=alert_types,
            frequency=frequency
        )
        return subscription

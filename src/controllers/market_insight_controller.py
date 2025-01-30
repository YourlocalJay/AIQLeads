from fastapi import APIRouter, HTTPException, Query, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from datetime import datetime, timedelta
import asyncio
import json
import io
import csv

from src.database.postgres_manager import get_async_session
from src.models.market_insight_model import MarketInsight
from src.schemas.market_insight_schema import (
    MarketInsightResponse,
    MarketInsightList,
    MarketForecast,
    CompetitorAnalysis,
    MarketTrend
)
from src.services.cache import redis_client
from src.monitoring.metrics import api_metrics
from src.auth.dependencies import validate_api_key
from src.ai.market_forecaster import predict_market_growth
from src.ai.competitor_analyzer import analyze_competitors
from src.websocket.market_updates import broadcast_market_updates
from src.utils.exporters import generate_csv, generate_json

router = APIRouter(
    prefix="/market-insights",
    tags=["Market Insights"],
    dependencies=[Depends(validate_api_key)]
)

CACHE_TTL = 3600  # 1 hour cache

@router.get(
    "/{region_name}/forecast",
    response_model=MarketForecast,
    summary="Get AI-powered market growth forecast"
)
@api_metrics.track("forecast_market")
async def get_market_forecast(
    region_name: str,
    forecast_days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session)
):
    """Predict future market penetration trends using AI models."""
    cache_key = f"forecast:{region_name}:{forecast_days}"
    
    try:
        # Check cache
        if cached := await redis_client.get(cache_key):
            return MarketForecast.parse_raw(cached)

        result = await session.execute(
            sa.select(MarketInsight)
            .where(MarketInsight.region_name == region_name)
            .order_by(MarketInsight.date.desc())
            .limit(365)  # Get last year's data
        )
        historical_data = result.scalars().all()

        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No historical data found for region"
            )

        # Generate AI forecast
        forecast = await predict_market_growth(
            historical_data=historical_data,
            forecast_days=forecast_days
        )

        # Cache results
        await redis_client.set(
            cache_key,
            forecast.json(),
            ex=CACHE_TTL
        )

        return forecast

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating forecast: {str(e)}"
        )

@router.get(
    "/compare",
    response_model=Dict[str, MarketTrend],
    summary="Compare multiple regions"
)
@api_metrics.track("compare_regions")
async def compare_regions(
    regions: List[str] = Query(..., min_items=2, max_items=5),
    timeframe: str = Query("month", regex="^(week|month|quarter|year)$"),
    session: AsyncSession = Depends(get_async_session)
):
    """Compare market insights across multiple regions with benchmarking."""
    cache_key = f"compare:{'-'.join(sorted(regions))}:{timeframe}"
    
    try:
        # Check cache
        if cached := await redis_client.get(cache_key):
            return json.loads(cached)

        # Get data for all regions
        query = (
            sa.select(MarketInsight)
            .where(MarketInsight.region_name.in_(regions))
            .order_by(MarketInsight.date.desc())
        )

        if timeframe == "week":
            query = query.limit(7)
        elif timeframe == "month":
            query = query.limit(30)
        elif timeframe == "quarter":
            query = query.limit(90)
        else:  # year
            query = query.limit(365)

        result = await session.execute(query)
        insights = result.scalars().all()

        # Group by region
        region_data = {}
        for insight in insights:
            if insight.region_name not in region_data:
                region_data[insight.region_name] = []
            region_data[insight.region_name].append(insight)

        # Analyze each region
        comparison = {}
        for region, data in region_data.items():
            comparison[region] = MarketTrend(
                current_penetration=data[0].penetration_rate,
                growth_rate=calculate_growth_rate(data),
                competitor_activity=analyze_competitors(data),
                historical_trend=extract_trend(data),
                benchmark_metrics=calculate_benchmarks(data)
            )

        # Cache results
        await redis_client.set(
            cache_key,
            json.dumps(comparison),
            ex=CACHE_TTL
        )

        return comparison

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing regions: {str(e)}"
        )

@router.get(
    "/{region_name}/export",
    summary="Export market insights"
)
@api_metrics.track("export_insights")
async def export_insights(
    region_name: str,
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Export market insights in JSON or CSV format."""
    try:
        query = (
            sa.select(MarketInsight)
            .where(MarketInsight.region_name == region_name)
            .order_by(MarketInsight.date.desc())
        )

        if start_date:
            query = query.where(MarketInsight.date >= start_date)
        if end_date:
            query = query.where(MarketInsight.date <= end_date)

        result = await session.execute(query)
        insights = result.scalars().all()

        if format == "json":
            content = generate_json(insights)
            media_type = "application/json"
            filename = f"{region_name}_insights.json"
        else:  # csv
            content = generate_csv(insights)
            media_type = "text/csv"
            filename = f"{region_name}_insights.csv"

        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting insights: {str(e)}"
        )

# Helper functions
def calculate_growth_rate(data: List[MarketInsight]) -> float:
    """Calculate growth rate from historical data."""
    if len(data) < 2:
        return 0.0
    return (data[0].penetration_rate - data[-1].penetration_rate) / data[-1].penetration_rate

def extract_trend(data: List[MarketInsight]) -> List[float]:
    """Extract trend values from historical data."""
    return [d.penetration_rate for d in reversed(data)]

def calculate_benchmarks(data: List[MarketInsight]) -> Dict[str, float]:
    """Calculate benchmark metrics from historical data."""
    return {
        "avg_penetration": sum(d.penetration_rate for d in data) / len(data),
        "max_penetration": max(d.penetration_rate for d in data),
        "min_penetration": min(d.penetration_rate for d in data),
        "volatility": calculate_volatility(data)
    }

def calculate_volatility(data: List[MarketInsight]) -> float:
    """Calculate market volatility from historical data."""
    if len(data) < 2:
        return 0.0
    changes = [abs(data[i].penetration_rate - data[i-1].penetration_rate) 
               for i in range(1, len(data))]
    return sum(changes) / len(changes)
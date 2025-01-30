from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from datetime import datetime

from src.database.postgres_manager import get_async_session
from src.models.market_insight_model import MarketInsight
from src.schemas.market_insight_schema import MarketInsightResponse, MarketInsightList
from src.services.cache import redis_client
from src.monitoring.metrics import api_metrics
from src.auth.dependencies import validate_api_key
from fastapi_limiter.depends import RateLimiter
from src.ai.forecaster import predict_market_growth  # AI forecasting module
from src.websocket.market_updates import broadcast_market_updates  # WebSocket for real-time updates

router = APIRouter(
    prefix="/market-insights",
    tags=["Market Insights"],
    dependencies=[Depends(validate_api_key)]
)

CACHE_TTL = 3600  # 1 hour cache
logger = logging.getLogger("market_insights")

class MarketInsightFilters(BaseModel):
    min_update_date: Optional[datetime] = Field(None, description="Filter insights updated after this date")
    max_risk_score: Optional[float] = Field(None, ge=0, le=1.0, description="Filter insights with risk score below this value")

@router.get(
    "/{region_name}",
    response_model=MarketInsightResponse,
    summary="Get market insights by region",
    dependencies=[Depends(RateLimiter(times=100, hours=1))],
)
@api_metrics.track("get_market_insights")
async def get_market_insights(
    region_name: str = Query(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9\-_ ]+$"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get comprehensive market insights for a specific region with caching and fraud detection metrics.
    """
    cache_key = f"market_insights:{region_name.lower()}"
    
    try:
        # Check Redis cache
        if cached_data := await redis_client.get(cache_key):
            logger.info(f"Cache hit for region: {region_name}")
            return MarketInsightResponse.parse_raw(cached_data)

        # Query database
        result = await session.execute(
            sa.select(MarketInsight)
            .where(sa.func.lower(MarketInsight.region_name) == region_name.lower())
            .limit(1)
        )
        insight = result.scalars().first()

        if not insight:
            logger.warning(f"Region not found: {region_name}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")

        # Cache response
        await redis_client.set(cache_key, MarketInsightResponse.from_orm(insight).json(), ex=CACHE_TTL)

        return MarketInsightResponse.from_orm(insight)

    except Exception as e:
        logger.error(f"Error fetching insights for {region_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving market insights")

@router.get(
    "",
    response_model=MarketInsightList,
    summary="List market insights with advanced filtering",
    dependencies=[Depends(RateLimiter(times=50, minutes=1))]
)
@api_metrics.track("list_market_insights")
async def list_market_insights(
    filters: MarketInsightFilters = Depends(),
    sort_by: str = Query("updated_at", enum=["region_name", "updated_at", "risk_score"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Paginated list of market insights with advanced filtering and sorting capabilities.
    """
    try:
        query = sa.select(MarketInsight)
        
        # Apply filters
        if filters.min_update_date:
            query = query.where(MarketInsight.updated_at >= filters.min_update_date)
        if filters.max_risk_score is not None:
            query = query.where(MarketInsight.risk_score <= filters.max_risk_score)
            
        # Sorting
        order_field = getattr(MarketInsight, sort_by, MarketInsight.updated_at)
        query = query.order_by(order_field.desc() if sort_order == "desc" else order_field.asc())

        # Pagination
        result = await session.execute(query.offset((page - 1) * size).limit(size))
        insights = result.scalars().all()
        
        total = await session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))

        return MarketInsightList(
            items=[MarketInsightResponse.from_orm(insight) for insight in insights],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
            sort_by=sort_by,
            sort_order=sort_order
        )

    except Exception as e:
        logger.error(f"Error listing insights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving market insights list")

@router.get("/{region_name}/forecast", summary="Get market growth forecast for a region")
async def get_market_forecast(region_name: str):
    """
    Predict future market penetration trends for a specific region.
    """
    try:
        forecast = predict_market_growth(region_name)
        return {"region": region_name, "forecast": forecast}
    except Exception as e:
        logger.error(f"Error generating forecast for {region_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error generating market forecast")

@router.get("/compare", summary="Compare multiple regions side by side")
async def compare_market_insights(region_names: List[str] = Query(..., description="List of regions to compare")):
    """
    Compare market insights across multiple regions.
    """
    try:
        with postgres_manager.get_session() as session:
            insights = session.query(MarketInsight).filter(MarketInsight.region_name.in_(region_names)).all()
            if not insights:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No market insights found for the given regions")
            return {"regions": region_names, "data": [MarketInsightResponse.from_orm(i) for i in insights]}
    except Exception as e:
        logger.error(f"Error comparing market insights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error comparing market insights")

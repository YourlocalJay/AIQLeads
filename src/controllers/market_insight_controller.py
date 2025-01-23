from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.postgres_manager import postgres_manager
from src.models.market_insight_model import MarketInsight
from src.schemas.market_insight_schema import MarketInsightResponse, MarketInsightList

router = APIRouter()

@router.get("/market-insights/{region_name}", response_model=MarketInsightResponse, summary="Get market insights by region")
async def get_market_insights(region_name: str):
    """
    Fetch market insights for a specific region.
    Args:
        region_name (str): The name of the region.
    Returns:
        MarketInsightResponse: Market insights data.
    """
    try:
        with postgres_manager.get_session() as session:
            insight = session.query(MarketInsight).filter(MarketInsight.region_name == region_name).first()
            if not insight:
                raise HTTPException(status_code=404, detail="Market insights not found for the region")
            return MarketInsightResponse.from_orm(insight)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market insights: {str(e)}")

@router.get("/market-insights", response_model=MarketInsightList, summary="List all market insights")
async def list_market_insights(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    List all market insights with pagination.
    Args:
        page (int): Page number.
        size (int): Number of items per page.
    Returns:
        MarketInsightList: Paginated list of market insights.
    """
    try:
        with postgres_manager.get_session() as session:
            query = session.query(MarketInsight)
            total = query.count()
            insights = query.offset((page - 1) * size).limit(size).all()
            return MarketInsightList(
                items=[MarketInsightResponse.from_orm(insight) for insight in insights],
                total=total,
                page=page,
                size=size,
                pages=(total // size) + (1 if total % size > 0 else 0)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing market insights: {str(e)}")

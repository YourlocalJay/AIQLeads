from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from datetime import datetime

from src.database.postgres_manager import get_async_session
from src.models.lead_model import Lead
from src.schemas.lead_schema import LeadCreate, LeadUpdate, LeadResponse, LeadList
from src.services.cache import redis_client
from src.monitoring.metrics import api_metrics
from src.auth.dependencies import validate_api_key
from fastapi_limiter.depends import RateLimiter
from src.ai.lead_scoring import score_lead  # AI module for lead prioritization
from src.websocket.lead_updates import broadcast_lead_updates  # WebSocket for real-time updates

router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
    dependencies=[Depends(validate_api_key)]
)

CACHE_TTL = 3600  # 1 hour cache

@router.post("/", response_model=LeadResponse, summary="Create a new lead")
@api_metrics.track("create_lead")
async def create_lead(
    lead_data: LeadCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new lead entry with AI-based scoring.
    """
    try:
        # Prevent duplicate leads based on email or phone
        existing_lead = await session.execute(
            sa.select(Lead).where(Lead.email == lead_data.email)
        )
        if existing_lead.scalars().first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lead already exists")

        # Score the lead using AI
        lead_data.score = score_lead(lead_data)

        # Insert new lead
        new_lead = Lead(**lead_data.dict())
        session.add(new_lead)
        await session.commit()
        await session.refresh(new_lead)

        # Notify clients via WebSocket
        await broadcast_lead_updates(new_lead)

        return LeadResponse.from_orm(new_lead)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating lead: {str(e)}")

@router.get("/{lead_id}", response_model=LeadResponse, summary="Get lead details")
@api_metrics.track("get_lead")
async def get_lead(
    lead_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Fetch details of a specific lead by ID.
    """
    cache_key = f"lead:{lead_id}"
    
    try:
        # Check Redis cache
        if cached_data := await redis_client.get(cache_key):
            return LeadResponse.parse_raw(cached_data)

        # Fetch lead from DB
        result = await session.execute(sa.select(Lead).where(Lead.id == lead_id))
        lead = result.scalars().first()

        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        # Cache result
        await redis_client.set(cache_key, LeadResponse.from_orm(lead).json(), ex=CACHE_TTL)

        return LeadResponse.from_orm(lead)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching lead: {str(e)}")

@router.put("/{lead_id}", response_model=LeadResponse, summary="Update lead details")
@api_metrics.track("update_lead")
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update an existing lead.
    """
    try:
        result = await session.execute(sa.select(Lead).where(Lead.id == lead_id))
        lead = result.scalars().first()

        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        for key, value in lead_data.dict(exclude_unset=True).items():
            setattr(lead, key, value)

        await session.commit()
        await session.refresh(lead)

        return LeadResponse.from_orm(lead)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating lead: {str(e)}")

@router.get("/", response_model=LeadList, summary="List leads with filtering and sorting")
@api_metrics.track("list_leads")
async def list_leads(
    sort_by: str = Query("created_at", enum=["created_at", "score", "lead_source"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """
    List leads with pagination and sorting.
    """
    try:
        query = sa.select(Lead)

        # Sorting
        order_field = getattr(Lead, sort_by, Lead.created_at)
        query = query.order_by(order_field.desc() if sort_order == "desc" else order_field.asc())

        # Pagination
        result = await session.execute(query.offset((page - 1) * size).limit(size))
        leads = result.scalars().all()
        
        total = await session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))

        return LeadList(
            items=[LeadResponse.from_orm(lead) for lead in leads],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
            sort_by=sort_by,
            sort_order=sort_order
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving leads list")

@router.delete("/{lead_id}", summary="Delete a lead")
@api_metrics.track("delete_lead")
async def delete_lead(
    lead_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a lead by ID.
    """
    try:
        result = await session.execute(sa.select(Lead).where(Lead.id == lead_id))
        lead = result.scalars().first()

        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        await session.delete(lead)
        await session.commit()
        return {"status": "success", "message": "Lead deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting lead: {str(e)}")

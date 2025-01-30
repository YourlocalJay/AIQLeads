from fastapi import APIRouter, HTTPException, Query, Depends, status, BackgroundTasks
from pydantic import BaseModel, EmailStr, constr
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from datetime import datetime
import asyncio
from collections import defaultdict

from src.database.postgres_manager import get_async_session
from src.models.lead_model import Lead
from src.schemas.lead_schema import LeadCreate, LeadUpdate, LeadResponse, LeadList, LeadBatch
from src.services.cache import redis_client
from src.monitoring.metrics import api_metrics, track_lead_source_performance
from src.auth.dependencies import validate_api_key
from fastapi_limiter.depends import RateLimiter
from src.ai.lead_scoring import score_lead, predict_conversion_probability
from src.ai.fraud_detection import detect_fraud_signals
from src.websocket.lead_updates import broadcast_lead_updates
from src.utils.rate_limiter import create_rate_limiter
from src.services.engagement_tracker import track_engagement

router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
    dependencies=[Depends(validate_api_key)]
)

CACHE_TTL = 3600  # 1 hour cache
BATCH_SIZE = 100  # Size for batch operations

class LeadSourceStats(BaseModel):
    total_leads: int
    conversion_rate: float
    avg_score: float
    engagement_rate: float

class LeadPriority(BaseModel):
    lead_id: int
    priority_score: float
    conversion_probability: float
    engagement_metrics: Dict[str, Any]

@router.post("/batch", response_model=List[LeadResponse], summary="Create multiple leads")
@api_metrics.track("create_leads_batch")
async def create_leads_batch(
    leads: LeadBatch,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create multiple leads with batch processing and fraud detection.
    """
    try:
        # Pre-process leads for duplicates and fraud
        emails = {lead.email for lead in leads.items}
        phones = {lead.phone for lead in leads.items if lead.phone}
        
        # Check for existing leads in batch
        existing = await session.execute(
            sa.select(Lead.email).where(Lead.email.in_(emails))
        )
        existing_emails = {r[0] for r in existing}

        # Process valid leads in batches
        valid_leads = []
        for lead_data in leads.items:
            if lead_data.email not in existing_emails:
                # Score and fraud check each lead
                fraud_score = await detect_fraud_signals(lead_data)
                if fraud_score < 0.7:  # Threshold for fraud detection
                    lead_data.score = await score_lead(lead_data)
                    valid_leads.append(Lead(**lead_data.dict()))

        # Batch insert valid leads
        session.add_all(valid_leads)
        await session.commit()

        # Background tasks for post-processing
        background_tasks.add_task(track_lead_source_performance, [l.lead_source for l in valid_leads])
        background_tasks.add_task(broadcast_lead_updates, valid_leads)

        return [LeadResponse.from_orm(lead) for lead in valid_leads]

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch lead creation: {str(e)}"
        )

@router.get("/priority-queue", response_model=List[LeadPriority])
@api_metrics.track("get_priority_queue")
async def get_priority_queue(
    min_score: float = Query(0.5, ge=0, le=1),
    max_age_hours: int = Query(72, ge=1),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a prioritized queue of leads based on score and engagement.
    """
    try:
        min_date = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Get recent leads above score threshold
        result = await session.execute(
            sa.select(Lead)
            .where(
                sa.and_(
                    Lead.score >= min_score,
                    Lead.created_at >= min_date
                )
            )
            .order_by(Lead.score.desc())
        )
        leads = result.scalars().all()

        # Calculate priority scores
        priority_leads = []
        for lead in leads:
            engagement = await track_engagement(lead.id)
            conversion_prob = await predict_conversion_probability(lead, engagement)
            
            priority_leads.append(LeadPriority(
                lead_id=lead.id,
                priority_score=lead.score * conversion_prob,
                conversion_probability=conversion_prob,
                engagement_metrics=engagement
            ))

        return sorted(priority_leads, key=lambda x: x.priority_score, reverse=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting priority queue: {str(e)}"
        )

@router.get("/source-analytics", response_model=Dict[str, LeadSourceStats])
@api_metrics.track("get_source_analytics")
async def get_source_analytics(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get analytics for different lead sources.
    """
    try:
        query = sa.select(Lead)
        if start_date:
            query = query.where(Lead.created_at >= start_date)
        if end_date:
            query = query.where(Lead.created_at <= end_date)

        result = await session.execute(query)
        leads = result.scalars().all()

        stats = defaultdict(lambda: {"total_leads": 0, "conversions": 0, "total_score": 0, "engagements": 0})
        
        for lead in leads:
            source = lead.lead_source
            stats[source]["total_leads"] += 1
            stats[source]["total_score"] += lead.score
            if lead.converted:
                stats[source]["conversions"] += 1
            
            engagement = await track_engagement(lead.id)
            if engagement["total_interactions"] > 0:
                stats[source]["engagements"] += 1

        return {
            source: LeadSourceStats(
                total_leads=data["total_leads"],
                conversion_rate=data["conversions"] / data["total_leads"],
                avg_score=data["total_score"] / data["total_leads"],
                engagement_rate=data["engagements"] / data["total_leads"]
            )
            for source, data in stats.items()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting source analytics: {str(e)}"
        )

# Keep existing CRUD endpoints but update with new features
# [Previous CRUD endpoints remain with their implementations]
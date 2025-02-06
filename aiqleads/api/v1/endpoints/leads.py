from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi_cache.decorator import cache
import asyncio
from aiqleads.core.ai_lead_scoring import LeadScorer
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.models.lead_model import Lead
from aiqleads.services.lead_service import LeadService
from aiqleads.utils.logging import logger
from aiqleads.middlewares.rate_limiter import RateLimiter
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])

# Singleton instances for shared resources
lead_scorer = LeadScorer()
lead_service = LeadService()
tracker = ProjectTracker()

# 📌 Context Manager for Operation Tracking
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

# 📌 Lead Score Model
class LeadScore(BaseModel):
    lead_id: str
    score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    factors: List[Dict[str, Any]]
    recommendations: List[str]

# 📌 Lead Score Request Model
class LeadScoreRequest(BaseModel):
    lead: Lead
    include_factors: bool = True
    generate_recommendations: bool = True

# 📌 Batch Score Request Model
class BatchScoreRequest(BaseModel):
    leads: List[Lead] = Field(..., max_items=100)
    include_factors: bool = True
    generate_recommendations: bool = True

# 📌 Batch Response Model
class BatchResponse(BaseModel):
    scores: List[LeadScore]
    errors: List[Dict[str, Any]]
    metadata: Dict[str, int] = Field(default_factory=lambda: {"processed": 0, "successful": 0, "failed": 0})

# 📌 Score a Single Lead
@router.post(
    "/score",
    response_model=LeadScore,
    dependencies=[Depends(RateLimiter(requests_per_minute=60))],
    summary="Score a Single Lead"
)
async def score_lead(request: LeadScoreRequest):
    """AI-powered lead scoring with detailed insights & recommendations."""
    if await lead_service.is_duplicate(request.lead):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Duplicate lead detected")

    async with track_operation("api/v1/leads/score", "Lead Scoring", lead_id=request.lead.id):
        try:
            score_result = await lead_scorer.analyze(
                lead_data=request.lead,
                include_factors=request.include_factors,
                generate_recommendations=request.generate_recommendations
            )
        except Exception as e:
            logger.error(f"Lead scoring failed: {e}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to score lead")

        return LeadScore(
            lead_id=request.lead.id,
            score=score_result.score,
            confidence=score_result.confidence,
            factors=score_result.contributing_factors if request.include_factors else [],
            recommendations=score_result.recommendations if request.generate_recommendations else []
        )

# 📌 Retrieve Existing Lead Score
@router.get(
    "/score/{lead_id}",
    response_model=LeadScore,
    dependencies=[Depends(RateLimiter(requests_per_minute=120))],
    summary="Retrieve Existing Lead Score"
)
@cache(expire=300)
async def get_lead_score(lead_id: str, include_factors: bool = True, include_recommendations: bool = True):
    """Fetch the stored score for a lead with optional factors & recommendations."""
    async with track_operation("api/v1/leads/score/{lead_id}", "Retrieve Lead Score", lead_id=lead_id):
        score = await lead_service.get_score(lead_id)
        if not score:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead score not found")

        return LeadScore(
            lead_id=lead_id,
            score=score.score,
            confidence=score.confidence,
            factors=score.factors if include_factors else [],
            recommendations=score.recommendations if include_recommendations else []
        )

# 📌 Batch Score Multiple Leads
@router.post(
    "/score/batch",
    response_model=BatchResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Batch Score Multiple Leads"
)
async def score_leads_batch(request: BatchScoreRequest):
    """AI-powered batch scoring for multiple leads."""
    results, errors = [], []
    metadata = {"processed": 0, "successful": 0, "failed": 0}

    async def process_lead(lead: Lead):
        metadata["processed"] += 1

        if await lead_service.is_duplicate(lead):
            metadata["failed"] += 1
            return {"lead_id": lead.id, "error": "Duplicate lead detected"}

        try:
            score_result = await lead_scorer.analyze(
                lead_data=lead,
                include_factors=request.include_factors,
                generate_recommendations=request.generate_recommendations
            )
            metadata["successful"] += 1
            return LeadScore(
                lead_id=lead.id,
                score=score_result.score,
                confidence=score_result.confidence,
                factors=score_result.contributing_factors if request.include_factors else [],
                recommendations=score_result.recommendations if request.generate_recommendations else []
            )
        except Exception as e:
            metadata["failed"] += 1
            return {"lead_id": lead.id, "error": str(e)}

    async with track_operation("api/v1/leads/score/batch", "Batch Lead Scoring"):
        processed = await asyncio.gather(*[process_lead(lead) for lead in request.leads])

        for result in processed:
            if isinstance(result, dict) and "error" in result:
                errors.append(result)
            else:
                results.append(result)

        return BatchResponse(scores=results, errors=errors, metadata=metadata)

# 📌 Get Component Status
@router.get(
    "/status/{component_id}",
    dependencies=[Depends(RateLimiter(requests_per_minute=120))],
    summary="Get Component Status"
)
@cache(expire=60)
async def get_component_status(component_id: str):
    """Retrieve the status of a specific component."""
    status_info = tracker.get_status(component_id)
    if not status_info:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Component not found")
    return status_info

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
import asyncio
from aiqleads.core.ai_lead_scoring import LeadScorer
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.models.lead_model import Lead
from aiqleads.services.lead_service import LeadService
from aiqleads.utils.logging import logger
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


class LeadScore(BaseModel):
    lead_id: str
    score: float
    confidence: float
    factors: List[dict]
    recommendations: List[str]


class BatchResponse(BaseModel):
    scores: List[LeadScore]
    errors: List[dict]


# Singleton instances for shared resources
lead_scorer = LeadScorer()
lead_service = LeadService()
tracker = ProjectTracker()


@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """
    Context manager to track the status of operations and log errors.
    """
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


@router.post("/score", response_model=LeadScore)
async def score_lead(lead: Lead):
    """
    AI-powered scoring for a single lead.

    Parameters:
        lead (Lead): Lead data including contact info, preferences, and history.

    Returns:
        LeadScore: Scoring details with confidence and recommendations.
    """
    # Check for duplicate leads
    if await lead_service.is_duplicate(lead):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate lead detected"
        )

    async with track_operation("api/v1/leads/score", "Lead Scoring", lead_id=lead.id):
        score_result = await lead_scorer.analyze(
            lead_data=lead,
            include_factors=True,
            generate_recommendations=True
        )

        return LeadScore(
            lead_id=lead.id,
            score=score_result.score,
            confidence=score_result.confidence,
            factors=score_result.contributing_factors,
            recommendations=score_result.recommendations
        )


@router.get("/score/{lead_id}", response_model=LeadScore)
async def get_lead_score(lead_id: str):
    """
    Retrieve existing score for a lead.

    Parameters:
        lead_id (str): Unique identifier for the lead.

    Returns:
        LeadScore: Stored scoring information.
    """
    async with track_operation(
        "api/v1/leads/score/{lead_id}", "Retrieve Lead Score", lead_id=lead_id
    ):
        score = await lead_service.get_score(lead_id)
        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead score not found"
            )
        return score


@router.post("/score/batch", response_model=BatchResponse)
async def score_leads_batch(leads: List[Lead]):
    """
    AI-powered batch scoring for multiple leads.

    Parameters:
        leads (List[Lead]): List of leads to score.

    Returns:
        BatchResponse: Scoring results and error logs.
    """
    results, errors = [], []

    async def process_lead(lead: Lead):
        """Process a single lead and return its score or an error."""
        if await lead_service.is_duplicate(lead):
            return {"lead_id": lead.id, "error": "Duplicate lead detected"}
        
        try:
            score_result = await lead_scorer.analyze(
                lead_data=lead,
                include_factors=True,
                generate_recommendations=True
            )
            return LeadScore(
                lead_id=lead.id,
                score=score_result.score,
                confidence=score_result.confidence,
                factors=score_result.contributing_factors,
                recommendations=score_result.recommendations
            )
        except Exception as e:
            return {"lead_id": lead.id, "error": str(e)}

    async with track_operation("api/v1/leads/score/batch", "Batch Lead Scoring"):
        processed = await asyncio.gather(*[process_lead(lead) for lead in leads])

        for result in processed:
            if isinstance(result, dict) and "error" in result:
                errors.append(result)
            else:
                results.append(result)

        # Log partial success if errors occurred
        if errors:
            tracker.update_status(
                component_id="api/v1/leads/score/batch",
                status="⚠️ Partial Success",
                notes=f"Batch processing errors: {errors}"
            )

        return BatchResponse(scores=results, errors=errors)


@router.get("/status/{component_id}")
async def get_component_status(component_id: str):
    """
    Retrieve the status of a specific component.

    Parameters:
        component_id (str): Unique identifier for the component.

    Returns:
        dict: Status and notes for the component.
    """
    status_info = tracker.get_status(component_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    return status_info

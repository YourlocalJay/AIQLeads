from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi_cache import FastAPICache
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


class LeadScore(BaseModel):
    lead_id: str = Field(..., description="Unique identifier for the lead")
    score: float = Field(..., ge=0, le=100, description="Lead score between 0 and 100")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score between 0 and 1")
    factors: List[dict] = Field(..., description="Contributing factors to the score")
    recommendations: List[str] = Field(..., description="AI-generated recommendations")

    class Config:
        schema_extra = {
            "example": {
                "lead_id": "lead_123",
                "score": 85.5,
                "confidence": 0.92,
                "factors": [
                    {"name": "response_time", "impact": 0.8},
                    {"name": "budget_match", "impact": 0.6}
                ],
                "recommendations": [
                    "Schedule immediate follow-up",
                    "Prepare custom pricing proposal"
                ]
            }
        }


class LeadScoreRequest(BaseModel):
    lead: Lead
    include_factors: bool = Field(True, description="Include scoring factors in response")
    generate_recommendations: bool = Field(True, description="Generate AI recommendations")

    class Config:
        schema_extra = {
            "example": {
                "lead": {
                    "id": "lead_123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "budget": 50000
                },
                "include_factors": True,
                "generate_recommendations": True
            }
        }


class BatchScoreRequest(BaseModel):
    leads: List[Lead] = Field(..., max_items=100, description="List of leads to score")
    include_factors: bool = Field(True, description="Include scoring factors in response")
    generate_recommendations: bool = Field(True, description="Generate AI recommendations")


class BatchResponse(BaseModel):
    scores: List[LeadScore]
    errors: List[dict]
    metadata: dict = Field(
        default_factory=lambda: {"processed": 0, "successful": 0, "failed": 0}
    )


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


@router.post("/score", 
    response_model=LeadScore,
    dependencies=[Depends(RateLimiter(requests_per_minute=60))],
    summary="Score a single lead",
    description="AI-powered scoring for a single lead with detailed analysis and recommendations."
)
async def score_lead(request: LeadScoreRequest):
    """
    Score a single lead using AI analysis.

    Parameters:
        request (LeadScoreRequest): Lead data and scoring preferences.

    Returns:
        LeadScore: Detailed scoring information with confidence and recommendations.

    Raises:
        HTTPException: If lead is duplicate or scoring fails.
    """
    # Check for duplicate leads
    if await lead_service.is_duplicate(request.lead):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate lead detected"
        )

    async with track_operation("api/v1/leads/score", "Lead Scoring", lead_id=request.lead.id):
        score_result = await lead_scorer.analyze(
            lead_data=request.lead,
            include_factors=request.include_factors,
            generate_recommendations=request.generate_recommendations
        )

        return LeadScore(
            lead_id=request.lead.id,
            score=score_result.score,
            confidence=score_result.confidence,
            factors=score_result.contributing_factors if request.include_factors else [],
            recommendations=score_result.recommendations if request.generate_recommendations else []
        )


@router.get("/score/{lead_id}",
    response_model=LeadScore,
    dependencies=[Depends(RateLimiter(requests_per_minute=120))],
)
@cache(expire=300)  # Cache for 5 minutes
async def get_lead_score(lead_id: str, include_factors: bool = True, include_recommendations: bool = True):
    """
    Retrieve existing score for a lead.

    Parameters:
        lead_id (str): Unique identifier for the lead.
        include_factors (bool): Include scoring factors in response.
        include_recommendations (bool): Include recommendations in response.

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
        
        # Filter response based on parameters
        if not include_factors:
            score.factors = []
        if not include_recommendations:
            score.recommendations = []
            
        return score


@router.post("/score/batch",
    response_model=BatchResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
)
async def score_leads_batch(request: BatchScoreRequest):
    """
    AI-powered batch scoring for multiple leads.

    Parameters:
        request (BatchScoreRequest): Batch of leads to score and preferences.

    Returns:
        BatchResponse: Scoring results, errors, and batch metadata.
    """
    results, errors = [], []
    metadata = {"processed": 0, "successful": 0, "failed": 0}

    async def process_lead(lead: Lead):
        """Process a single lead and return its score or an error."""
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

        # Log partial success if errors occurred
        if errors:
            tracker.update_status(
                component_id="api/v1/leads/score/batch",
                status="⚠️ Partial Success",
                notes=f"Batch processing completed. Success: {metadata['successful']}, Failed: {metadata['failed']}"
            )

        return BatchResponse(scores=results, errors=errors, metadata=metadata)


@router.get("/status/{component_id}",
    dependencies=[Depends(RateLimiter(requests_per_minute=120))],
)
@cache(expire=60)  # Cache for 1 minute
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

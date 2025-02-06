import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from aiqleads.api.v1.endpoints.leads import (
    router, LeadScore, LeadScoreRequest, BatchScoreRequest, BatchResponse
)
from aiqleads.models.lead_model import Lead

# Test client setup
client = TestClient(router)

# Sample test data
SAMPLE_LEAD = Lead(
    id="lead_123",
    name="John Doe",
    email="john@example.com",
    phone="+1234567890",
    source="website",
    status="new",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    metadata={
        "budget": 50000,
        "priority": "high",
        "preferences": ["email", "phone"]
    }
)

SAMPLE_SCORE_RESULT = MagicMock(
    score=85.5,
    confidence=0.92,
    contributing_factors=[
        {"name": "response_time", "impact": 0.8},
        {"name": "budget_match", "impact": 0.6}
    ],
    recommendations=[
        "Schedule immediate follow-up",
        "Prepare custom pricing proposal"
    ]
)

@pytest.fixture
def mock_lead_scorer():
    with patch("aiqleads.api.v1.endpoints.leads.lead_scorer") as mock:
        mock.analyze = AsyncMock(return_value=SAMPLE_SCORE_RESULT)
        yield mock

@pytest.fixture
def mock_lead_service():
    with patch("aiqleads.api.v1.endpoints.leads.lead_service") as mock:
        mock.is_duplicate = AsyncMock(return_value=False)
        mock.get_score = AsyncMock(return_value=None)
        yield mock

@pytest.fixture
def mock_tracker():
    with patch("aiqleads.api.v1.endpoints.leads.tracker") as mock:
        mock.update_status = AsyncMock()
        mock.get_status = AsyncMock(return_value={"status": "🟢 Active", "notes": "Test status"})
        yield mock

@pytest.mark.asyncio
async def test_score_lead_success(mock_lead_scorer, mock_lead_service, mock_tracker):
    """Test successful scoring of a single lead"""
    request = LeadScoreRequest(
        lead=SAMPLE_LEAD,
        include_factors=True,
        generate_recommendations=True
    )
    
    response = await client.post("/api/v1/leads/score", json=request.dict())
    
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == SAMPLE_LEAD.id
    assert data["score"] == SAMPLE_SCORE_RESULT.score
    assert data["confidence"] == SAMPLE_SCORE_RESULT.confidence
    assert len(data["factors"]) == len(SAMPLE_SCORE_RESULT.contributing_factors)
    assert len(data["recommendations"]) == len(SAMPLE_SCORE_RESULT.recommendations)

@pytest.mark.asyncio
async def test_score_lead_without_factors(mock_lead_scorer, mock_lead_service):
    """Test lead scoring without factors and recommendations"""
    request = LeadScoreRequest(
        lead=SAMPLE_LEAD,
        include_factors=False,
        generate_recommendations=False
    )
    
    response = await client.post("/api/v1/leads/score", json=request.dict())
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["factors"]) == 0
    assert len(data["recommendations"]) == 0

@pytest.mark.asyncio
async def test_score_lead_duplicate(mock_lead_scorer, mock_lead_service):
    """Test duplicate lead detection"""
    mock_lead_service.is_duplicate.return_value = True
    
    request = LeadScoreRequest(lead=SAMPLE_LEAD)
    response = await client.post("/api/v1/leads/score", json=request.dict())
    
    assert response.status_code == 400
    assert "Duplicate lead detected" in response.json()["detail"]

@pytest.mark.asyncio
async def test_score_lead_scoring_failure(mock_lead_scorer, mock_lead_service):
    """Test handling of scoring failures"""
    mock_lead_scorer.analyze.side_effect = Exception("Scoring failed")
    
    request = LeadScoreRequest(lead=SAMPLE_LEAD)
    response = await client.post("/api/v1/leads/score", json=request.dict())
    
    assert response.status_code == 500
    assert "Failed to score lead" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_lead_score_success(mock_lead_service):
    """Test successful retrieval of existing lead score"""
    mock_lead_service.get_score.return_value = MagicMock(
        score=85.5,
        confidence=0.92,
        factors=SAMPLE_SCORE_RESULT.contributing_factors,
        recommendations=SAMPLE_SCORE_RESULT.recommendations
    )
    
    response = await client.get(
        f"/api/v1/leads/score/{SAMPLE_LEAD.id}",
        params={"include_factors": True, "include_recommendations": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == SAMPLE_LEAD.id
    assert data["score"] == 85.5
    assert len(data["factors"]) > 0
    assert len(data["recommendations"]) > 0

@pytest.mark.asyncio
async def test_get_lead_score_not_found(mock_lead_service):
    """Test handling of non-existent lead score"""
    mock_lead_service.get_score.return_value = None
    
    response = await client.get(f"/api/v1/leads/score/nonexistent")
    
    assert response.status_code == 404
    assert "Lead score not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_batch_scoring_success(mock_lead_scorer, mock_lead_service):
    """Test successful batch scoring"""
    leads = [
        Lead(id="lead1", name="John Doe", email="john@example.com"),
        Lead(id="lead2", name="Jane Smith", email="jane@example.com")
    ]
    
    request = BatchScoreRequest(
        leads=leads,
        include_factors=True,
        generate_recommendations=True
    )
    
    response = await client.post("/api/v1/leads/score/batch", json=request.dict())
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["scores"]) == 2
    assert data["metadata"]["processed"] == 2
    assert data["metadata"]["successful"] == 2
    assert data["metadata"]["failed"] == 0
    assert len(data["errors"]) == 0

@pytest.mark.asyncio
async def test_batch_scoring_with_errors(mock_lead_scorer, mock_lead_service):
    """Test batch scoring with some failures"""
    mock_lead_service.is_duplicate.side_effect = [True, False]
    mock_lead_scorer.analyze.side_effect = [Exception("Scoring failed"), SAMPLE_SCORE_RESULT]
    
    leads = [
        Lead(id="lead1", name="John Doe", email="john@example.com"),
        Lead(id="lead2", name="Jane Smith", email="jane@example.com")
    ]
    
    request = BatchScoreRequest(leads=leads)
    response = await client.post("/api/v1/leads/score/batch", json=request.dict())
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["scores"]) == 1
    assert len(data["errors"]) == 1
    assert data["metadata"]["processed"] == 2
    assert data["metadata"]["successful"] == 1
    assert data["metadata"]["failed"] == 1

@pytest.mark.asyncio
async def test_get_component_status_success(mock_tracker):
    """Test successful retrieval of component status"""
    response = await client.get("/api/v1/leads/status/test_component")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "🟢 Active"
    assert "notes" in data

@pytest.mark.asyncio
async def test_get_component_status_not_found(mock_tracker):
    """Test handling of non-existent component status"""
    mock_tracker.get_status.return_value = None
    
    response = await client.get("/api/v1/leads/status/nonexistent")
    
    assert response.status_code == 404
    assert "Component not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_rate_limiting(mock_lead_service):
    """Test rate limiting on lead scoring endpoints"""
    request = LeadScoreRequest(lead=SAMPLE_LEAD)
    responses = []
    
    # Test rate limit on score endpoint (60 requests/minute)
    for _ in range(70):
        response = await client.post("/api/v1/leads/score", json=request.dict())
        responses.append(response.status_code)
    
    assert 429 in responses  # Should see some rate limit responses

@pytest.mark.asyncio
async def test_response_caching(mock_lead_service):
    """Test response caching for get endpoints"""
    mock_lead_service.get_score.return_value = MagicMock(
        score=85.5,
        confidence=0.92,
        factors=SAMPLE_SCORE_RESULT.contributing_factors,
        recommendations=SAMPLE_SCORE_RESULT.recommendations
    )
    
    # First request
    response1 = await client.get(f"/api/v1/leads/score/{SAMPLE_LEAD.id}")
    assert response1.status_code == 200
    
    # Change mock return value
    mock_lead_service.get_score.return_value = None
    
    # Second request should return cached response
    response2 = await client.get(f"/api/v1/leads/score/{SAMPLE_LEAD.id}")
    assert response2.status_code == 200
    assert response2.json() == response1.json()

if __name__ == "__main__":
    pytest.main(["-v", "test_leads.py"])

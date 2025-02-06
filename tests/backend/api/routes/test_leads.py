import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from aiqleads.api.v1.endpoints.leads import router, LeadScoreRequest, BatchScoreRequest
from aiqleads.models.lead_model import Lead
from aiqleads.core.ai_lead_scoring import LeadScorer
from aiqleads.services.lead_service import LeadService

# Test client setup
client = TestClient(router)

# Mock data
SAMPLE_LEAD = Lead(
    id="test_lead_1",
    name="John Doe",
    email="john@example.com",
    budget=50000
)

SAMPLE_SCORE_RESULT = AsyncMock(
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

@pytest.mark.asyncio
async def test_score_lead_success(mock_lead_scorer, mock_lead_service):
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
async def test_score_lead_duplicate(mock_lead_scorer, mock_lead_service):
    """Test duplicate lead detection"""
    mock_lead_service.is_duplicate.return_value = True
    
    request = LeadScoreRequest(lead=SAMPLE_LEAD)
    response = await client.post("/api/v1/leads/score", json=request.dict())
    
    assert response.status_code == 400
    assert "Duplicate lead" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_lead_score_success(mock_lead_service):
    """Test successful retrieval of existing lead score"""
    mock_lead_service.get_score.return_value = {
        "lead_id": SAMPLE_LEAD.id,
        "score": 85.5,
        "confidence": 0.92,
        "factors": SAMPLE_SCORE_RESULT.contributing_factors,
        "recommendations": SAMPLE_SCORE_RESULT.recommendations
    }
    
    response = await client.get(f"/api/v1/leads/score/{SAMPLE_LEAD.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == SAMPLE_LEAD.id
    assert data["score"] == 85.5

@pytest.mark.asyncio
async def test_get_lead_score_not_found(mock_lead_service):
    """Test handling of non-existent lead score"""
    mock_lead_service.get_score.return_value = None
    
    response = await client.get(f"/api/v1/leads/score/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_batch_scoring_success(mock_lead_scorer, mock_lead_service):
    """Test successful batch scoring"""
    leads = [
        Lead(id="lead1", name="John Doe", email="john@example.com", budget=50000),
        Lead(id="lead2", name="Jane Smith", email="jane@example.com", budget=75000)
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
    
    leads = [
        Lead(id="lead1", name="John Doe", email="john@example.com", budget=50000),
        Lead(id="lead2", name="Jane Smith", email="jane@example.com", budget=75000)
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
async def test_rate_limiting(mock_lead_service):
    """Test rate limiting functionality"""
    # Simulate multiple requests
    responses = []
    for _ in range(70):  # Exceeds rate limit of 60/minute
        response = await client.get("/api/v1/leads/score/test")
        responses.append(response.status_code)
    
    # Should see some 429 Too Many Requests
    assert 429 in responses

@pytest.mark.asyncio
async def test_response_caching(mock_lead_service):
    """Test response caching"""
    mock_lead_service.get_score.return_value = {
        "lead_id": SAMPLE_LEAD.id,
        "score": 85.5,
        "confidence": 0.92,
        "factors": [],
        "recommendations": []
    }
    
    # First request should hit the service
    response1 = await client.get(f"/api/v1/leads/score/{SAMPLE_LEAD.id}")
    assert response1.status_code == 200
    
    # Change the mock return value
    mock_lead_service.get_score.return_value = None
    
    # Second request should return cached response
    response2 = await client.get(f"/api/v1/leads/score/{SAMPLE_LEAD.id}")
    assert response2.status_code == 200
    assert response2.json() == response1.json()

@pytest.mark.asyncio
async def test_component_status(mock_lead_service):
    """Test component status endpoint"""
    response = await client.get("/api/v1/leads/status/api/v1/leads/score")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "notes" in data

if __name__ == "__main__":
    pytest.main(["-v", "test_leads.py"])

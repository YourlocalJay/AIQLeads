import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from aiqleads.api.v1.endpoints.analytics import (
    router, TimeRange, PerformanceMetrics, LeadInsights,
    MarketSegment, PredictiveAnalytics
)
from aiqleads.models.user_model import User

# Test client setup
client = TestClient(router)

# Mock data
SAMPLE_USER = User(
    id="test_user_1",
    email="test@example.com",
    full_name="Test User",
    credits_balance=1000.0,
    is_active=True,
    last_login=datetime.utcnow(),
    subscription_tier="professional",
    features_enabled=["analytics"],
    scopes=["user"]
)

SAMPLE_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test_token"

SAMPLE_TIME_RANGE = TimeRange(
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow(),
    granularity="day"
)

SAMPLE_PERFORMANCE_METRICS = {
    "conversion_rate": 0.35,
    "average_response_time": 2.5,
    "lead_quality_score": 85.5,
    "engagement_rate": 0.75,
    "roi": 3.2
}

SAMPLE_LEAD_INSIGHTS = {
    "total_leads": 1250,
    "qualified_leads": 450,
    "conversion_rate": 0.36,
    "average_deal_size": 25000.0,
    "top_sources": [
        {"source": "website", "count": 500, "conversion_rate": 0.4},
        {"source": "referral", "count": 300, "conversion_rate": 0.35}
    ],
    "growth_rate": 0.15
}

SAMPLE_MARKET_SEGMENTS = [
    {
        "segment_name": "enterprise",
        "size": 500,
        "average_budget": 100000.0,
        "conversion_rate": 0.4,
        "lifetime_value": 500000.0,
        "growth_potential": 0.8
    }
]

SAMPLE_PREDICTIVE_ANALYTICS = {
    "lead_scoring_accuracy": 0.92,
    "churn_risk_factors": [
        {"factor": "response_time", "impact": 0.8},
        {"factor": "engagement", "impact": 0.6}
    ],
    "growth_opportunities": [
        {
            "segment": "enterprise",
            "potential": 0.85,
            "estimated_value": 500000
        }
    ],
    "market_trends": [
        {
            "trend": "increased_digital_adoption",
            "impact": "positive",
            "probability": 0.9
        }
    ],
    "recommendations": [
        "Focus on enterprise segment expansion",
        "Improve response time automation"
    ]
}

@pytest.fixture
def mock_user_service():
    with patch("aiqleads.api.v1.endpoints.analytics.user_service") as mock:
        mock.get_current_user = AsyncMock(return_value=SAMPLE_USER)
        yield mock

@pytest.fixture
def mock_analytics_service():
    with patch("aiqleads.api.v1.endpoints.analytics.analytics_service") as mock:
        mock.calculate_performance_metrics = AsyncMock(return_value=SAMPLE_PERFORMANCE_METRICS)
        mock.analyze_leads = AsyncMock(return_value=SAMPLE_LEAD_INSIGHTS)
        mock.analyze_market_segments = AsyncMock(return_value=SAMPLE_MARKET_SEGMENTS)
        mock.generate_predictions = AsyncMock(return_value=SAMPLE_PREDICTIVE_ANALYTICS)
        mock.generate_custom_analytics = AsyncMock(return_value={})
        mock.export_analytics = AsyncMock(return_value={"url": "http://example.com/export"})
        yield mock

@pytest.mark.asyncio
async def test_get_performance_metrics_success(mock_user_service, mock_analytics_service):
    """Test successful retrieval of performance metrics"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/performance",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversion_rate"] == SAMPLE_PERFORMANCE_METRICS["conversion_rate"]
    assert data["lead_quality_score"] == SAMPLE_PERFORMANCE_METRICS["lead_quality_score"]

@pytest.mark.asyncio
async def test_get_performance_metrics_unauthorized(mock_user_service):
    """Test unauthorized access to performance metrics"""
    mock_user_service.get_current_user.return_value = None
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/performance",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_lead_insights_success(mock_user_service, mock_analytics_service):
    """Test successful retrieval of lead insights"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/leads",
        params={**SAMPLE_TIME_RANGE.dict(), "segment": "enterprise"},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_leads"] == SAMPLE_LEAD_INSIGHTS["total_leads"]
    assert len(data["top_sources"]) == len(SAMPLE_LEAD_INSIGHTS["top_sources"])

@pytest.mark.asyncio
async def test_get_market_segments_success(mock_user_service, mock_analytics_service):
    """Test successful retrieval of market segments"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/market-segments",
        params={**SAMPLE_TIME_RANGE.dict(), "min_size": 100},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(SAMPLE_MARKET_SEGMENTS)
    assert data[0]["segment_name"] == SAMPLE_MARKET_SEGMENTS[0]["segment_name"]

@pytest.mark.asyncio
async def test_get_predictive_analytics_success(mock_user_service, mock_analytics_service):
    """Test successful retrieval of predictive analytics"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/predictive",
        params={**SAMPLE_TIME_RANGE.dict(), "confidence_threshold": 0.8},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["lead_scoring_accuracy"] == SAMPLE_PREDICTIVE_ANALYTICS["lead_scoring_accuracy"]
    assert len(data["recommendations"]) == len(SAMPLE_PREDICTIVE_ANALYTICS["recommendations"])

@pytest.mark.asyncio
async def test_get_custom_analytics_success(mock_user_service, mock_analytics_service):
    """Test successful retrieval of custom analytics"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/custom",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "metrics": ["conversion_rate", "roi"],
            "filters": {"segment": "enterprise"}
        },
        headers=headers
    )
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_export_analytics_success(mock_user_service, mock_analytics_service):
    """Test successful export of analytics data"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/analytics/export",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "metrics": ["conversion_rate", "roi"],
            "format": "csv"
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data

@pytest.mark.asyncio
async def test_rate_limiting(mock_user_service, mock_analytics_service):
    """Test rate limiting on analytics endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    responses = []
    
    # Test rate limit on performance metrics endpoint (30 requests/minute)
    for _ in range(35):
        response = await client.get(
            "/api/v1/analytics/performance",
            params=SAMPLE_TIME_RANGE.dict(),
            headers=headers
        )
        responses.append(response.status_code)
    
    assert 429 in responses  # Should see some rate limit responses

@pytest.mark.asyncio
async def test_response_caching(mock_user_service, mock_analytics_service):
    """Test response caching for analytics endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    
    # First request
    response1 = await client.get(
        "/api/v1/analytics/performance",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    assert response1.status_code == 200
    
    # Change mock data
    mock_analytics_service.calculate_performance_metrics.return_value = {
        **SAMPLE_PERFORMANCE_METRICS,
        "conversion_rate": 0.5
    }
    
    # Second request should return cached response
    response2 = await client.get(
        "/api/v1/analytics/performance",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    assert response2.status_code == 200
    assert response2.json() == response1.json()

if __name__ == "__main__":
    pytest.main(["-v", "test_analytics.py"])

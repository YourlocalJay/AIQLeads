import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from aiqleads.api.v1.endpoints.market_trends import (
    router, TimeRange, MarketTrend, Forecast, Opportunity
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
    features_enabled=["market_trends"],
    scopes=["user"]
)

SAMPLE_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test_token"

SAMPLE_TIME_RANGE = TimeRange(
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow(),
    granularity="day"
)

SAMPLE_TREND = {
    "trend_id": "trend_123",
    "name": "Rising Digital Marketing ROI",
    "description": "Increasing effectiveness of digital marketing...",
    "confidence": 0.85,
    "impact": "positive",
    "affected_segments": ["SMB", "Enterprise"],
    "predicted_duration": 90,
    "data_points": [
        {"date": "2025-01-01", "value": 1.2},
        {"date": "2025-01-02", "value": 1.3}
    ],
    "recommendations": [
        "Increase digital marketing budget",
        "Focus on content marketing"
    ]
}

SAMPLE_FORECAST = {
    "forecast_id": "forecast_123",
    "metric": "lead_conversion_rate",
    "current_value": 0.25,
    "predicted_value": 0.35,
    "confidence_interval": [0.30, 0.40],
    "factors": [
        {"name": "market_growth", "impact": 0.6},
        {"name": "competition", "impact": -0.2}
    ],
    "timeline": "3_months",
    "probability": 0.85
}

SAMPLE_OPPORTUNITY = {
    "opportunity_id": "opp_123",
    "title": "Expand into Healthcare Sector",
    "description": "Growing demand for AI solutions...",
    "potential_value": 1000000.0,
    "success_probability": 0.75,
    "market_size": 5000000.0,
    "competition_level": "medium",
    "required_resources": ["domain_expertise", "sales_team"],
    "timeline": "6_months",
    "risk_factors": [
        {"factor": "regulation", "impact": "high"},
        {"factor": "adoption_rate", "impact": "medium"}
    ]
}

SAMPLE_COMPETITIVE_ANALYSIS = {
    "market_share": {
        "company": 25.0,
        "competitors": {
            "competitor_1": 30.0,
            "competitor_2": 20.0
        }
    },
    "strengths": ["AI technology", "Customer service"],
    "weaknesses": ["Market presence", "Brand recognition"],
    "opportunities": ["Healthcare sector", "International markets"],
    "threats": ["New entrants", "Regulatory changes"]
}

SAMPLE_SENTIMENT = {
    "overall_sentiment": "positive",
    "confidence": 0.85,
    "sentiment_by_source": {
        "news": 0.8,
        "social_media": 0.7,
        "industry_reports": 0.9
    },
    "key_topics": [
        {"topic": "AI adoption", "sentiment": 0.9},
        {"topic": "Market growth", "sentiment": 0.8}
    ]
}

SAMPLE_ALERTS = [
    {
        "alert_id": "alert_123",
        "type": "market_shift",
        "severity": "high",
        "title": "Emerging Market Opportunity",
        "description": "Rapid growth in healthcare sector...",
        "probability": 0.85,
        "recommended_actions": [
            "Develop healthcare-specific solutions",
            "Partner with healthcare providers"
        ]
    }
]

@pytest.fixture
def mock_user_service():
    with patch("aiqleads.api.v1.endpoints.market_trends.user_service") as mock:
        mock.get_current_user = AsyncMock(return_value=SAMPLE_USER)
        yield mock

@pytest.fixture
def mock_market_trends_service():
    with patch("aiqleads.api.v1.endpoints.market_trends.market_trends_service") as mock:
        mock.analyze_trends = AsyncMock(return_value=[SAMPLE_TREND])
        mock.generate_forecasts = AsyncMock(return_value=[SAMPLE_FORECAST])
        mock.identify_opportunities = AsyncMock(return_value=[SAMPLE_OPPORTUNITY])
        mock.analyze_competition = AsyncMock(return_value=SAMPLE_COMPETITIVE_ANALYSIS)
        mock.analyze_sentiment = AsyncMock(return_value=SAMPLE_SENTIMENT)
        mock.generate_alerts = AsyncMock(return_value=SAMPLE_ALERTS)
        mock.create_alert_subscription = AsyncMock(return_value={"status": "subscribed"})
        yield mock

@pytest.mark.asyncio
async def test_get_market_trends_success(mock_user_service, mock_market_trends_service):
    """Test successful retrieval of market trends"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/trends",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "segment": "Enterprise",
            "min_confidence": 0.7
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["trend_id"] == SAMPLE_TREND["trend_id"]
    assert data[0]["confidence"] == SAMPLE_TREND["confidence"]

@pytest.mark.asyncio
async def test_get_forecasts_success(mock_user_service, mock_market_trends_service):
    """Test successful retrieval of forecasts"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/forecasts",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "metrics": ["lead_conversion_rate"],
            "min_probability": 0.7
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["forecast_id"] == SAMPLE_FORECAST["forecast_id"]
    assert data[0]["probability"] == SAMPLE_FORECAST["probability"]

@pytest.mark.asyncio
async def test_get_opportunities_success(mock_user_service, mock_market_trends_service):
    """Test successful retrieval of opportunities"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/opportunities",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "min_value": 500000,
            "min_probability": 0.6,
            "sector": "healthcare"
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["opportunity_id"] == SAMPLE_OPPORTUNITY["opportunity_id"]
    assert data[0]["success_probability"] == SAMPLE_OPPORTUNITY["success_probability"]

@pytest.mark.asyncio
async def test_get_competitive_analysis_success(mock_user_service, mock_market_trends_service):
    """Test successful retrieval of competitive analysis"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/competitive-analysis",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "sector": "healthcare",
            "competitors": ["competitor_1", "competitor_2"]
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "market_share" in data
    assert "strengths" in data
    assert "weaknesses" in data

@pytest.mark.asyncio
async def test_get_market_sentiment_success(mock_user_service, mock_market_trends_service):
    """Test successful retrieval of market sentiment"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/sentiment-analysis",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "sector": "healthcare",
            "sources": ["news", "social_media"]
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["overall_sentiment"] == SAMPLE_SENTIMENT["overall_sentiment"]
    assert data["confidence"] == SAMPLE_SENTIMENT["confidence"]

@pytest.mark.asyncio
async def test_get_market_alerts_success(mock_user_service, mock_market_trends_service):
    """Test successful retrieval of market alerts"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/alerts",
        params={
            **SAMPLE_TIME_RANGE.dict(),
            "alert_types": ["market_shift"],
            "min_severity": "medium"
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["alert_id"] == SAMPLE_ALERTS[0]["alert_id"]
    assert data[0]["severity"] == SAMPLE_ALERTS[0]["severity"]

@pytest.mark.asyncio
async def test_subscribe_to_alerts_success(mock_user_service, mock_market_trends_service):
    """Test successful alert subscription"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.post(
        "/api/v1/market-trends/subscribe",
        params={
            "alert_types": ["market_shift", "competitor_activity"],
            "frequency": "daily"
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "subscribed"

@pytest.mark.asyncio
async def test_unauthorized_access(mock_user_service):
    """Test unauthorized access to market trends endpoints"""
    mock_user_service.get_current_user.return_value = None
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/market-trends/trends",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_rate_limiting(mock_user_service, mock_market_trends_service):
    """Test rate limiting on market trends endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    responses = []
    
    # Test rate limit on trends endpoint (30 requests/minute)
    for _ in range(35):
        response = await client.get(
            "/api/v1/market-trends/trends",
            params=SAMPLE_TIME_RANGE.dict(),
            headers=headers
        )
        responses.append(response.status_code)
    
    assert 429 in responses  # Should see some rate limit responses

@pytest.mark.asyncio
async def test_response_caching(mock_user_service, mock_market_trends_service):
    """Test response caching for market trends endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    
    # First request
    response1 = await client.get(
        "/api/v1/market-trends/trends",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    assert response1.status_code == 200
    
    # Change mock data
    mock_market_trends_service.analyze_trends.return_value = [
        {**SAMPLE_TREND, "confidence": 0.95}
    ]
    
    # Second request should return cached response
    response2 = await client.get(
        "/api/v1/market-trends/trends",
        params=SAMPLE_TIME_RANGE.dict(),
        headers=headers
    )
    assert response2.status_code == 200
    assert response2.json() == response1.json()

if __name__ == "__main__":
    pytest.main(["-v", "test_market_trends.py"])

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from aiqleads.api.v1.endpoints.users import router, UserCreate, UserUpdate, CreditTransaction
from aiqleads.models.user_model import User
from aiqleads.services.user_service import UserService

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
    features_enabled=["lead_scoring", "market_analysis"],
    scopes=["user"]
)

SAMPLE_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test_token"

@pytest.fixture
def mock_user_service():
    with patch("aiqleads.api.v1.endpoints.users.user_service") as mock:
        mock.authenticate_user = AsyncMock(return_value=SAMPLE_USER)
        mock.create_access_token = AsyncMock(return_value=SAMPLE_TOKEN)
        mock.create_refresh_token = AsyncMock(return_value=f"{SAMPLE_TOKEN}_refresh")
        mock.get_current_user = AsyncMock(return_value=SAMPLE_USER)
        mock.get_user_by_email = AsyncMock(return_value=None)
        mock.create_user = AsyncMock(return_value=SAMPLE_USER)
        mock.update_user = AsyncMock(return_value=SAMPLE_USER)
        mock.update_credits = AsyncMock(return_value=SAMPLE_USER)
        mock.get_credit_history = AsyncMock(return_value=[])
        mock.upgrade_subscription = AsyncMock(return_value=SAMPLE_USER)
        yield mock

@pytest.mark.asyncio
async def test_login_success(mock_user_service):
    """Test successful user login"""
    response = await client.post(
        "/api/v1/users/token",
        data={"username": "test@example.com", "password": "testpass"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == SAMPLE_TOKEN
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["refresh_token"] == f"{SAMPLE_TOKEN}_refresh"

@pytest.mark.asyncio
async def test_login_failure(mock_user_service):
    """Test failed login attempt"""
    mock_user_service.authenticate_user.return_value = None
    
    response = await client.post(
        "/api/v1/users/token",
        data={"username": "wrong@example.com", "password": "wrongpass"}
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_user_success(mock_user_service):
    """Test successful user registration"""
    user_data = {
        "email": "new@example.com",
        "password": "newpass123",
        "full_name": "New User"
    }
    
    response = await client.post("/api/v1/users/register", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == SAMPLE_USER.email
    assert data["full_name"] == SAMPLE_USER.full_name

@pytest.mark.asyncio
async def test_register_user_duplicate(mock_user_service):
    """Test registration with existing email"""
    mock_user_service.get_user_by_email.return_value = SAMPLE_USER
    
    user_data = {
        "email": "test@example.com",
        "password": "testpass",
        "full_name": "Test User"
    }
    
    response = await client.post("/api/v1/users/register", json=user_data)
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_current_user(mock_user_service):
    """Test getting current user details"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == SAMPLE_USER.email
    assert data["credits_balance"] == SAMPLE_USER.credits_balance

@pytest.mark.asyncio
async def test_update_user(mock_user_service):
    """Test updating user information"""
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.put("/api/v1/users/me", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == SAMPLE_USER.email
    assert data["full_name"] == SAMPLE_USER.full_name

@pytest.mark.asyncio
async def test_manage_credits_add(mock_user_service):
    """Test adding credits to user account"""
    transaction = {
        "amount": 500.0,
        "description": "Purchase of additional credits",
        "transaction_type": "add"
    }
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.post("/api/v1/users/credits", json=transaction, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["credits_balance"] == SAMPLE_USER.credits_balance

@pytest.mark.asyncio
async def test_manage_credits_subtract_insufficient(mock_user_service):
    """Test subtracting more credits than available"""
    transaction = {
        "amount": 2000.0,
        "description": "Attempt to use more credits than available",
        "transaction_type": "subtract"
    }
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.post("/api/v1/users/credits", json=transaction, headers=headers)
    
    assert response.status_code == 400
    assert "Insufficient credits" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_credit_history(mock_user_service):
    """Test retrieving credit transaction history"""
    mock_user_service.get_credit_history.return_value = [
        {
            "timestamp": datetime.utcnow(),
            "amount": 500.0,
            "transaction_type": "add",
            "description": "Credit purchase"
        }
    ]
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get("/api/v1/users/credits/history", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["amount"] == 500.0

@pytest.mark.asyncio
async def test_upgrade_subscription(mock_user_service):
    """Test upgrading user subscription"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.post(
        "/api/v1/users/subscription/upgrade",
        params={"tier": "enterprise"},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["subscription_tier"] == SAMPLE_USER.subscription_tier

@pytest.mark.asyncio
async def test_refresh_token_success(mock_user_service):
    """Test successful token refresh"""
    response = await client.post(
        "/api/v1/users/refresh",
        params={"refresh_token": f"{SAMPLE_TOKEN}_refresh"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == SAMPLE_TOKEN
    assert data["expires_in"] == 3600

@pytest.mark.asyncio
async def test_rate_limiting(mock_user_service):
    """Test rate limiting on endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    responses = []
    
    # Test rate limit on user details endpoint (60 requests/minute)
    for _ in range(70):
        response = await client.get("/api/v1/users/me", headers=headers)
        responses.append(response.status_code)
    
    assert 429 in responses  # Should see some rate limit responses

@pytest.mark.asyncio
async def test_response_caching(mock_user_service):
    """Test response caching for get endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    
    # First request
    response1 = await client.get("/api/v1/users/me", headers=headers)
    assert response1.status_code == 200
    
    # Change mock data
    new_user = SAMPLE_USER.copy()
    new_user.full_name = "Changed Name"
    mock_user_service.get_current_user.return_value = new_user
    
    # Second request should return cached response
    response2 = await client.get("/api/v1/users/me", headers=headers)
    assert response2.status_code == 200
    assert response2.json() == response1.json()

if __name__ == "__main__":
    pytest.main(["-v", "test_users.py"])

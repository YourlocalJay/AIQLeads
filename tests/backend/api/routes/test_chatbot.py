import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from aiqleads.api.v1.endpoints.chatbot import (
    router, Message, Conversation, ChatResponse
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
    features_enabled=["chatbot"],
    scopes=["user"]
)

SAMPLE_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test_token"

SAMPLE_CONVERSATION_ID = "conv_123"

SAMPLE_MESSAGE = {
    "content": "Tell me about lead XYZ's engagement history",
    "role": "user",
    "timestamp": datetime.utcnow().isoformat(),
    "metadata": {
        "lead_id": "lead_xyz",
        "context": "engagement_history"
    }
}

SAMPLE_RESPONSE = {
    "message": {
        "content": "Lead XYZ has shown increasing engagement...",
        "role": "assistant",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "lead_id": "lead_xyz",
            "confidence": 0.95
        }
    },
    "suggested_actions": [
        "Schedule follow-up call",
        "Send personalized proposal"
    ],
    "confidence_score": 0.95,
    "requires_human": False,
    "follow_up_questions": [
        "Would you like to see their contact history?",
        "Should I analyze their purchase patterns?"
    ]
}

SAMPLE_CONVERSATION = {
    "id": SAMPLE_CONVERSATION_ID,
    "messages": [SAMPLE_MESSAGE],
    "context": {"lead_id": "lead_xyz"},
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

@pytest.fixture
def mock_user_service():
    with patch("aiqleads.api.v1.endpoints.chatbot.user_service") as mock:
        mock.get_current_user = AsyncMock(return_value=SAMPLE_USER)
        yield mock

@pytest.fixture
def mock_chatbot_service():
    with patch("aiqleads.api.v1.endpoints.chatbot.chatbot_service") as mock:
        mock.process_message = AsyncMock(return_value=SAMPLE_RESPONSE)
        mock.get_conversation = AsyncMock(return_value=SAMPLE_CONVERSATION)
        mock.create_conversation = AsyncMock(return_value=SAMPLE_CONVERSATION)
        mock.list_conversations = AsyncMock(return_value=[SAMPLE_CONVERSATION])
        mock.update_context = AsyncMock(return_value=SAMPLE_CONVERSATION)
        mock.submit_feedback = AsyncMock(return_value=True)
        mock.delete_conversation = AsyncMock(return_value=True)
        mock.log_interaction = AsyncMock()
        yield mock

@pytest.mark.asyncio
async def test_send_message_success(mock_user_service, mock_chatbot_service):
    """Test successful message sending"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.post(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}/message",
        json=SAMPLE_MESSAGE,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == SAMPLE_RESPONSE["message"]["content"]
    assert len(data["suggested_actions"]) == len(SAMPLE_RESPONSE["suggested_actions"])
    assert data["confidence_score"] == SAMPLE_RESPONSE["confidence_score"]

@pytest.mark.asyncio
async def test_send_message_unauthorized(mock_user_service):
    """Test unauthorized message sending"""
    mock_user_service.get_current_user.return_value = None
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.post(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}/message",
        json=SAMPLE_MESSAGE,
        headers=headers
    )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_conversation_success(mock_user_service, mock_chatbot_service):
    """Test successful conversation retrieval"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == SAMPLE_CONVERSATION_ID
    assert len(data["messages"]) == len(SAMPLE_CONVERSATION["messages"])

@pytest.mark.asyncio
async def test_get_conversation_not_found(mock_user_service, mock_chatbot_service):
    """Test retrieval of non-existent conversation"""
    mock_chatbot_service.get_conversation.return_value = None
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}",
        headers=headers
    )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_conversation_success(mock_user_service, mock_chatbot_service):
    """Test successful conversation creation"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    initial_context = {"lead_id": "lead_xyz"}
    
    response = await client.post(
        "/api/v1/chatbot/conversations",
        json={"initial_context": initial_context},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == SAMPLE_CONVERSATION_ID
    assert data["context"] == initial_context

@pytest.mark.asyncio
async def test_list_conversations_success(mock_user_service, mock_chatbot_service):
    """Test successful conversation listing"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.get(
        "/api/v1/chatbot/conversations",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == SAMPLE_CONVERSATION_ID

@pytest.mark.asyncio
async def test_update_context_success(mock_user_service, mock_chatbot_service):
    """Test successful context update"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    context_updates = {"new_key": "new_value"}
    
    response = await client.post(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}/context",
        json=context_updates,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == SAMPLE_CONVERSATION_ID

@pytest.mark.asyncio
async def test_submit_feedback_success(mock_user_service, mock_chatbot_service):
    """Test successful feedback submission"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    feedback = {"rating": 5, "comment": "Very helpful response"}
    
    response = await client.post(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}/feedback",
        params={"message_id": "msg_123"},
        json=feedback,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

@pytest.mark.asyncio
async def test_delete_conversation_success(mock_user_service, mock_chatbot_service):
    """Test successful conversation deletion"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.delete(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

@pytest.mark.asyncio
async def test_delete_conversation_not_found(mock_user_service, mock_chatbot_service):
    """Test deletion of non-existent conversation"""
    mock_chatbot_service.delete_conversation.return_value = False
    
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    response = await client.delete(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}",
        headers=headers
    )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_rate_limiting(mock_user_service, mock_chatbot_service):
    """Test rate limiting on chatbot endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    responses = []
    
    # Test rate limit on message endpoint (60 requests/minute)
    for _ in range(70):
        response = await client.post(
            f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}/message",
            json=SAMPLE_MESSAGE,
            headers=headers
        )
        responses.append(response.status_code)
    
    assert 429 in responses  # Should see some rate limit responses

@pytest.mark.asyncio
async def test_response_caching(mock_user_service, mock_chatbot_service):
    """Test response caching for get endpoints"""
    headers = {"Authorization": f"Bearer {SAMPLE_TOKEN}"}
    
    # First request
    response1 = await client.get(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}",
        headers=headers
    )
    assert response1.status_code == 200
    
    # Change mock data
    new_conversation = {**SAMPLE_CONVERSATION}
    new_conversation["context"] = {"new_key": "new_value"}
    mock_chatbot_service.get_conversation.return_value = new_conversation
    
    # Second request should return cached response
    response2 = await client.get(
        f"/api/v1/chatbot/{SAMPLE_CONVERSATION_ID}",
        headers=headers
    )
    assert response2.status_code == 200
    assert response2.json() == response1.json()

if __name__ == "__main__":
    pytest.main(["-v", "test_chatbot.py"])

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.chatbot_service import ChatbotService
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from contextlib import asynccontextmanager
from uuid import uuid4

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])

# Initialize services
chatbot_service = ChatbotService()
user_service = UserService()
tracker = ProjectTracker()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

# 📌 Message Model
class Message(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    role: str = Field("user", regex="^(user|assistant|system)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

# 📌 Conversation Model
class Conversation(BaseModel):
    id: str
    messages: List[Message]
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# 📌 Chat Response Model
class ChatResponse(BaseModel):
    message: Message
    suggested_actions: List[str] = []
    confidence_score: float = Field(..., ge=0, le=1)
    requires_human: bool = False
    follow_up_questions: List[str] = []

# 📌 Send Message to Chatbot
@router.post(
    "/{conversation_id}/message",
    response_model=ChatResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=60))],
    summary="Send a Message to the Chatbot"
)
async def send_message(
    conversation_id: str,
    message: Message,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme)
):
    """Process a user message and return an AI chatbot response."""
    async with track_operation("api/v1/chatbot/message", "Process Chat Message", conversation_id=conversation_id):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        conversation = await chatbot_service.get_conversation(user.id, conversation_id)
        if not conversation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

        response = await chatbot_service.process_message(
            user_id=user.id,
            conversation_id=conversation_id,
            message=message
        )

        # Background logging task
        background_tasks.add_task(chatbot_service.log_interaction, user.id, conversation_id, message, response)

        return response

# 📌 Get Conversation History
@router.get(
    "/{conversation_id}",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Conversation History"
)
@cache(expire=60)  # Cache for 1 minute
async def get_conversation(conversation_id: str, token: str = Depends(oauth2_scheme)):
    """Retrieve chatbot conversation history and context."""
    async with track_operation("api/v1/chatbot/conversation", "Get Conversation", conversation_id=conversation_id):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        conversation = await chatbot_service.get_conversation(user.id, conversation_id)
        if not conversation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

        return conversation

# 📌 Create a New Conversation
@router.post(
    "/conversations",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Create a New Conversation"
)
async def create_conversation(
    initial_context: Optional[Dict[str, Any]] = Query(None, description="Initial context for the conversation"),
    token: str = Depends(oauth2_scheme)
):
    """Create a new chatbot conversation for the user."""
    async with track_operation("api/v1/chatbot/conversations", "Create Conversation"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        return await chatbot_service.create_conversation(user.id, initial_context or {})

# 📌 Submit Feedback for a Chat Message
@router.post(
    "/{conversation_id}/feedback",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Submit Feedback"
)
async def submit_feedback(
    conversation_id: str,
    message_id: str,
    feedback: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """Submit feedback for a chatbot message."""
    async with track_operation("api/v1/chatbot/feedback", "Submit Feedback", conversation_id=conversation_id, message_id=message_id):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        await chatbot_service.submit_feedback(user.id, conversation_id, message_id, feedback)
        return {"status": "success", "message": "Feedback submitted successfully"}

# 📌 Delete a Conversation
@router.delete(
    "/{conversation_id}",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))],
    summary="Delete a Conversation"
)
async def delete_conversation(conversation_id: str, token: str = Depends(oauth2_scheme)):
    """Delete a chatbot conversation and its associated data."""
    async with track_operation("api/v1/chatbot/delete", "Delete Conversation", conversation_id=conversation_id):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication credentials")

        success = await chatbot_service.delete_conversation(user.id, conversation_id)
        if not success:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

        return {"status": "success", "message": "Conversation deleted successfully"}

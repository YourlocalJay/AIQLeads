from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache.decorator import cache
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator, constr
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

# 📌 Base Models
class Message(BaseModel):
    content: constr(min_length=1, max_length=2000)
    role: str = Field("user", regex="^(user|assistant|system)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("content")
    def content_not_empty(cls, v):
        if v.strip() == "":
            raise ValueError("Message content cannot be empty")
        return v.strip()

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    messages: List[Message] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("messages")
    def messages_not_too_long(cls, v):
        if len(v) > 100:  # Limit conversation length
            raise ValueError("Conversation exceeds maximum length")
        return v

class ChatResponse(BaseModel):
    message: Message
    suggested_actions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0, le=1)
    requires_human: bool = False
    follow_up_questions: List[str] = Field(default_factory=list)
    response_time: float = Field(..., description="Response time in seconds")

class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str = Field(..., regex="^(helpful|unclear|incorrect|other)$")
    comment: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)

# 📌 Helper Functions
@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Context manager for operation tracking"""
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
        logger.error(f"Operation failed: {operation_name}", exc_info=True)
        raise

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token"""
    user = await user_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user.id

async def verify_conversation_access(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id)
) -> Tuple[str, Conversation]:
    """Verify user's access to conversation and return conversation"""
    conversation = await chatbot_service.get_conversation(user_id, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return user_id, conversation

# 📌 API Endpoints
@router.post(
    "/{conversation_id}/message",
    response_model=ChatResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=60))],
    summary="Send Message to Chatbot"
)
async def send_message(
    conversation_id: str,
    message: Message,
    background_tasks: BackgroundTasks,
    user_data: Tuple[str, Conversation] = Depends(verify_conversation_access)
):
    """Send a message to the chatbot and get AI-powered response"""
    user_id, conversation = user_data
    
    try:
        start_time = datetime.utcnow()
        response = await chatbot_service.process_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message
        )
        response_time = (datetime.utcnow() - start_time).total_seconds()
        response.response_time = response_time

        # Schedule background tasks
        background_tasks.add_task(
            chatbot_service.log_interaction,
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            response=response,
            metadata={
                "response_time": response_time,
                "confidence": response.confidence_score
            }
        )

        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.get(
    "/{conversation_id}",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Get Conversation History"
)
@cache(expire=60)
async def get_conversation(
    user_data: Tuple[str, Conversation] = Depends(verify_conversation_access)
):
    """Retrieve conversation history and context"""
    _, conversation = user_data
    return conversation

@router.post(
    "/conversations",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Create New Conversation"
)
async def create_conversation(
    initial_context: Optional[Dict[str, Any]] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new conversation with optional initial context"""
    try:
        return await chatbot_service.create_conversation(
            user_id=user_id,
            initial_context=initial_context or {}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )

@router.get(
    "/conversations",
    response_model=List[Conversation],
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="List Recent Conversations"
)
@cache(expire=300)
async def list_conversations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id)
):
    """List recent conversations for the user"""
    try:
        return await chatbot_service.list_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )

@router.post(
    "/{conversation_id}/feedback",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))],
    summary="Submit Feedback"
)
async def submit_feedback(
    conversation_id: str,
    message_id: str = Query(..., description="ID of the message being rated"),
    feedback: FeedbackRequest,
    user_data: Tuple[str, Conversation] = Depends(verify_conversation_access)
):
    """Submit feedback for a chatbot message"""
    user_id, _ = user_data
    
    try:
        await chatbot_service.submit_feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            feedback=feedback.dict()
        )
        return {"status": "success", "message": "Feedback submitted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@router.delete(
    "/{conversation_id}",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))],
    summary="Delete Conversation"
)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a conversation and its associated data"""
    try:
        success = await chatbot_service.delete_conversation(user_id, conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"status": "success", "message": "Conversation deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )

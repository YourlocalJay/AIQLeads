from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
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

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])

# Initialize services
chatbot_service = ChatbotService()
user_service = UserService()
tracker = ProjectTracker()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Message(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    role: str = Field("user", regex="^(user|assistant|system)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "content": "Tell me about lead XYZ's engagement history",
                "role": "user",
                "timestamp": "2025-02-05T14:30:00Z",
                "metadata": {
                    "lead_id": "lead_xyz",
                    "context": "engagement_history"
                }
            }
        }

class Conversation(BaseModel):
    id: str
    messages: List[Message]
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    message: Message
    suggested_actions: List[str] = []
    confidence_score: float = Field(..., ge=0, le=1)
    requires_human: bool = False
    follow_up_questions: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "message": {
                    "content": "Lead XYZ has shown increasing engagement...",
                    "role": "assistant",
                    "timestamp": "2025-02-05T14:30:05Z",
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
        }

@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Context manager for tracking operations and logging"""
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

@router.post("/{conversation_id}/message",
    response_model=ChatResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=60))])
async def send_message(
    conversation_id: str,
    message: Message,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme)
):
    """
    Send a message to the AI chatbot and get a response.
    """
    async with track_operation(
        "api/v1/chatbot/message",
        "Process Chat Message",
        conversation_id=conversation_id
    ):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Process message and get response
        response = await chatbot_service.process_message(
            user_id=user.id,
            conversation_id=conversation_id,
            message=message
        )
        
        # Schedule background tasks (e.g., update analytics, log interaction)
        background_tasks.add_task(
            chatbot_service.log_interaction,
            user_id=user.id,
            conversation_id=conversation_id,
            message=message,
            response=response
        )
        
        return response

@router.get("/{conversation_id}",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=60)  # Cache for 1 minute
async def get_conversation(
    conversation_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Retrieve conversation history and context.
    """
    async with track_operation(
        "api/v1/chatbot/conversation",
        "Get Conversation",
        conversation_id=conversation_id
    ):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        conversation = await chatbot_service.get_conversation(
            user_id=user.id,
            conversation_id=conversation_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation

@router.post("/conversations",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def create_conversation(
    initial_context: Optional[Dict[str, Any]] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Create a new conversation with optional initial context.
    """
    async with track_operation("api/v1/chatbot/conversations", "Create Conversation"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        conversation = await chatbot_service.create_conversation(
            user_id=user.id,
            initial_context=initial_context or {}
        )
        return conversation

@router.get("/conversations",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)  # Cache for 5 minutes
async def list_conversations(
    token: str = Depends(oauth2_scheme),
    limit: int = 10,
    offset: int = 0
):
    """
    List recent conversations for the user.
    """
    async with track_operation("api/v1/chatbot/conversations", "List Conversations"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        conversations = await chatbot_service.list_conversations(
            user_id=user.id,
            limit=limit,
            offset=offset
        )
        return conversations

@router.post("/{conversation_id}/context",
    response_model=Conversation,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def update_conversation_context(
    conversation_id: str,
    context_updates: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """
    Update the context for an existing conversation.
    """
    async with track_operation(
        "api/v1/chatbot/context",
        "Update Context",
        conversation_id=conversation_id
    ):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        conversation = await chatbot_service.update_context(
            user_id=user.id,
            conversation_id=conversation_id,
            context_updates=context_updates
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation

@router.post("/{conversation_id}/feedback",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def submit_feedback(
    conversation_id: str,
    message_id: str,
    feedback: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """
    Submit feedback for a specific message in a conversation.
    """
    async with track_operation(
        "api/v1/chatbot/feedback",
        "Submit Feedback",
        conversation_id=conversation_id,
        message_id=message_id
    ):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        await chatbot_service.submit_feedback(
            user_id=user.id,
            conversation_id=conversation_id,
            message_id=message_id,
            feedback=feedback
        )
        return {"status": "success", "message": "Feedback submitted successfully"}

@router.delete("/{conversation_id}",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def delete_conversation(
    conversation_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Delete a conversation and its associated data.
    """
    async with track_operation(
        "api/v1/chatbot/delete",
        "Delete Conversation",
        conversation_id=conversation_id
    ):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        success = await chatbot_service.delete_conversation(
            user_id=user.id,
            conversation_id=conversation_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"status": "success", "message": "Conversation deleted successfully"}

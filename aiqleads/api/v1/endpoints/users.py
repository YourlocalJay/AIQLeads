from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_cache.decorator import cache
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from aiqleads.models.user_model import User, UserCreate, UserUpdate
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Initialize services
user_service = UserService()
tracker = ProjectTracker()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: str
    scopes: List[str] = []

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    credits_balance: float
    is_active: bool
    last_login: Optional[datetime]
    subscription_tier: str
    features_enabled: List[str]

    class Config:
        schema_extra = {
            "example": {
                "id": "user_123",
                "email": "user@example.com",
                "full_name": "John Doe",
                "credits_balance": 1000.0,
                "is_active": True,
                "last_login": "2025-02-05T14:30:00Z",
                "subscription_tier": "professional",
                "features_enabled": ["lead_scoring", "market_analysis", "chatbot"]
            }
        }

class CreditTransaction(BaseModel):
    amount: float = Field(..., gt=0, description="Amount of credits to add or subtract")
    description: str = Field(..., min_length=3, max_length=200)
    transaction_type: str = Field(..., regex="^(add|subtract)$")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return access token.
    """
    async with track_operation("api/v1/users/token", "User Authentication", username=form_data.username):
        user = await user_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = user_service.create_access_token(
            data={"sub": user.email, "scopes": user.scopes}
        )
        refresh_token = user_service.create_refresh_token(
            data={"sub": user.email}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600  # 1 hour
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Get new access token using refresh token.
    """
    async with track_operation("api/v1/users/refresh", "Token Refresh"):
        token_data = user_service.validate_refresh_token(refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        new_access_token = user_service.create_access_token(
            data={"sub": token_data.username, "scopes": token_data.scopes}
        )
        
        return Token(
            access_token=new_access_token,
            expires_in=3600
        )

@router.post("/register", response_model=UserResponse, 
    dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def register_user(user_data: UserCreate):
    """
    Register a new user account.
    """
    async with track_operation("api/v1/users/register", "User Registration", email=user_data.email):
        if await user_service.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user = await user_service.create_user(user_data)
        return user

@router.get("/me", response_model=UserResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=60))])
@cache(expire=60)  # Cache for 1 minute
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current authenticated user's details.
    """
    async with track_operation("api/v1/users/me", "Get Current User"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user

@router.put("/me", response_model=UserResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def update_user(
    update_data: UserUpdate,
    token: str = Depends(oauth2_scheme)
):
    """
    Update current user's information.
    """
    async with track_operation("api/v1/users/me", "Update User"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        updated_user = await user_service.update_user(user.id, update_data)
        return updated_user

@router.post("/credits", response_model=UserResponse,
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def manage_credits(
    transaction: CreditTransaction,
    token: str = Depends(oauth2_scheme)
):
    """
    Add or subtract credits from user's account.
    """
    async with track_operation(
        "api/v1/users/credits", 
        f"Credit {transaction.transaction_type}",
        amount=transaction.amount
    ):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        if transaction.transaction_type == "subtract" and user.credits_balance < transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient credits"
            )
        
        updated_user = await user_service.update_credits(
            user.id,
            transaction.amount,
            transaction.transaction_type,
            transaction.description
        )
        return updated_user

@router.get("/credits/history",
    dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)  # Cache for 5 minutes
async def get_credit_history(
    token: str = Depends(oauth2_scheme),
    limit: int = 10,
    offset: int = 0
):
    """
    Get user's credit transaction history.
    """
    async with track_operation("api/v1/users/credits/history", "Get Credit History"):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        history = await user_service.get_credit_history(user.id, limit, offset)
        return history

@router.post("/subscription/upgrade",
    dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def upgrade_subscription(
    tier: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Upgrade user's subscription tier.
    """
    async with track_operation("api/v1/users/subscription", "Subscription Upgrade", tier=tier):
        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        updated_user = await user_service.upgrade_subscription(user.id, tier)
        return updated_user

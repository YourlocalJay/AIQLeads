from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_cache.decorator import cache
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
from functools import lru_cache
from aiqleads.core.security import create_access_token, verify_token
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from aiqleads.models.user_model import User, UserCreate, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Singleton instances
user_service = UserService()
tracker = ProjectTracker()

# 📌 Context Manager for Operation Tracking
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Tracks operation status in `ProjectTracker`."""
    try:
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

# 📌 Token Model
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

# 📌 User Response Model
class UserResponse(User):
    id: str
    credits_balance: float
    subscription_tier: str
    features_enabled: List[str] = []

# 📌 Credit Transaction Model
class CreditTransaction(BaseModel):
    amount: float = Field(..., gt=0, description="Amount of credits to add or subtract")
    description: str = Field(..., min_length=3, max_length=200)
    transaction_type: str = Field(..., regex="^(add|subtract)$")

# 📌 OAuth2 Dependency
@lru_cache()
def get_oauth_token():
    return OAuth2PasswordBearer(tokenUrl="token")

oauth2_scheme = get_oauth_token()

def verify_authenticated(token: str = Depends(oauth2_scheme)):
    """Verifies authentication token and extracts user ID."""
    try:
        payload = verify_token(token)
        if not payload.get('id'):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
        return payload['id']
    except:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

# 📌 User Authentication - Token Generation
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates user and returns an access token."""
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(days=7))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (await verify_token(access_token))['exp'],
        "refresh_token": refresh_token
    }

# 📌 Token Refresh
@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refreshes access token using a valid refresh token."""
    new_token = await user_service.refresh_token(refresh_token)
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": (await verify_token(new_token))['exp']
    }

# 📌 User Registration
@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Registers a new user and returns user details."""
    if await user_service.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await user_service.create_user(user_data)
    return UserResponse.from_orm(new_user)

# 📌 Get Current User
@router.get("/me", response_model=UserResponse)
@cache(expire=60)
async def get_current_user(user_id: str = Depends(verify_authenticated)):
    """Retrieves the authenticated user's profile."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)

# 📌 Update User Profile
@router.put("/me", response_model=UserResponse)
async def update_user(update_data: UserUpdate, user_id: str = Depends(verify_authenticated)):
    """Updates the user's profile details."""
    updated_user = await user_service.update_user(user_id, update_data)
    return UserResponse.from_orm(updated_user)

# 📌 Manage User Credits
@router.post("/credits", response_model=UserResponse)
async def manage_credits(transaction: CreditTransaction, user_id: str = Depends(verify_authenticated)):
    """Adds or subtracts credits from user account."""
    user = await user_service.update_credits(user_id, transaction.amount, transaction.transaction_type, transaction.description)
    return UserResponse.from_orm(user)

# 📌 Get Credit Transaction History
@router.get("/credits/history", dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)
async def get_credit_history(user_id: str = Depends(verify_authenticated), limit: int = 10, offset: int = 0):
    """Fetches credit transaction history for the user."""
    history = await user_service.get_credit_history(user_id, limit, offset)
    return {"transactions": history}

# 📌 Upgrade User Subscription
@router.post("/subscription/upgrade", dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def upgrade_subscription(subscription_tier: str, user_id: str = Depends(verify_authenticated)):
    """Upgrades user subscription tier."""
    updated_user = await user_service.upgrade_subscription(user_id, subscription_tier)
    return UserResponse.from_orm(updated_user)

# 📌 Cancel User Subscription
@router.post("/subscription/cancel", dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def cancel_subscription(user_id: str = Depends(verify_authenticated)):
    """Cancels user's active subscription."""
    updated_user = await user_service.cancel_subscription(user_id)
    return UserResponse.from_orm(updated_user)

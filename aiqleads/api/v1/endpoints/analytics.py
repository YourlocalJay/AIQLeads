from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2PasswordRequestForm
from fastapi_cache.decorator import cache
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator, SecretStr
from datetime import datetime, timedelta
from aiqleads.core.project_tracking import ProjectTracker
from aiqleads.services.user_service import UserService
from aiqleads.middlewares.rate_limiter import RateLimiter
from aiqleads.utils.logging import logger
from aiqleads.models.user_model import User, UserCreate, UserUpdate, UserRoles
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from jose import JWTError
from passlib.context import CryptContext
from typing import Annotated
import uuid

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "user:read": "Read user information",
        "user:write": "Modify user information",
        "admin": "Admin privileges"
    }
)

# Initialize services
user_service = UserService()
tracker = ProjectTracker()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    credits_balance: float = Field(..., ge=0)
    is_active: bool
    last_login: Optional[datetime]
    subscription_tier: Optional[str]
    features_enabled: List[str]
    roles: List[str]

    @validator("credits_balance")
    def validate_credits(cls, value):
        if value < 0:
            raise ValueError("Credits balance cannot be negative")
        return value

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
                "features_enabled": ["lead_scoring", "market_analysis", "chatbot"],
                "roles": ["user"]
            }
        }

class CreditTransaction(BaseModel):
    amount: float = Field(..., gt=0, description="Amount of credits to add or subtract")
    description: str = Field(..., min_length=3, max_length=200)
    transaction_type: str = Field(..., regex="^(add|subtract)$")

class PasswordUpdate(BaseModel):
    current_password: SecretStr
    new_password: SecretStr

    @validator("new_password")
    def validate_password_complexity(cls, v):
        if len(v.get_secret_value()) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    try:
        payload = user_service.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await user_service.get_user_by_email(payload.get("sub"))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or deleted",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if security_scopes.scopes:
            for scope in security_scopes.scopes:
                if scope not in user.roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required scope: {scope}",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        return user
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@asynccontextmanager
async def track_operation(component_id: str, operation_name: str, **kwargs):
    """Enhanced operation tracking with error classification"""
    try:
        yield
        tracker.log_operation(
            component_id=component_id,
            operation=operation_name,
            status="success",
            details=kwargs
        )
    except HTTPException as he:
        tracker.log_operation(
            component_id=component_id,
            operation=operation_name,
            status="client_error",
            details={**kwargs, "error": he.detail}
        )
        raise
    except Exception as e:
        tracker.log_operation(
            component_id=component_id,
            operation=operation_name,
            status="server_error",
            details={**kwargs, "error": str(e)}
        )
        logger.error(f"Operation failed: {operation_name}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with track_operation("users/auth", "User Authentication", username=form_data.username):
        user = await user_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = user_service.create_access_token(
            data={"sub": user.email, "scopes": user.roles}
        )
        refresh_token = user_service.create_refresh_token(
            data={"sub": user.email}
        )

        await user_service.update_last_login(user.id)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=user_service.access_token_expire_minutes * 60
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    async with track_operation("users/auth", "Token Refresh"):
        new_access_token = await user_service.refresh_access_token(refresh_token)
        return Token(
            access_token=new_access_token,
            expires_in=user_service.access_token_expire_minutes * 60
        )

@router.post("/register", response_model=UserResponse, 
            dependencies=[Depends(RateLimiter(requests_per_minute=5))])
async def register_user(user_data: UserCreate):
    async with track_operation("users/registration", "User Registration", email=user_data.email):
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        new_user = await user_service.create_user(user_data)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=UserResponse(**new_user.dict()).dict()
        )

@router.get("/me", response_model=UserResponse,
           dependencies=[Depends(RateLimiter(requests_per_minute=60))])
@cache(expire=60)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return UserResponse(**current_user.dict())

@router.put("/me", response_model=UserResponse,
           dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def update_user_profile(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    async with track_operation("users/profile", "Update Profile", user_id=current_user.id):
        updated_user = await user_service.update_user(current_user.id, update_data)
        return UserResponse(**updated_user.dict())

@router.post("/me/password", response_model=UserResponse,
            dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def change_password(
    password_data: PasswordUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    async with track_operation("users/password", "Change Password", user_id=current_user.id):
        if not user_service.verify_password(
            password_data.current_password.get_secret_value(),
            current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        updated_user = await user_service.change_password(
            current_user.id,
            password_data.new_password.get_secret_value()
        )
        return UserResponse(**updated_user.dict())

@router.post("/credits", response_model=UserResponse,
           dependencies=[Depends(RateLimiter(requests_per_minute=30))])
async def manage_credits(
    transaction: CreditTransaction,
    current_user: Annotated[User, Depends(get_current_user)]
):
    async with track_operation("users/credits", "Credit Management", user_id=current_user.id):
        if transaction.transaction_type == "subtract" and current_user.credits_balance < transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient credits"
            )
        
        updated_user = await user_service.update_credits(
            current_user.id,
            transaction.amount,
            transaction.transaction_type,
            transaction.description
        )
        return UserResponse(**updated_user.dict())

@router.get("/credits/history", dependencies=[Depends(RateLimiter(requests_per_minute=30))])
@cache(expire=300)
async def get_credit_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 10,
    offset: int = 0
):
    async with track_operation("users/credits/history", "Credit History", user_id=current_user.id):
        history = await user_service.get_credit_history(current_user.id, limit, offset)
        return {
            "transactions": [t.dict() for t in history],
            "total": await user_service.get_credit_history_count(current_user.id),
            "limit": limit,
            "offset": offset
        }

@router.post("/subscription/upgrade", response_model=UserResponse,
            dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def upgrade_subscription(
    tier: str,
    current_user: Annotated[User, Security(get_current_user, scopes=["user:write"])]
):
    async with track_operation("users/subscription", "Subscription Upgrade", user_id=current_user.id):
        if current_user.subscription_tier == tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Already subscribed to {tier} tier"
            )
        
        updated_user = await user_service.upgrade_subscription(current_user.id, tier)
        return UserResponse(**updated_user.dict())

@router.post("/subscription/cancel", response_model=UserResponse,
            dependencies=[Depends(RateLimiter(requests_per_minute=10))])
async def cancel_subscription(
    current_user: Annotated[User, Security(get_current_user, scopes=["user:write"])]
):
    async with track_operation("users/subscription", "Subscription Cancel", user_id=current_user.id):
        if not current_user.subscription_tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription to cancel"
            )
        
        updated_user = await user_service.cancel_subscription(current_user.id)
        return UserResponse(**updated_user.dict())

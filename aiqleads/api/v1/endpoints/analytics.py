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

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = user_service.create_access_token(data={"sub": user.email, "scopes": user.roles})
    refresh_token = user_service.create_refresh_token(data={"sub": user.email})
    await user_service.update_last_login(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token, expires_in=user_service.access_token_expire_minutes * 60)

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(requests_per_minute=5))])
async def register_user(user_data: UserCreate):
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    new_user = await user_service.create_user(user_data)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=UserResponse(**new_user.dict()).dict())

@router.get("/me", response_model=UserResponse, dependencies=[Depends(RateLimiter(requests_per_minute=60))])
@cache(expire=60)
async def get_current_user_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return UserResponse(**current_user.dict())

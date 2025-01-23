from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import re

# Constants
AVAILABLE_MARKETS = ["Las Vegas", "Dallas/Ft. Worth", "Austin", "Phoenix"]

class NotificationPreferences(BaseModel):
    """Schema for user notification preferences."""
    email: bool = True
    sms: bool = False
    lead_alerts: bool = True
    market_insights: bool = True

class UserBase(BaseModel):
    """Base user schema with common fields and validations."""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    preferred_market: Optional[str] = Field(
        None,
        description="Primary market of interest"
    )
    notification_preferences: NotificationPreferences = Field(
        default_factory=NotificationPreferences
    )

    @validator('phone')
    def validate_phone(cls, v):
        """Validate and normalize phone number format."""
        if v is None:
            return v
        # Remove spaces but preserve hyphens for formatting
        v = v.replace(" ", "")
        # Validate format: +X-XXX-XXX-XXXX or +XXXXXXXXXXXX
        if not (re.match(r'^\+\d(-\d{3})*(-\d{4})?$', v) or re.match(r'^\+\d+$', v)):
            raise ValueError('Invalid phone format. Expected: +X-XXX-XXX-XXXX or +XXXXXXXXXXXX')
        return v

    @validator('preferred_market')
    def validate_market_availability(cls, v):
        """Validate that the selected market is supported."""
        if v and v not in AVAILABLE_MARKETS:
            raise ValueError(f"Market {v} not currently supported. Available markets: {', '.join(AVAILABLE_MARKETS)}")
        return v

class UserCreate(UserBase):
    """Schema for user creation with password validation."""
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password_complexity(cls, v):
        """
        Validate password meets complexity requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character (@$!%*?&#)
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit.')
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError('Password must contain at least one special character (e.g., @$!%*?&#).')
        return v

class UserUpdate(BaseModel):
    """Schema for user updates allowing partial updates."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    preferred_market: Optional[str] = None
    notification_preferences: Optional[NotificationPreferences] = None
    is_active: Optional[bool] = Field(default=None)
    is_verified: Optional[bool] = Field(default=None)

    @validator('password')
    def validate_password_if_provided(cls, v):
        """Validate password only if it's being updated."""
        if v is not None:
            UserCreate.validate_password_complexity(v)
        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Reuse phone validation from UserBase."""
        return UserBase.validate_phone(v) if v else v

    @validator('preferred_market')
    def validate_market_if_provided(cls, v):
        """Validate market only if it's being updated."""
        return UserBase.validate_market_availability(v) if v else v

class UserInDB(UserBase):
    """Schema for user data as stored in the database."""
    id: int
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime
    last_login_attempt: Optional[datetime] = None
    failed_login_attempts: int = Field(default=0)
    account_locked_until: Optional[datetime] = None

    class Config:
        """Pydantic configuration for datetime handling."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserResponse(UserInDB):
    """Schema for user data in API responses."""
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    total_leads_purchased: Optional[int] = Field(default=0)
    available_credits: Optional[int] = Field(default=0)
    authorized_markets: List[str] = Field(default_factory=list)

    class Config:
        """Configure schema for response serialization."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Example Corp",
                "phone": "+1-234-567-8900",
                "preferred_market": "Las Vegas",
                "notification_preferences": {
                    "email": True,
                    "sms": False,
                    "lead_alerts": True,
                    "market_insights": True
                },
                "subscription_tier": "Professional",
                "subscription_status": "active",
                "total_leads_purchased": 150,
                "available_credits": 1000,
                "authorized_markets": ["Las Vegas", "Phoenix"],
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:30:00"
            }
        }
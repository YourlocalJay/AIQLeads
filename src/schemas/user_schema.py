from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields and validations."""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)

    @validator('phone')
    def validate_phone(cls, v):
        """Validate and normalize phone number format."""
        if v is None:
            return v
        v = v.replace(" ", "").replace("-", "")
        if not re.match(r'^\+\d+$', v):
            raise ValueError('Invalid phone number format. Must start with "+" followed by digits.')
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


class UserInDB(UserBase):
    """Schema for user data as stored in the database."""
    id: int
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration for datetime handling."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserResponse(UserInDB):
    """Schema for user data in API responses."""
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
                "phone": "+1234567890",
                "is_active": True,
                "is_verified": False,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:30:00"
            }
        }

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, constr, validator
import re


class UserBase(BaseModel):
    """Base schema with common user attributes"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is None:
            return v
        phone_pattern = re.compile(r'^\+\d{1,3}[-]?\d{3}[-]?\d{3}[-]?\d{4}$')
        if not phone_pattern.match(v):
            raise ValueError('Invalid phone number format. Expected format: +1-234-567-8900')
        return v


class UserCreate(UserBase):
    """Schema for user creation with password validation"""
    password: str
    confirm_password: str

    @validator('password')
    def validate_password(cls, v):
        """Enforce password policy"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError('Password must contain at least one special character (@$!%*?&#)')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure confirm_password matches password"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates allowing partial updates"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one number')
            if not re.search(r'[@$!%*?&#]', v):
                raise ValueError('Password must contain at least one special character (@$!%*?&#)')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            phone_pattern = re.compile(r'^\+\d{1,3}[-]?\d{3}[-]?\d{3}[-]?\d{4}$')
            if not phone_pattern.match(v):
                raise ValueError('Invalid phone number format. Expected format: +1-234-567-8900')
        return v


class UserInDB(UserBase):
    """Schema for user data as stored in database"""
    id: int
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserResponse(UserInDB):
    """Schema for user data in API responses"""
    pass

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Example Corp",
                "phone": "+1-234-567-8900",
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-21T00:00:00",
                "updated_at": "2024-01-21T00:00:00"
            }
        }
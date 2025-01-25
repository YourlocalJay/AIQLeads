from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Check for valid phone format: +{country_code}-{area_code}-{local_number}
        phone_pattern = r'^\+(?!\+)[1-9]\d{0,2}[-\s]?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}$'
        if not re.match(phone_pattern, v):
            raise ValueError('Invalid phone number format. Must include country code and follow format: +X-XXX-XXX-XXXX')
        return v

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError('Password must contain at least one special character (@$!%*?&#)')
        return v

class UserUpdate(BaseModel):
    """Schema for user updates"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if v is None:
            return v
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
        if v is None:
            return v
        phone_pattern = r'^\+(?!\+)[1-9]\d{0,2}[-\s]?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}$'
        if not re.match(phone_pattern, v):
            raise ValueError('Invalid phone number format. Must include country code and follow format: +X-XXX-XXX-XXXX')
        return v

class UserInDB(UserBase):
    """Schema for user database representation"""
    id: int
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        
    @validator('created_at', 'updated_at')
    def ensure_timezone(cls, v):
        if v and v.tzinfo is None:
            return v.replace(tzinfo=None)  # Ensure UTC for naive datetimes
        return v

class UserResponse(UserInDB):
    """Schema for user API responses"""
    pass
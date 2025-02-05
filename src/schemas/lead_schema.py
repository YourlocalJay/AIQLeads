from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl, constr, validator, Field, confloat
from src.models.lead_model import LeadStatus


class CoordinatePoint(BaseModel):
    """Schema for geographical coordinates"""

    longitude: confloat(ge=-180, le=180)
    latitude: confloat(ge=-90, le=90)
    accuracy: Optional[float] = Field(None, ge=0, le=1)

    @validator("accuracy")
    def validate_accuracy(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Accuracy must be between 0 and 1")
        return v


class LeadBase(BaseModel):
    """Base schema with common lead attributes"""

    company_name: constr(min_length=1, max_length=200)
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = Field(None, ge=0)
    annual_revenue: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator("phone")
    def validate_phone(cls, v):
        if v is not None:
            import re

            phone_pattern = re.compile(r"^\+\d{1,3}[-]?\d{3}[-]?\d{3}[-]?\d{4}$")
            if not phone_pattern.match(v):
                raise ValueError(
                    "Invalid phone number format. Expected format: +1-234-567-8900"
                )
        return v


class LeadCreate(LeadBase):
    """Schema for creating new leads"""

    owner_id: int = Field(..., gt=0)
    location: Optional[CoordinatePoint] = None
    status: LeadStatus = Field(default=LeadStatus.NEW)


class LeadUpdate(BaseModel):
    """Schema for updating leads"""

    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    location: Optional[CoordinatePoint] = None
    status: Optional[LeadStatus] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class LeadInDB(LeadBase):
    """Schema for lead data as stored in database"""

    id: int
    owner_id: int
    status: LeadStatus
    score: Optional[float] = Field(None, ge=0, le=1)
    is_active: bool = True
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_contact: Optional[datetime] = None

    class Config:
        orm_mode = True


class LeadResponse(LeadInDB):
    """Schema for lead data in API responses"""

    distance: Optional[float] = None  # Distance in meters when requested

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "owner_id": 1,
                "company_name": "Example Corp",
                "contact_name": "John Doe",
                "contact_title": "CEO",
                "email": "john@example.com",
                "phone": "+1-234-567-8900",
                "website": "https://example.com",
                "street_address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA",
                "location": "POINT(-73.935242 40.730610)",
                "industry": "Technology",
                "employee_count": 100,
                "annual_revenue": 1000000.0,
                "status": "qualified",
                "score": 0.85,
                "is_active": True,
                "metadata": {"source": "LinkedIn", "campaign_id": "Q1-2024"},
                "notes": "Interested in enterprise solution",
                "created_at": "2024-01-21T00:00:00",
                "updated_at": "2024-01-21T00:00:00",
                "last_contact": "2024-01-21T00:00:00",
                "distance": 1234.56,
            }
        }

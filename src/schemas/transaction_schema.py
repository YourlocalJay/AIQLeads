from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator
import pycountry

from ..models.transaction_model import TransactionStatus, TransactionType


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    user_id: int = Field(..., description="ID of the user making the transaction")
    amount: Decimal = Field(..., description="Transaction amount", gt=Decimal('0'))
    currency: str = Field(..., description="Three-letter ISO currency code", min_length=3, max_length=3)
    type: TransactionType = Field(..., description="Type of transaction")
    reference_id: str = Field(..., description="Unique reference ID from payment processor", max_length=100, regex="^[A-Za-z0-9_-]+$")
    description: Optional[str] = Field(None, description="Transaction description", max_length=255)

    @validator("currency")
    def validate_currency(cls, v):
        """Validate currency code against ISO standards using pycountry."""
        if not v.isalpha():
            raise ValueError("Currency code must contain only letters")
        
        currency = pycountry.currencies.get(alpha_3=v.upper())
        if not currency:
            raise ValueError(f"Invalid currency code: {v}")
            
        return v.upper()
    
    @validator("reference_id")
    def validate_reference_id(cls, v):
        """Validate reference ID format."""
        if not v.strip():
            raise ValueError("Reference ID cannot be empty")
        return v


class TransactionResponse(BaseModel):
    """Schema for returning transaction data."""
    id: int
    user_id: int
    amount: Decimal
    currency: str
    status: TransactionStatus
    type: TransactionType
    reference_id: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

    class Config:
        orm_mode = True
        
        
class TransactionUpdate(BaseModel):
    """Schema for updating transaction status."""
    status: TransactionStatus = Field(..., description="New transaction status")
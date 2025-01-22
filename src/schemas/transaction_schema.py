from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator

from ..models.transaction_model import TransactionStatus, TransactionType


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    user_id: int = Field(..., description="ID of the user making the transaction")
    amount: Decimal = Field(..., description="Transaction amount", gt=Decimal('0'))
    currency: str = Field(..., description="Three-letter currency code", min_length=3, max_length=3)
    type: TransactionType = Field(..., description="Type of transaction")
    reference_id: str = Field(..., description="Unique reference ID from payment processor", max_length=100)
    description: Optional[str] = Field(None, description="Transaction description", max_length=255)

    @validator("currency")
    def validate_currency(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency code must be a valid 3-letter code")
        return v.upper()


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

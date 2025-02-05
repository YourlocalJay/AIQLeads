from datetime import datetime
from pydantic import BaseModel, Field

from ..models.subscription_model import SubscriptionTier, SubscriptionStatus


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription."""

    user_id: int = Field(..., description="ID of the subscribing user")
    transaction_id: int = Field(..., description="ID of the related transaction")
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: datetime = Field(..., description="Subscription end date")
    auto_renew: bool = Field(
        default=True, description="Whether the subscription will auto-renew"
    )


class SubscriptionResponse(BaseModel):
    """Schema for returning subscription data."""

    id: int
    user_id: int
    transaction_id: int
    tier: SubscriptionTier
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

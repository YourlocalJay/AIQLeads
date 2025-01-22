from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class SubscriptionTier(PyEnum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(PyEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    tier = Column(Enum(SubscriptionTier), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.PENDING)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        now = datetime.utcnow()
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )
    
    def cancel_subscription(self) -> None:
        """Cancel subscription and disable auto-renewal."""
        self.auto_renew = False
        self.status = SubscriptionStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def renew_subscription(self, period_days: int = 30) -> None:
        """Renew subscription for another period."""
        if not self.auto_renew:
            raise ValueError("Auto-renewal is disabled for this subscription")
        self.start_date = self.end_date
        self.end_date = self.end_date + timedelta(days=period_days)
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

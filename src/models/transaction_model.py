from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class TransactionStatus(PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class TransactionType(PyEnum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    REFUND = "refund"

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    type = Column(Enum(TransactionType), nullable=False)
    reference_id = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def validate_amount(self) -> bool:
        """Validate transaction amount."""
        return self.amount > Decimal('0.00')
    
    def validate_currency(self) -> bool:
        """Validate currency code format."""
        import pycountry
        return pycountry.currencies.get(alpha_3=self.currency.upper()) is not None
    
    def update_status(self, new_status: TransactionStatus) -> None:
        """Update transaction status with validation."""
        valid_transitions = {
            TransactionStatus.PENDING: [TransactionStatus.COMPLETED, TransactionStatus.FAILED],
            TransactionStatus.COMPLETED: [TransactionStatus.REFUNDED],
            TransactionStatus.FAILED: [],
            TransactionStatus.REFUNDED: []
        }
        if new_status not in valid_transitions[self.status]:
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        self.status = new_status
        self.updated_at = datetime.utcnow()

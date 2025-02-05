from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base
import pycountry


class TransactionStatus(PyEnum):
    """Enum representing possible transaction statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class TransactionType(PyEnum):
    """Enum representing types of transactions."""

    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    REFUND = "refund"


class Transaction(Base):
    """Transaction model for handling financial transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(
        Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING
    )
    type = Column(Enum(TransactionType), nullable=False)
    reference_id = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    description = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="transactions")

    def __init__(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        type: TransactionType,
        reference_id: str,
        description: str = None,
    ):
        self.user_id = user_id
        self.amount = amount
        self.currency = currency.upper()
        self.type = type
        self.reference_id = reference_id
        self.description = description

        if not self.validate_currency():
            raise ValueError(f"Invalid currency code: {self.currency}")

    def validate_amount(self) -> bool:
        """Validate transaction amount is positive."""
        return self.amount > Decimal("0.00")

    def validate_currency(self) -> bool:
        """Validate currency code against ISO standards using pycountry."""
        if not self.currency or len(self.currency) != 3:
            return False
        return pycountry.currencies.get(alpha_3=self.currency.upper()) is not None

    def update_status(self, new_status: TransactionStatus) -> None:
        """Update transaction status with state transition validation."""
        valid_transitions = {
            TransactionStatus.PENDING: [
                TransactionStatus.COMPLETED,
                TransactionStatus.FAILED,
            ],
            TransactionStatus.COMPLETED: [TransactionStatus.REFUNDED],
            TransactionStatus.FAILED: [],
            TransactionStatus.REFUNDED: [],
        }

        if new_status not in valid_transitions[self.status]:
            raise ValueError(
                f"Invalid status transition from {self.status} to {new_status}"
            )

        self.status = new_status
        self.updated_at = datetime.utcnow()

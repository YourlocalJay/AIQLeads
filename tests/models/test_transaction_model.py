import pytest
from datetime import datetime
from decimal import Decimal
from src.models.transaction_model import Transaction, TransactionStatus, TransactionType

def test_transaction_creation():
    """Test successful creation of a transaction."""
    transaction = Transaction(
        user_id=1,
        amount=Decimal('99.99'),
        currency='USD',
        type=TransactionType.ONE_TIME,
        reference_id='ref123'
    )
    assert transaction.amount == Decimal('99.99')
    assert transaction.currency == 'USD'
    assert transaction.type == TransactionType.ONE_TIME
    assert transaction.status == TransactionStatus.PENDING


def test_invalid_currency_code():
    """Test invalid currency code raises a validation error."""
    with pytest.raises(ValueError):
        transaction = Transaction(
            user_id=1,
            amount=Decimal('50.00'),
            currency='INVALID',
            type=TransactionType.ONE_TIME,
            reference_id='ref123'
        )


def test_status_transition():
    """Test valid and invalid status transitions."""
    transaction = Transaction(
        user_id=1,
        amount=Decimal('50.00'),
        currency='USD',
        type=TransactionType.ONE_TIME,
        reference_id='ref123'
    )

    # Valid transition
    transaction.update_status(TransactionStatus.COMPLETED)
    assert transaction.status == TransactionStatus.COMPLETED

    # Invalid transition
    with pytest.raises(ValueError):
        transaction.update_status(TransactionStatus.PENDING)

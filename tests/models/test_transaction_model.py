import pytest
from decimal import Decimal

from src.models.transaction_model import Transaction, TransactionStatus, TransactionType


def test_transaction_creation():
    """Test successful creation of a transaction."""
    transaction = Transaction(
        user_id=1,
        amount=Decimal("99.99"),
        currency="USD",
        type=TransactionType.ONE_TIME,
        reference_id="ref123",
    )

    assert transaction.amount == Decimal("99.99")
    assert transaction.currency == "USD"
    assert transaction.type == TransactionType.ONE_TIME
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.validate_amount() is True
    assert transaction.validate_currency() is True


def test_invalid_currency_code():
    """Test invalid currency code raises a validation error."""
    invalid_currencies = ["USDD", "US", "XXX", "123", "US!"]

    for currency in invalid_currencies:
        with pytest.raises(ValueError, match="Invalid currency code"):
            Transaction(
                user_id=1,
                amount=Decimal("50.00"),
                currency=currency,
                type=TransactionType.ONE_TIME,
                reference_id="ref123",
            )


def test_valid_currency_codes():
    """Test various valid ISO currency codes."""
    valid_currencies = ["USD", "EUR", "GBP", "JPY", "AUD"]

    for currency in valid_currencies:
        transaction = Transaction(
            user_id=1,
            amount=Decimal("50.00"),
            currency=currency,
            type=TransactionType.ONE_TIME,
            reference_id="ref123",
        )
        assert transaction.currency == currency
        assert transaction.validate_currency() is True


def test_status_transition():
    """Test valid and invalid status transitions."""
    transaction = Transaction(
        user_id=1,
        amount=Decimal("50.00"),
        currency="USD",
        type=TransactionType.ONE_TIME,
        reference_id="ref123",
    )

    # Test valid transitions
    valid_transitions = [
        (TransactionStatus.PENDING, TransactionStatus.COMPLETED),
        (TransactionStatus.COMPLETED, TransactionStatus.REFUNDED),
    ]

    for current, next_status in valid_transitions:
        transaction.status = current
        transaction.update_status(next_status)
        assert transaction.status == next_status

    # Test invalid transitions
    invalid_transitions = [
        (TransactionStatus.PENDING, TransactionStatus.REFUNDED),
        (TransactionStatus.COMPLETED, TransactionStatus.PENDING),
        (TransactionStatus.FAILED, TransactionStatus.COMPLETED),
        (TransactionStatus.REFUNDED, TransactionStatus.COMPLETED),
    ]

    for current, next_status in invalid_transitions:
        transaction.status = current
        with pytest.raises(ValueError, match="Invalid status transition"):
            transaction.update_status(next_status)


def test_zero_amount():
    """Test zero amount is not allowed."""
    with pytest.raises(ValueError):
        Transaction(
            user_id=1,
            amount=Decimal("0.00"),
            currency="USD",
            type=TransactionType.ONE_TIME,
            reference_id="ref123",
        )


def test_negative_amount():
    """Test negative amount is not allowed."""
    with pytest.raises(ValueError):
        Transaction(
            user_id=1,
            amount=Decimal("-50.00"),
            currency="USD",
            type=TransactionType.ONE_TIME,
            reference_id="ref123",
        )

import pytest
from datetime import datetime, timedelta
from src.models.subscription_model import Subscription, SubscriptionTier, SubscriptionStatus

def test_subscription_creation():
    """Test successful creation of a subscription."""
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    subscription = Subscription(
        user_id=1,
        transaction_id=1,
        tier=SubscriptionTier.BASIC,
        start_date=start_date,
        end_date=end_date
    )
    assert subscription.tier == SubscriptionTier.BASIC
    assert subscription.status == SubscriptionStatus.PENDING
    assert subscription.is_active is False  # Not active until status changes


def test_subscription_cancellation():
    """Test cancelling a subscription."""
    subscription = Subscription(
        user_id=1,
        transaction_id=1,
        tier=SubscriptionTier.PREMIUM,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    subscription.cancel_subscription()
    assert subscription.status == SubscriptionStatus.CANCELLED
    assert subscription.auto_renew is False


def test_subscription_renewal():
    """Test renewing a subscription."""
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    subscription = Subscription(
        user_id=1,
        transaction_id=1,
        tier=SubscriptionTier.PREMIUM,
        start_date=start_date,
        end_date=end_date,
        auto_renew=True
    )
    subscription.renew_subscription(period_days=30)
    assert subscription.start_date == end_date
    assert subscription.end_date == end_date + timedelta(days=30)
    assert subscription.status == SubscriptionStatus.ACTIVE

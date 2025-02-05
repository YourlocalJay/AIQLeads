import pytest
from datetime import datetime, timedelta

from src.aggregator.components.rate_limiter import RateLimiter
from src.aggregator.exceptions import RateLimitExceeded


@pytest.fixture
def rate_limiter():
    return RateLimiter(default_rate_limit=10)


def test_rate_limiter_initialization():
    """Test rate limiter initialization"""
    limiter = RateLimiter(default_rate_limit=5)
    assert limiter.get_rate_limit("test.com") == 5


def test_can_make_request_success(rate_limiter):
    """Test successful request check"""
    assert rate_limiter.can_make_request("test.com") is True


def test_rate_limit_exceeded(rate_limiter):
    """Test rate limit exceeded"""
    # Make maximum allowed requests
    domain = "test.com"
    rate_limit = rate_limiter.get_rate_limit(domain)

    for _ in range(rate_limit):
        assert rate_limiter.can_make_request(domain) is True

    # Next request should fail
    with pytest.raises(RateLimitExceeded) as exc:
        rate_limiter.can_make_request(domain)
    assert domain in str(exc.value)
    assert "rate_limit" in exc.value.details


def test_rate_limit_window(rate_limiter):
    """Test rate limit time window"""
    domain = "test.com"

    # Set up requests just over 1 minute ago
    old_time = datetime.now() - timedelta(seconds=61)
    rate_limiter._request_timestamps[domain] = [old_time] * rate_limiter.get_rate_limit(
        domain
    )

    # New request should succeed because old timestamps are expired
    assert rate_limiter.can_make_request(domain) is True


def test_rate_limit_adjustment(rate_limiter):
    """Test rate limit adjustment"""
    domain = "test.com"
    initial_limit = rate_limiter.get_rate_limit(domain)

    # Record multiple errors
    for _ in range(6):
        rate_limiter.record_error(domain)

    # Rate limit should be reduced
    assert rate_limiter.get_rate_limit(domain) < initial_limit

    # Record success to gradually increase limit
    rate_limiter.record_success(domain)
    assert rate_limiter.get_rate_limit(domain) > 1


def test_adaptive_rate_limiting(rate_limiter):
    """Test adaptive rate limiting"""
    domain = "test.com"

    # Record 429 status
    rate_limiter.record_error(domain, status_code=429)
    reduced_limit = rate_limiter.get_rate_limit(domain)
    assert reduced_limit < 10

    # Record successful requests
    for _ in range(5):
        rate_limiter.record_success(domain)

    # Rate limit should gradually increase
    assert rate_limiter.get_rate_limit(domain) > reduced_limit


def test_domain_isolation(rate_limiter):
    """Test rate limits are isolated per domain"""
    domain1 = "test1.com"
    domain2 = "test2.com"

    # Exhaust rate limit for domain1
    for _ in range(rate_limiter.get_rate_limit(domain1)):
        rate_limiter.can_make_request(domain1)

    # domain2 should still be allowed
    assert rate_limiter.can_make_request(domain2) is True


def test_rate_limit_reset(rate_limiter):
    """Test rate limit reset"""
    domain = "test.com"

    # Make some requests
    rate_limiter.can_make_request(domain)
    assert len(rate_limiter._request_timestamps[domain]) > 0

    # Reset domain
    rate_limiter.reset(domain)
    assert len(rate_limiter._request_timestamps[domain]) == 0
    assert rate_limiter._error_counters[domain] == 0


def test_concurrent_requests(rate_limiter):
    """Test handling of concurrent requests"""
    domain = "test.com"
    rate_limit = rate_limiter.get_rate_limit(domain)

    # Simulate concurrent requests
    results = []
    for _ in range(rate_limit + 5):
        try:
            results.append(rate_limiter.can_make_request(domain))
        except RateLimitExceeded:
            results.append(False)

    # Should have exactly rate_limit True results
    assert sum(results) == rate_limit


def test_error_counter_reset(rate_limiter):
    """Test error counter reset after success"""
    domain = "test.com"

    # Record some errors
    for _ in range(3):
        rate_limiter.record_error(domain)
    assert rate_limiter._error_counters[domain] > 0

    # Success should reset counter
    rate_limiter.record_success(domain)
    assert rate_limiter._error_counters[domain] == 0


def test_rate_limit_minimum(rate_limiter):
    """Test rate limit minimum value"""
    domain = "test.com"

    # Force rate limit reduction
    for _ in range(10):
        rate_limiter.record_error(domain, status_code=429)

    # Should not go below 1
    assert rate_limiter.get_rate_limit(domain) >= 1


def test_rate_limit_maximum(rate_limiter):
    """Test rate limit maximum value"""
    domain = "test.com"

    # Record many successes
    for _ in range(20):
        rate_limiter.record_success(domain)

    # Should not exceed maximum
    assert rate_limiter.get_rate_limit(domain) <= 30


def test_timestamp_cleanup(rate_limiter):
    """Test old timestamp cleanup"""
    domain = "test.com"
    old_time = datetime.now() - timedelta(minutes=2)

    # Add old timestamps
    rate_limiter._request_timestamps[domain] = [old_time] * 5

    # Request should clean up old timestamps
    rate_limiter.can_make_request(domain)
    assert len(rate_limiter._request_timestamps[domain]) == 1

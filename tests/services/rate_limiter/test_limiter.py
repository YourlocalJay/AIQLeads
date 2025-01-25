import pytest
from src.services.rate_limiter.limiter import RateLimiter

def test_rate_limit_check(redis_mock):
    limiter = RateLimiter(redis_mock)
    assert limiter.check_rate_limit('test', 100, 3600)
    
def test_remaining_requests(redis_mock):
    limiter = RateLimiter(redis_mock)
    redis_mock.set('rate_limit:test:0', 50)
    assert limiter.get_remaining('test', 3600) == 50
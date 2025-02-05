from src.aggregator.exceptions import (
    ScraperError,
    RateLimitExceeded,
    InvalidCredentials,
    ParseError,
    LocationError,
    NetworkError,
    ProxyError,
    CaptchaError,
    BrowserError,
    ValidationError,
    PaginationError,
)


def test_base_scraper_error():
    """Test base scraper error with details"""
    error = ScraperError("Test error", code=500, source="test")
    assert (
        str(error)
        == "ScraperError: Test error | Details: {'code': 500, 'source': 'test'}"
    )
    assert error.details == {"code": 500, "source": "test"}


def test_rate_limit_exceeded():
    """Test rate limit exceeded error"""
    error = RateLimitExceeded(
        "Rate limit exceeded", domain="test.com", rate_limit=100, wait_time=60
    )
    assert "Rate limit exceeded" in str(error)
    assert error.details["domain"] == "test.com"
    assert error.details["rate_limit"] == 100
    assert error.details["wait_time"] == 60


def test_invalid_credentials():
    """Test invalid credentials error"""
    error = InvalidCredentials(
        "Invalid API key", service="test-api", key_type="api_key"
    )
    assert "Invalid API key" in str(error)
    assert error.details["service"] == "test-api"
    assert error.details["key_type"] == "api_key"


def test_parse_error():
    """Test parse error"""
    error = ParseError(
        "Failed to parse JSON", data={"test": "data"}, source="test.json"
    )
    assert "Failed to parse JSON" in str(error)
    assert error.details["data"] == {"test": "data"}
    assert error.details["source"] == "test.json"


def test_location_error():
    """Test location error"""
    error = LocationError(
        "Invalid location format", location="invalid", required_format="lat,lng"
    )
    assert "Invalid location format" in str(error)
    assert error.details["location"] == "invalid"
    assert error.details["required_format"] == "lat,lng"


def test_network_error():
    """Test network error"""
    error = NetworkError("Connection timeout", url="https://test.com", timeout=30)
    assert "Connection timeout" in str(error)
    assert error.details["url"] == "https://test.com"
    assert error.details["timeout"] == 30


def test_proxy_error():
    """Test proxy error"""
    error = ProxyError(
        "Proxy connection failed", proxy="http://proxy.test.com", attempt=2
    )
    assert "Proxy connection failed" in str(error)
    assert error.details["proxy"] == "http://proxy.test.com"
    assert error.details["attempt"] == 2


def test_captcha_error():
    """Test CAPTCHA error"""
    error = CaptchaError(
        "Failed to solve CAPTCHA", type="recaptcha", provider="2captcha"
    )
    assert "Failed to solve CAPTCHA" in str(error)
    assert error.details["type"] == "recaptcha"
    assert error.details["provider"] == "2captcha"


def test_browser_error():
    """Test browser error"""
    error = BrowserError(
        "Failed to initialize browser", browser="chromium", headless=True
    )
    assert "Failed to initialize browser" in str(error)
    assert error.details["browser"] == "chromium"
    assert error.details["headless"] is True


def test_validation_error():
    """Test validation error"""
    error = ValidationError(
        "Required field missing",
        field="email",
        constraints=["required", "email_format"],
    )
    assert "Required field missing" in str(error)
    assert error.details["field"] == "email"
    assert error.details["constraints"] == ["required", "email_format"]


def test_pagination_error():
    """Test pagination error"""
    error = PaginationError("Invalid page token", page=5, total_pages=10)
    assert "Invalid page token" in str(error)
    assert error.details["page"] == 5
    assert error.details["total_pages"] == 10


def test_error_inheritance():
    """Test error class inheritance"""
    assert issubclass(RateLimitExceeded, ScraperError)
    assert issubclass(InvalidCredentials, ScraperError)
    assert issubclass(ParseError, ScraperError)
    assert issubclass(LocationError, ScraperError)
    assert issubclass(NetworkError, ScraperError)
    assert issubclass(ProxyError, ScraperError)
    assert issubclass(CaptchaError, ScraperError)
    assert issubclass(BrowserError, ScraperError)
    assert issubclass(ValidationError, ScraperError)
    assert issubclass(PaginationError, ScraperError)


def test_error_chaining():
    """Test error chaining"""
    original = ValueError("Original error")
    error = ScraperError("Wrapped error", original_error=original)
    assert "Wrapped error" in str(error)
    assert error.details["original_error"] == original


def test_empty_details():
    """Test error with no additional details"""
    error = ScraperError("Simple error")
    assert str(error) == "ScraperError: Simple error | Details: {}"
    assert error.details == {}

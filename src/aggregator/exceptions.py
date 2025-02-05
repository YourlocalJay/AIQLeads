from typing import Optional


class ScraperError(Exception):
    """Base exception for scraper-related errors."""

    def __init__(self, message: str, **kwargs):
        """
        Args:
            message: Error message describing the exception
            kwargs: Additional context or details about the error
        """
        super().__init__(message)
        self.details = kwargs

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.args[0]} | Details: {self.details}"


class RateLimitExceeded(ScraperError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(message, **kwargs)


class InvalidCredentials(ScraperError):
    """Raised when API credentials are invalid."""

    def __init__(self, message: str = "Invalid API credentials", **kwargs):
        super().__init__(message, **kwargs)


class ParseError(ScraperError):
    """Raised when data parsing fails."""

    def __init__(self, message: str = "Data parsing failed", **kwargs):
        super().__init__(message, **kwargs)


class LocationError(ScraperError):
    """Raised when location parsing or geocoding fails."""

    def __init__(self, message: str = "Location parsing or geocoding failed", **kwargs):
        super().__init__(message, **kwargs)


class NetworkError(ScraperError):
    """Raised when network requests fail."""

    def __init__(self, message: str = "Network request failed", **kwargs):
        super().__init__(message, **kwargs)


class ProxyError(ScraperError):
    """Raised when proxy-related operations fail."""

    def __init__(
        self,
        message: str = "Proxy operation failed",
        proxy: Optional[str] = None,
        **kwargs,
    ):
        kwargs["proxy"] = proxy
        super().__init__(message, **kwargs)


class CaptchaError(ScraperError):
    """Raised when CAPTCHA detection or solving fails."""

    def __init__(self, message: str = "CAPTCHA handling failed", **kwargs):
        super().__init__(message, **kwargs)


class BrowserError(ScraperError):
    """Raised when browser-related operations fail."""

    def __init__(self, message: str = "Browser operation failed", **kwargs):
        super().__init__(message, **kwargs)


class ValidationError(ScraperError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str = "Data validation failed",
        field: Optional[str] = None,
        **kwargs,
    ):
        kwargs["field"] = field
        super().__init__(message, **kwargs)


class PaginationError(ScraperError):
    """Raised when pagination handling fails."""

    def __init__(
        self, message: str = "Pagination failed", page: Optional[int] = None, **kwargs
    ):
        kwargs["page"] = page
        super().__init__(message, **kwargs)

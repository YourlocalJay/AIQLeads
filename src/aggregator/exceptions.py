class ScraperError(Exception):
    """Base exception for scraper-related errors."""
    def __init__(self, message: str, **kwargs):
        """
        Args:
            message (str): Error message describing the exception.
            kwargs: Additional context or details about the error.
        """
        super().__init__(message)
        self.details = kwargs

    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0]} | Details: {self.details}"


class RateLimitExceeded(ScraperError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message="Rate limit exceeded", **kwargs):
        super().__init__(message, **kwargs)


class InvalidCredentials(ScraperError):
    """Raised when API credentials are invalid."""
    def __init__(self, message="Invalid API credentials", **kwargs):
        super().__init__(message, **kwargs)


class ParseError(ScraperError):
    """Raised when data parsing fails."""
    def __init__(self, message="Data parsing failed", **kwargs):
        super().__init__(message, **kwargs)


class LocationError(ScraperError):
    """Raised when location parsing or geocoding fails."""
    def __init__(self, message="Location parsing or geocoding failed", **kwargs):
        super().__init__(message, **kwargs)


class NetworkError(ScraperError):
    """Raised when network requests fail."""
    def __init__(self, message="Network request failed", **kwargs):
        super().__init__(message, **kwargs)

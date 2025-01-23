class ScraperError(Exception):
    """Base exception for scraper-related errors."""
    pass

class RateLimitExceeded(ScraperError):
    """Raised when rate limit is exceeded."""
    pass

class InvalidCredentials(ScraperError):
    """Raised when API credentials are invalid."""
    pass

class ParseError(ScraperError):
    """Raised when data parsing fails."""
    pass

class LocationError(ScraperError):
    """Raised when location parsing or geocoding fails."""
    pass

class NetworkError(ScraperError):
    """Raised when network requests fail."""
    pass
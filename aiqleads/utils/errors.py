class ScraperError(Exception):
    """Base exception for scraper-related errors."""
    pass

class RateLimitExceeded(ScraperError):
    """Raised when rate limit is exceeded."""
    pass

class NetworkError(ScraperError):
    """Raised when network requests fail."""
    pass

class ParseError(ScraperError):
    """Raised when data parsing fails."""
    pass

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.aggregator.rate_limiter import RateLimiter
from src.aggregator.exceptions import ScraperError, NetworkError
from src.schemas.lead_schema import LeadCreate


class BaseScraper(ABC):
    """Abstract base class for all lead scrapers.
    
    Provides core functionality and interface requirements for platform-specific
    implementations. Handles rate limiting, error tracking, and data validation.
    """
    
    def __init__(self, rate_limit: int = 60, time_window: int = 60):
        """Initialize scraper with rate limiting parameters.
        
        Args:
            rate_limit (int): Maximum number of requests allowed
            time_window (int): Time window in seconds for rate limiting
        """
        self.rate_limiter = RateLimiter(rate_limit, time_window)
        self.errors: List[Dict[str, Any]] = []
        self.last_scrape: Optional[datetime] = None
        self._session = None  # HTTP session placeholder for implementations
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """Initialize scraper resources (e.g., HTTP session)."""
        pass
    
    async def cleanup(self) -> None:
        """Clean up resources (e.g., close HTTP session)."""
        if self._session:
            await self._session.close()
            self._session = None
    
    @abstractmethod
    async def search(self, location: str, radius_km: float = 50.0, **kwargs) -> List[LeadCreate]:
        """Search for leads in the specified location.
        
        Args:
            location (str): Target location (city, state, or postal code)
            radius_km (float): Search radius in kilometers
            **kwargs: Platform-specific search parameters
            
        Returns:
            List[LeadCreate]: List of validated lead schemas
            
        Raises:
            ScraperError: If scraping fails or rate limit is exceeded
            NetworkError: If network request fails
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate API credentials or session state.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        return True  # Default implementation for scrapers without credentials
    
    def add_error(self, error_type: str, details: str, data: Optional[Dict] = None) -> None:
        """Record an error for logging and monitoring.
        
        Args:
            error_type (str): Category of error (e.g., 'rate_limit', 'parse_error')
            details (str): Error description
            data (Optional[Dict]): Additional error context
        """
        error_entry = {
            'timestamp': datetime.utcnow(),
            'type': error_type,
            'details': details,
            'data': data or {}
        }
        self.errors.append(error_entry)
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Returns:
            Dict containing current rate limit metrics
        """
        return await self.rate_limiter.get_status()
    
    def clear_errors(self) -> None:
        """Clear error history."""
        self.errors = []
    
    @abstractmethod
    async def extract_contact_info(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information from raw listing data.
        
        Args:
            listing_data (Dict[str, Any]): Raw data from platform API/scrape
            
        Returns:
            Dict[str, Any]: Normalized contact information
            
        Raises:
            ParseError: If contact information extraction fails
        """
        pass

    async def is_rate_limited(self) -> bool:
        """Check if the scraper is currently rate-limited.
        
        Returns:
            bool: True if rate limit is exceeded, False otherwise
        """
        return not await self.rate_limiter.check_rate_limit()

    async def log_scrape_activity(self, leads_found: int) -> None:
        """Log scraper activity after a scrape operation.
        
        Args:
            leads_found (int): Number of leads discovered in the scrape
        """
        self.last_scrape = datetime.utcnow()

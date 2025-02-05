from src.aggregator.base_scraper import BaseScraper
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ScraperError, ParseError, NetworkError
from typing import List, Dict, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """
    Enhanced LinkedIn scraper with improved error handling, rate limiting,
    and contact extraction capabilities.
    """

    BASE_URL = "https://api.linkedin.com/v2/"
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    BATCH_SIZE = 25  # listings per request

    def __init__(
        self,
        rate_limit: int = 30,
        time_window: int = RATE_LIMIT_WINDOW,
        api_key: Optional[str] = None,
    ):
        """
        Initialize LinkedIn scraper with configurable parameters.

        Args:
            rate_limit: Maximum requests per time window
            time_window: Time window in seconds
            api_key: Optional API key for authentication
        """
        super().__init__(rate_limit, time_window)
        self.api_key = api_key
        self.session_token = None
        self._cache = {}
        self._cache_ttl = timedelta(minutes=15)

    async def search(
        self,
        location: str,
        radius_km: float = 50.0,
        batch_size: int = BATCH_SIZE,
        **kwargs,
    ) -> List[LeadCreate]:
        """
        Search for real estate leads on LinkedIn with enhanced features.

        Args:
            location: Target location (city, state, or postal code)
            radius_km: Search radius in kilometers
            batch_size: Number of listings per request
            **kwargs: Additional search parameters

        Returns:
            List of validated LeadCreate instances

        Raises:
            ScraperError: On scraping failures
            NetworkError: On network issues
        """
        try:
            logger.info(
                f"Starting LinkedIn search: location={location}, radius={radius_km}km"
            )

            # Check cache first
            cache_key = f"{location}:{radius_km}"
            if cached_results := self._get_from_cache(cache_key):
                logger.info("Returning cached results")
                return cached_results

            await self.rate_limiter.acquire()

            leads = []
            retry_count = 0

            while retry_count < self.MAX_RETRIES:
                try:
                    raw_listings = await self._fetch_listings(
                        location, radius_km, batch_size
                    )
                    parsed_leads = await self._process_listings(raw_listings)
                    leads.extend(parsed_leads)

                    # Store in cache
                    self._add_to_cache(cache_key, leads)

                    await self.log_scrape_activity(len(leads))
                    logger.info(f"Successfully extracted {len(leads)} leads")
                    return leads

                except NetworkError as e:
                    retry_count += 1
                    if retry_count >= self.MAX_RETRIES:
                        raise
                    logger.warning(
                        f"Retry {retry_count}/{self.MAX_RETRIES} after error: {e}"
                    )
                    await asyncio.sleep(self.RETRY_DELAY * retry_count)

        except Exception as e:
            self.add_error(
                "search_error",
                str(e),
                {
                    "location": location,
                    "radius_km": radius_km,
                    "timestamp": datetime.utcnow(),
                },
            )
            logger.error(f"LinkedIn search failed: {str(e)}", exc_info=True)
            raise ScraperError(f"LinkedIn search failed: {str(e)}")

    async def validate_credentials(self) -> bool:
        """
        Validate LinkedIn API credentials with retry logic.

        Returns:
            bool: True if credentials are valid

        Raises:
            ScraperError: On validation failure
        """
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                # Implement actual credential validation here
                endpoint = urljoin(self.BASE_URL, "credentials/validate")
                # Add validation logic
                return True

            except NetworkError as e:
                retry_count += 1
                if retry_count >= self.MAX_RETRIES:
                    raise ScraperError(f"Credential validation failed: {str(e)}")
                await asyncio.sleep(self.RETRY_DELAY * retry_count)

    async def extract_contact_info(
        self, listing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and validate contact information with enhanced validation.

        Args:
            listing_data: Raw LinkedIn listing data

        Returns:
            Normalized contact information

        Raises:
            ParseError: On extraction failure
        """
        try:
            contact_info = {
                "name": listing_data.get("name", "").strip(),
                "email": listing_data.get("email"),
                "phone": listing_data.get("phone"),
                "linkedin_url": listing_data.get("profile_url"),
                "company": listing_data.get("company_name"),
                "title": listing_data.get("title"),
                "extracted_at": datetime.utcnow(),
            }

            if not contact_info["email"] and not contact_info["phone"]:
                raise ParseError("Neither email nor phone available")

            # Validate contact info
            if contact_info["email"]:
                self._validate_email(contact_info["email"])
            if contact_info["phone"]:
                self._normalize_phone(contact_info["phone"])

            return contact_info

        except Exception as e:
            self.add_error("contact_extraction_error", str(e), listing_data)
            logger.error(f"Contact extraction failed: {str(e)}")
            raise ParseError(f"Contact extraction failed: {str(e)}")

    async def _fetch_listings(
        self, location: str, radius_km: float, batch_size: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch listings from LinkedIn API with batching support.

        Args:
            location: Search location
            radius_km: Search radius
            batch_size: Number of listings per request

        Returns:
            List of raw listing data
        """
        # Implementation placeholder
        await asyncio.sleep(1)  # Simulate API call
        return []

    async def _process_listings(self, raw_listings: List[Dict]) -> List[LeadCreate]:
        """
        Process raw listings into validated lead schemas.

        Args:
            raw_listings: Raw listing data from API

        Returns:
            List of validated LeadCreate instances
        """
        leads = []
        for listing in raw_listings:
            try:
                contact_info = await self.extract_contact_info(listing)
                lead = LeadCreate(
                    name=contact_info["name"],
                    email=contact_info["email"],
                    phone=contact_info["phone"],
                    source="LinkedIn",
                    metadata={
                        "linkedin_url": contact_info["linkedin_url"],
                        "company": contact_info["company"],
                        "title": contact_info["title"],
                        "extracted_at": contact_info["extracted_at"],
                    },
                )
                leads.append(lead)
            except ParseError as e:
                logger.warning(f"Skipping invalid listing: {str(e)}")
                continue
        return leads

    def _get_from_cache(self, key: str) -> Optional[List[LeadCreate]]:
        """Get results from cache if still valid."""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.utcnow() - entry["timestamp"] < self._cache_ttl:
                return entry["data"]
        return None

    def _add_to_cache(self, key: str, data: List[LeadCreate]) -> None:
        """Add results to cache with timestamp."""
        self._cache[key] = {"timestamp": datetime.utcnow(), "data": data}

    @staticmethod
    def _validate_email(email: str) -> None:
        """Validate email format."""
        # Add email validation logic
        pass

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize phone number format."""
        # Add phone normalization logic
        return phone

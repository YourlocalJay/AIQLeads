from src.aggregator.base_scraper import BaseScraper
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ScraperError, ParseError, NetworkError
from typing import List, Dict, Optional, Any
import asyncio
import logging
import aiohttp
from datetime import datetime
from urllib.parse import urljoin
import phonenumbers
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)


class CraigslistScraper(BaseScraper):
    """
    Enhanced Craigslist scraper with full API integration and robust error handling.
    """

    BASE_URL = "https://api.craigslist.org/v1/"
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    BATCH_SIZE = 20  # listings per request

    def __init__(
        self,
        rate_limit: int = 20,
        time_window: int = RATE_LIMIT_WINDOW,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Craigslist scraper with configurable parameters.

        Args:
            rate_limit: Maximum requests per time window
            time_window: Time window in seconds
            api_key: Optional API key for authentication
        """
        super().__init__(rate_limit, time_window)
        self.api_key = api_key
        self.session = None

    async def initialize(self):
        """Initialize aiohttp session for requests."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers=self._get_headers(), timeout=aiohttp.ClientTimeout(total=30)
            )

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def search(
        self,
        location: str,
        radius_km: float = 50.0,
        category: str = "real-estate",
        **kwargs,
    ) -> List[LeadCreate]:
        """
        Search for real estate leads on Craigslist.

        Args:
            location: Target location (city, state, or postal code)
            radius_km: Search radius in kilometers
            category: Listing category
            **kwargs: Additional search parameters

        Returns:
            List of validated LeadCreate instances
        """
        try:
            await self.initialize()
            logger.info(
                f"Starting Craigslist search: location={location}, radius={radius_km}km"
            )

            await self.rate_limiter.acquire()
            leads = []
            retry_count = 0

            while retry_count < self.MAX_RETRIES:
                try:
                    raw_listings = await self._fetch_listings(
                        location, radius_km, category
                    )
                    parsed_leads = await self._process_listings(raw_listings)
                    leads.extend(parsed_leads)

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
            logger.error(f"Craigslist search failed: {str(e)}", exc_info=True)
            raise ScraperError(f"Craigslist search failed: {str(e)}")
        finally:
            await self.cleanup()

    async def extract_contact_info(
        self, listing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and validate contact information from listing data.

        Args:
            listing_data: Raw listing data

        Returns:
            Normalized contact information
        """
        try:
            contact_info = {
                "name": listing_data.get("contact_name", "").strip(),
                "email": listing_data.get("contact_email"),
                "phone": listing_data.get("contact_phone"),
                "location": listing_data.get("location", {}),
                "posting_date": listing_data.get("posting_date"),
                "price": listing_data.get("price"),
            }

            if not contact_info["email"] and not contact_info["phone"]:
                raise ParseError("Neither email nor phone available")

            # Validate and normalize contact info
            if contact_info["email"]:
                contact_info["email"] = self._validate_email(contact_info["email"])
            if contact_info["phone"]:
                contact_info["phone"] = self._normalize_phone(contact_info["phone"])

            return contact_info

        except Exception as e:
            self.add_error("contact_extraction_error", str(e), listing_data)
            logger.error(f"Contact extraction failed: {str(e)}")
            raise ParseError(f"Contact extraction failed: {str(e)}")

    async def _fetch_listings(
        self, location: str, radius_km: float, category: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch listings from Craigslist API.

        Args:
            location: Search location
            radius_km: Search radius
            category: Listing category

        Returns:
            List of raw listing data
        """
        endpoint = urljoin(self.BASE_URL, "search")
        params = {
            "location": location,
            "radius": radius_km,
            "category": category,
            "limit": self.BATCH_SIZE,
            "format": "json",
        }

        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 429:  # Rate limit exceeded
                    retry_after = int(
                        response.headers.get("Retry-After", self.RETRY_DELAY)
                    )
                    logger.warning(
                        f"Rate limit exceeded. Waiting {retry_after} seconds"
                    )
                    await asyncio.sleep(retry_after)
                    raise NetworkError("Rate limit exceeded")

                response.raise_for_status()
                data = await response.json()
                return data.get("listings", [])

        except aiohttp.ClientError as e:
            raise NetworkError(f"API request failed: {str(e)}")

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
                    source="Craigslist",
                    metadata={
                        "location": contact_info["location"],
                        "posting_date": contact_info["posting_date"],
                        "price": contact_info["price"],
                        "listing_url": listing.get("url"),
                        "extracted_at": datetime.utcnow(),
                    },
                )
                leads.append(lead)
            except ParseError as e:
                logger.warning(f"Skipping invalid listing: {str(e)}")
                continue
        return leads

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional API key."""
        headers = {"User-Agent": "AIQLeads/1.0", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _validate_email(email: str) -> str:
        """Validate email format."""
        try:
            validated_email = validate_email(email).email
            return validated_email
        except EmailNotValidError as e:
            raise ParseError(f"Invalid email: {email}") from e

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize phone number format."""
        try:
            parsed_phone = phonenumbers.parse(phone, "US")  # Default region: US
            if not phonenumbers.is_valid_number(parsed_phone):
                raise ParseError(f"Invalid phone number: {phone}")
            return phonenumbers.format_number(
                parsed_phone, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException as e:
            raise ParseError(f"Invalid phone number: {phone}") from e

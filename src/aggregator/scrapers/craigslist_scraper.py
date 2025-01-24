from src.aggregator.base_scraper import BaseScraper
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ScraperError, ParseError
from src.aggregator.rate_limiter import RateLimiter
from typing import List, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)

class CraigslistScraper(BaseScraper):
    """Scraper for extracting real estate leads from Craigslist."""

    def __init__(self, rate_limit: int = 20, time_window: int = 60):
        super().__init__(rate_limit, time_window)

    async def search(self, location: str, radius_km: float = 50.0, **kwargs) -> List[LeadCreate]:
        """
        Search for leads on Craigslist.

        Args:
            location (str): Target location (city, state, or postal code).
            radius_km (float): Search radius in kilometers.
            **kwargs: Additional search parameters.

        Returns:
            List[LeadCreate]: A list of leads extracted and validated.

        Raises:
            ScraperError: If scraping fails or rate limit is exceeded.
        """
        try:
            logger.info(f"Starting Craigslist search for location: {location}, radius: {radius_km} km")
            await self.rate_limiter.acquire()  # Enforce rate limiting

            # Simulate API call and response
            raw_listings = await self._mock_api_call(location, radius_km)

            # Parse and validate leads
            leads = [self._parse_listing(listing) for listing in raw_listings]
            logger.info(f"Successfully extracted {len(leads)} leads from Craigslist.")
            return leads
        except Exception as e:
            self.add_error("search_error", str(e))
            logger.error(f"Craigslist scraping failed: {e}")
            raise ScraperError("Craigslist scraping failed.")

    async def validate_credentials(self) -> bool:
        """
        Craigslist scrapers typically do not need credentials.

        Returns:
            bool: Always True for Craigslist.
        """
        logger.info("Craigslist scraper does not require credential validation.")
        return True

    async def extract_contact_info(self, listing_data: dict) -> dict:
        """
        Extract contact information from Craigslist listing data.

        Args:
            listing_data (dict): Raw data from Craigslist.

        Returns:
            dict: Extracted contact information.
        """
        try:
            contact_info = {
                "name": listing_data.get("name", "N/A"),
                "email": listing_data.get("email", None),
                "phone": listing_data.get("phone", None),
            }
            if not contact_info["phone"] and not contact_info["email"]:
                raise ParseError("Missing both phone and email in contact info.")
            return contact_info
        except Exception as e:
            self.add_error("contact_extraction_error", str(e), listing_data)
            logger.error(f"Failed to extract contact info: {e}")
            raise ScraperError("Failed to extract contact info.")

    async def _mock_api_call(self, location: str, radius_km: float) -> List[dict]:
        """
        Mock API call to simulate Craigslist scraping.

        Args:
            location (str): Target location.
            radius_km (float): Search radius in kilometers.

        Returns:
            List[dict]: Simulated raw listing data.
        """
        await asyncio.sleep(1)  # Simulate network delay
        return [
            {"name": "Alice Johnson", "email": "alice.johnson@example.com", "phone": "+1111111111"},
            {"name": "Bob Carter", "email": None, "phone": "+2222222222"},
        ]

    def _parse_listing(self, listing: dict) -> LeadCreate:
        """
        Parse raw listing into LeadCreate schema.

        Args:
            listing (dict): Raw listing data.

        Returns:
            LeadCreate: Validated lead schema.
        """
        try:
            return LeadCreate(
                name=listing["name"],
                email=listing.get("email"),
                phone=listing.get("phone"),
                source="Craigslist"
            )
        except KeyError as e:
            raise ParseError(f"Missing required field: {e}")

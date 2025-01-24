from src.aggregator.base_scraper import BaseScraper
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ScraperError, ParseError
from src.aggregator.rate_limiter import RateLimiter
from typing import List, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)

class FSBOScraper(BaseScraper):
    """Scraper for extracting For Sale By Owner (FSBO) property leads."""

    BASE_URL = "https://www.forsalebyowner.com/api/v1/properties"

    def __init__(self, rate_limit: int = 50, time_window: int = 60):
        super().__init__(rate_limit, time_window)

    async def search(self, location: str, radius_km: float = 50.0, **kwargs) -> List[LeadCreate]:
        """
        Search for FSBO property leads in the specified location.

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
            logger.info(f"Starting FSBO search for location: {location}, radius: {radius_km} km")
            await self.rate_limiter.acquire()  # Enforce rate limiting

            # Simulate API call and response
            raw_listings = await self._mock_api_call(location, radius_km)

            # Parse and validate leads
            leads = [self._parse_listing(listing) for listing in raw_listings]
            logger.info(f"Successfully extracted {len(leads)} leads from FSBO.")
            return leads
        except Exception as e:
            self.add_error("search_error", str(e))
            logger.error(f"FSBO scraping failed: {e}")
            raise ScraperError("FSBO scraping failed.")

    async def validate_credentials(self) -> bool:
        """
        Validate API credentials if required (FSBO typically doesn’t need credentials).

        Returns:
            bool: Always True for FSBO.
        """
        logger.info("FSBO scraper does not require credential validation.")
        return True

    async def extract_contact_info(self, listing_data: dict) -> dict:
        """
        Extract contact information from FSBO listing data.

        Args:
            listing_data (dict): Raw data from FSBO.

        Returns:
            dict: Extracted contact information.
        """
        try:
            contact_info = {
                "name": listing_data.get("ownerName", "N/A"),
                "email": listing_data.get("ownerEmail", None),
                "phone": listing_data.get("ownerPhone", None),
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
        Mock API call to simulate FSBO scraping.

        Args:
            location (str): Target location.
            radius_km (float): Search radius in kilometers.

        Returns:
            List[dict]: Simulated raw listing data.
        """
        await asyncio.sleep(1)  # Simulate network delay
        return [
            {"ownerName": "Emily Carter", "ownerEmail": "emily.carter@example.com", "ownerPhone": "+4444444444"},
            {"ownerName": "Jack Brown", "ownerEmail": None, "ownerPhone": "+5555555555"},
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
                name=listing["ownerName"],
                email=listing.get("ownerEmail"),
                phone=listing.get("ownerPhone"),
                source="FSBO",
                metadata={
                    "property_id": listing.get("id"),
                    "price": listing.get("price"),
                    "location": listing.get("location"),
                    "property_type": listing.get("propertyType"),
                }
            )
        except KeyError as e:
            raise ParseError(f"Missing required field: {e}")

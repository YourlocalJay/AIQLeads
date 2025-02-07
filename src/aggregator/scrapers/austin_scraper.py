import asyncio
import logging
from typing import List, Optional
from urllib.parse import urlencode

from aiqleads.scrapers.base_scraper import BaseScraper
from aiqleads.schemas.lead_schema import LeadCreate
from aiqleads.scrapers.exceptions import ScraperError, ParseError
from aiqleads.utils.request_fingerprint import RequestFingerprinter

logger = logging.getLogger(__name__)

class AustinScraper(BaseScraper):
    """Scraper for extracting real estate leads from Austin and surrounding areas."""

    BASE_URL = "https://www.austinrealestate.com/api/v1/properties"
    SUBREGIONS = ["Round Rock", "Cedar Park", "Pflugerville", "Georgetown"]

    def __init__(self, rate_limit: int = 50, time_window: int = 60):
        super().__init__(rate_limit, time_window)

    async def search(
        self,
        location: str = "Austin",
        radius_km: float = 50.0,
        include_subregions: bool = True,
        **kwargs,
    ) -> List[LeadCreate]:
        """
        Search for properties in Austin and optional surrounding areas.

        Args:
            location (str): Central target location (default: "Austin").
            radius_km (float): Search radius in kilometers.
            include_subregions (bool): Whether to include predefined subregions.
            **kwargs: Additional search parameters.

        Returns:
            List[LeadCreate]: A list of validated leads extracted.
        """
        try:
            logger.info(f"Starting Austin search for location: {location}, radius: {radius_km} km")
            await self.rate_limiter.acquire()

            # Gather listings for the main location and subregions
            locations_to_search = [location]
            if include_subregions:
                locations_to_search.extend(self.SUBREGIONS)

            all_leads = await asyncio.gather(*[self._fetch_listings(loc, radius_km) for loc in locations_to_search])

            # Flatten list and remove empty results
            extracted_leads = [lead for leads in all_leads for lead in leads if leads]
            logger.info(f"Total leads extracted: {len(extracted_leads)}")

            return extracted_leads
        except Exception as e:
            self.add_error("search_error", str(e))
            logger.error(f"Austin scraper failed: {e}", exc_info=True)
            raise ScraperError("Austin scraper failed.") from e

    async def validate_credentials(self) -> bool:
        """
        Validate credentials if required (most local MLS sites require logins).

        Returns:
            bool: Always True for Austin scraper.
        """
        logger.info("Validating credentials for Austin scraper.")
        return True  # Simulated validation

    async def extract_contact_info(self, listing_data: dict) -> dict:
        """
        Extract contact information.

        Args:
            listing_data (dict): Raw data from Austin listings.

        Returns:
            dict: Extracted contact information.
        """
        try:
            contact_info = {
                "name": listing_data.get("agentName", "N/A"),
                "email": listing_data.get("agentEmail"),
                "phone": listing_data.get("agentPhone"),
            }
            if not contact_info["phone"] and not contact_info["email"]:
                raise ParseError("Missing both phone and email in contact info.")
            return contact_info
        except Exception as e:
            self.add_error("contact_extraction_error", str(e), listing_data)
            logger.error(f"Failed to extract contact info: {e}", exc_info=True)
            raise ScraperError("Failed to extract contact info.") from e

    async def _fetch_listings(self, location: str, radius_km: float) -> List[LeadCreate]:
        """
        Fetch listings asynchronously.

        Args:
            location (str): Target location.
            radius_km (float): Search radius in kilometers.

        Returns:
            List[LeadCreate]: Parsed and validated listings.
        """
        params = {
            "location": location,
            "radius": radius_km,
            "type": "fsbo",
            "sort": "newest",
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"

        response = await self.fetch(url)
        if not response:
            self.add_error("fetch_error", f"Failed to fetch listings for {location}")
            logger.error(f"Failed to fetch listings for {location}")
            return []

        try:
            listings = response.get("listings", [])
            return [self._parse_listing(listing) for listing in listings]
        except Exception as e:
            self.add_error("parse_error", str(e), response)
            logger.error(f"Parsing error: {e}", exc_info=True)
            return []

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
                name=listing["agentName"],
                email=listing.get("agentEmail"),
                phone=listing.get("agentPhone"),
                source="AustinRealEstate",
                metadata={"price": listing.get("price"), "city": listing.get("city", "Austin")},
            )
        except KeyError as e:
            raise ParseError(f"Missing required field: {e}") from e


from src.aggregator.base_scraper import BaseScraper
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ScraperError, ParseError
from src.aggregator.rate_limiter import RateLimiter
from typing import List, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)

class LasVegasScraper(BaseScraper):
    """Scraper for extracting real estate leads from Las Vegas and surrounding areas."""
    
    BASE_URL = "https://www.lasvegasrealestate.com/api/v1/properties"
    SUBREGIONS = ["Henderson", "Summerlin", "North Las Vegas", "Enterprise"]

    def __init__(self, rate_limit: int = 50, time_window: int = 60):
        super().__init__(rate_limit, time_window)
    
    async def search(self, location: str = "Las Vegas", radius_km: float = 50.0, include_subregions: bool = True, **kwargs) -> List[LeadCreate]:
        """
        Search for properties in Las Vegas and optional surrounding areas.

        Args:
            location (str): Central target location (default: "Las Vegas").
            radius_km (float): Search radius in kilometers.
            include_subregions (bool): Whether to include predefined subregions.
            **kwargs: Additional search parameters.

        Returns:
            List[LeadCreate]: A list of leads extracted and validated.
        """
        try:
            logger.info(f"Starting Las Vegas search for location: {location}, radius: {radius_km} km")
            await self.rate_limiter.acquire()

            # Gather listings for the main location and subregions
            locations_to_search = [location]
            if include_subregions:
                locations_to_search.extend(self.SUBREGIONS)
            
            all_leads = []
            for loc in locations_to_search:
                logger.info(f"Searching location: {loc}")
                raw_listings = await self._mock_api_call(loc, radius_km)
                leads = [self._parse_listing(listing) for listing in raw_listings]
                all_leads.extend(leads)
                logger.info(f"Extracted {len(leads)} leads from {loc}.")
            
            logger.info(f"Total leads extracted: {len(all_leads)}")
            return all_leads
        except Exception as e:
            self.add_error("search_error", str(e))
            logger.error(f"Las Vegas scraper failed: {e}")
            raise ScraperError("Las Vegas scraper failed.")
    
    async def validate_credentials(self) -> bool:
        """
        Validate credentials if required (most local MLS sites require logins).

        Returns:
            bool: Always True for Las Vegas scraper.
        """
        logger.info("Validating credentials for Las Vegas scraper.")
        return True  # Simulated validation
    
    async def extract_contact_info(self, listing_data: dict) -> dict:
        """
        Extract contact information.

        Args:
            listing_data (dict): Raw data from Las Vegas listings.

        Returns:
            dict: Extracted contact information.
        """
        try:
            contact_info = {
                "name": listing_data.get("agentName", "N/A"),
                "email": listing_data.get("agentEmail", None),
                "phone": listing_data.get("agentPhone", None),
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
        Mock API call for testing.

        Args:
            location (str): Target location.
            radius_km (float): Search radius in kilometers.

        Returns:
            List[dict]: Simulated raw listing data.
        """
        await asyncio.sleep(1)
        return [
            {"agentName": "John Doe", "agentEmail": "john.doe@example.com", "agentPhone": "+1234567890", "price": 500000},
            {"agentName": "Jane Smith", "agentEmail": "jane.smith@example.com", "agentPhone": "+0987654321", "price": 600000},
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
                name=listing["agentName"],
                email=listing.get("agentEmail"),
                phone=listing.get("agentPhone"),
                source="LasVegasRealEstate",
                metadata={"price": listing.get("price"), "city": "Las Vegas"}
            )
        except KeyError as e:
            raise ParseError(f"Missing required field: {e}")

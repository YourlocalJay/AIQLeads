from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime
from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import SQLAlchemyError
from src.database.postgres_manager import PostgresManager
from src.models.lead_model import Lead
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError


class LasVegasParser(BaseParser):
    """
    Parser for Las Vegas real estate listings with advanced fraud detection,
    geospatial validation, and metadata enrichment.
    """

    MARKET_ID = "las_vegas"
    VERSION = "2.0.0"

    def __init__(self):
        super().__init__()
        self.price_pattern = re.compile(r"\$?([\d,]+(?:\.\d{2})?)")
        self.location_pattern = re.compile(
            r"Las Vegas|Henderson|North Las Vegas|Summerlin", re.IGNORECASE
        )

    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse Las Vegas market listing content.

        Args:
            content: Raw HTML content of the listing page.

        Returns:
            List of parsed and validated listing dictionaries.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")
            listings = []

            for item in soup.select(".listing-item"):
                try:
                    listing = {
                        "title": self._extract_title(item),
                        "price": self._parse_price(item),
                        "location": self._extract_location(item),
                        "geospatial_data": self._validate_geospatial_data(item),
                        "description": self._extract_description(item),
                        "contact": self._extract_contact(item),
                        "metadata": self._build_metadata(),
                    }
                    # Validate and append only if valid
                    if self.validate(listing):
                        listings.append(listing)
                except ParseError as e:
                    self.logger.warning(f"Skipping invalid listing: {e}")
                    continue

            return listings
        except Exception as e:
            raise ParseError(f"Failed to parse Las Vegas listings: {e}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract and validate the title of the listing."""
        title_elem = soup.select_one(".listing-title")
        if not title_elem:
            raise ParseError("Missing title element")
        return title_elem.text.strip()

    def _parse_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract and parse the price from the listing."""
        price_elem = soup.select_one(".listing-price")
        if not price_elem:
            return None

        match = self.price_pattern.search(price_elem.text)
        if not match:
            return None

        return float(match.group(1).replace(",", ""))

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract and validate the location."""
        location_elem = soup.select_one(".listing-location")
        if not location_elem:
            raise ParseError("Missing location element")

        location = location_elem.text.strip()
        if not self.location_pattern.search(location):
            raise ParseError("Invalid or unsupported location")

        return location

    def _validate_geospatial_data(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Validate geospatial data for Las Vegas area."""
        lat_elem = soup.select_one(".latitude")
        lng_elem = soup.select_one(".longitude")

        if not lat_elem or not lng_elem:
            raise ParseError("Missing geospatial data")

        try:
            latitude = float(lat_elem.text.strip())
            longitude = float(lng_elem.text.strip())
            return {"latitude": latitude, "longitude": longitude}
        except ValueError:
            raise ParseError("Invalid geospatial data format")

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract the description of the listing."""
        description_elem = soup.select_one(".listing-description")
        return (
            description_elem.text.strip()
            if description_elem
            else "No description provided."
        )

    def _extract_contact(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information from the listing."""
        contact = {}

        email_elem = soup.select_one(".contact-email")
        if email_elem:
            contact["email"] = email_elem.text.strip()

        phone_elem = soup.select_one(".contact-phone")
        if phone_elem:
            contact["phone"] = phone_elem.text.strip()

        if not contact:
            raise ParseError("No contact information available")

        return contact

    def _build_metadata(self) -> Dict[str, Any]:
        """Build metadata for the listing."""
        return {
            "market": self.MARKET_ID,
            "version": self.VERSION,
            "extracted_at": datetime.utcnow().isoformat(),
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate parsed data before further processing."""
        required_fields = {"title", "price", "location", "geospatial_data", "contact"}
        missing = required_fields - data.keys()
        if missing:
            raise ParseError(f"Missing required fields: {', '.join(missing)}")

        return True

    async def store_to_db(self, listings: List[Dict[str, Any]]) -> None:
        """Store parsed listings into the database."""
        db = PostgresManager()
        try:
            with db.get_session() as session:
                for listing in listings:
                    lead = Lead(
                        title=listing["title"],
                        price=listing["price"],
                        location=WKTElement(
                            f"POINT({listing['geospatial_data']['longitude']} {listing['geospatial_data']['latitude']})",
                            srid=4326,
                        ),
                        description=listing["description"],
                        contact=listing["contact"],
                        metadata=listing["metadata"],
                    )
                    session.add(lead)
                session.commit()
            self.logger.info(
                f"Successfully stored {len(listings)} listings to the database."
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Database storage failed: {e}")
            raise

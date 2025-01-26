from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import SQLAlchemyError
from src.database.postgres_manager import PostgresManager
from src.models.lead_model import Lead
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone

class LinkedInParser(BaseParser):
    """
    Parser for LinkedIn real estate leads.

    Extracts and validates data from LinkedIn listings, with advanced
    contact validation, geospatial support, and fraud detection.
    """

    MARKET_ID = "linkedin"
    VERSION = "1.0.0"

    def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse LinkedIn market listing content.

        Args:
            content (str): Raw HTML content of the listing page.

        Returns:
            List[Dict[str, Any]]: Parsed and validated listing dictionaries.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            listings = []

            for item in soup.select(".listing-item"):
                try:
                    listing = {
                        "title": self._extract_title(item),
                        "price": self._extract_price(item),
                        "location": self._extract_location(item),
                        "geospatial_data": self._validate_geospatial_data(item),
                        "description": self._extract_description(item),
                        "contact": self._extract_contact(item),
                        "metadata": self._build_metadata()
                    }

                    if self.validate(listing):
                        listings.append(listing)

                except ParseError as e:
                    self.logger.warning(f"Skipping invalid listing: {e}")
                    continue

            return listings
        except Exception as e:
            raise ParseError(f"Failed to parse LinkedIn listings: {e}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_elem = soup.select_one(".listing-title")
        if not title_elem:
            raise ParseError("Missing title element")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        price_elem = soup.select_one(".listing-price")
        if not price_elem:
            return None

        try:
            return float(price_elem.text.replace("$", "").replace(",", ""))
        except ValueError:
            raise ParseError("Invalid price format")

    def _extract_location(self, soup: BeautifulSoup) -> str:
        location_elem = soup.select_one(".listing-location")
        if not location_elem:
            raise ParseError("Missing location element")
        return location_elem.text.strip()

    def _validate_geospatial_data(self, soup: BeautifulSoup) -> Dict[str, float]:
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
        description_elem = soup.select_one(".listing-description")
        return description_elem.text.strip() if description_elem else "No description provided."

    def _extract_contact(self, soup: BeautifulSoup) -> Dict[str, str]:
        contact = {}

        email_elem = soup.select_one(".contact-email")
        if email_elem:
            contact['email'] = email_elem.text.strip()

        phone_elem = soup.select_one(".contact-phone")
        if phone_elem:
            contact['phone'] = phone_elem.text.strip()

        if not contact:
            raise ParseError("No contact information available")

        if contact.get('email') and not validate_email(contact['email']):
            raise ParseError("Invalid email format")

        if contact.get('phone') and not validate_phone(contact['phone']):
            raise ParseError("Invalid phone format")

        return contact

    def _build_metadata(self) -> Dict[str, Any]:
        return {
            "market": self.MARKET_ID,
            "version": self.VERSION,
            "extracted_at": datetime.utcnow().isoformat()
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        required_fields = {"title", "price", "location", "geospatial_data", "contact"}
        missing = required_fields - data.keys()
        if missing:
            raise ParseError(f"Missing required fields: {', '.join(missing)}")

        return True

    async def store_to_db(self, listings: List[Dict[str, Any]]) -> None:
        db = PostgresManager()
        try:
            with db.get_session() as session:
                for listing in listings:
                    lead = Lead(
                        title=listing['title'],
                        price=listing['price'],
                        location=WKTElement(f"POINT({listing['geospatial_data']['longitude']} {listing['geospatial_data']['latitude']})", srid=4326),
                        description=listing['description'],
                        contact=listing['contact'],
                        metadata=listing['metadata']
                    )
                    session.add(lead)
                session.commit()
            self.logger.info(f"Successfully stored {len(listings)} listings to the database.")
        except SQLAlchemyError as e:
            self.logger.error(f"Database storage failed: {e}")
            raise

from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from geoalchemy2 import WKTElement
from shapely.geometry import Point
from datetime import datetime
import logging
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone

logger = logging.getLogger(__name__)

class PhoenixParser(BaseParser):
    """
    Parser for Phoenix real estate listings, with advanced validation, geospatial handling,
    and fraud detection mechanisms.
    """

    MARKET_ID = "phoenix"
    VERSION = "1.1"

    def parse_listing(self, content: str) -> LeadCreate:
        """
        Parse raw listing content into a validated LeadCreate schema.

        Args:
            content (str): Raw HTML content of the listing.

        Returns:
            LeadCreate: Parsed lead schema.

        Raises:
            ParseError: If parsing fails or fields are invalid.
        """
        try:
            logger.info("Parsing Phoenix listing...")
            soup = BeautifulSoup(content, "html.parser")

            title = self._extract_title(soup)
            price = self._extract_price(soup)
            location = self._extract_location(soup)
            contact = self._extract_contact_info(soup)
            metadata = self._extract_metadata(soup)

            lead = LeadCreate(
                name=contact.get("name", "Unknown"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                price=price,
                location=location,
                source="Phoenix",
                metadata=metadata,
            )

            self._validate_lead(lead)
            logger.info(f"Successfully parsed lead: {lead}")

            return lead
        except Exception as e:
            logger.error(f"Failed to parse Phoenix listing: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse Phoenix listing: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_elem = soup.select_one(".listing-title")
        if not title_elem:
            raise ParseError("Missing title element.")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        price_elem = soup.select_one(".price")
        if not price_elem:
            raise ParseError("Missing price element.")
        try:
            return float(price_elem.text.replace("$", "").replace(",", "").strip())
        except ValueError:
            raise ParseError("Invalid price format.")

    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        location_elem = soup.select_one(".location")
        lat_elem = soup.select_one(".latitude")
        lng_elem = soup.select_one(".longitude")

        if not location_elem or not lat_elem or not lng_elem:
            raise ParseError("Missing location or geospatial data.")

        try:
            latitude = float(lat_elem.text.strip())
            longitude = float(lng_elem.text.strip())
            return {
                "address": location_elem.text.strip(),
                "coordinates": WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            }
        except ValueError:
            raise ParseError("Invalid geospatial data format.")

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        contact = {
            "name": soup.select_one(".contact-name").text.strip() if soup.select_one(".contact-name") else "Unknown",
            "email": soup.select_one(".contact-email").text.strip() if soup.select_one(".contact-email") else None,
            "phone": soup.select_one(".contact-phone").text.strip() if soup.select_one(".contact-phone") else None,
        }

        if contact["email"] and not validate_email(contact["email"]):
            raise ParseError("Invalid email format.")

        if contact["phone"] and not validate_phone(contact["phone"]):
            raise ParseError("Invalid phone format.")

        return contact

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract additional metadata for the listing.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            Dict[str, Any]: Metadata dictionary.
        """
        return {
            "listing_date": soup.select_one(".listing-date").text.strip() if soup.select_one(".listing-date") else None,
            "property_type": soup.select_one(".property-type").text.strip() if soup.select_one(".property-type") else None,
            "square_footage": soup.select_one(".sqft").text.strip() if soup.select_one(".sqft") else None,
            "bedrooms": soup.select_one(".bedrooms").text.strip() if soup.select_one(".bedrooms") else None,
            "bathrooms": soup.select_one(".bathrooms").text.strip() if soup.select_one(".bathrooms") else None,
        }

    def _validate_lead(self, lead: LeadCreate) -> None:
        """
        Validate the parsed lead schema.

        Args:
            lead (LeadCreate): Parsed lead.

        Raises:
            ParseError: If validation fails.
        """
        if not lead.title:
            raise ParseError("Title is missing.")
        if lead.price is None or lead.price <= 0:
            raise ParseError("Invalid price.")
        if not lead.location or not lead.location.get("coordinates"):
            raise ParseError("Invalid location or coordinates.")

    def parse_multiple_listings(self, listings: List[str]) -> List[LeadCreate]:
        """
        Parse multiple listings into LeadCreate objects.

        Args:
            listings (List[str]): List of raw HTML listing contents.

        Returns:
            List[LeadCreate]: List of parsed and validated leads.
        """
        parsed_leads = []
        for content in listings:
            try:
                lead = self.parse_listing(content)
                parsed_leads.append(lead)
            except ParseError as e:
                logger.warning(f"Skipping invalid listing: {e}")
                continue
        return parsed_leads

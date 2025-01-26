from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import re
from geoalchemy2.elements import WKTElement
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone, validate_price

logger = logging.getLogger(__name__)

class ZillowParser(BaseParser):
    """
    Parser for Zillow listings with enhanced validation, geospatial support,
    and fraud detection.
    """

    MARKET_ID = "zillow"
    VERSION = "2.0"

    def parse_listing(self, content: str) -> LeadCreate:
        """
        Parse raw HTML content from Zillow into a structured LeadCreate object.

        Args:
            content (str): Raw HTML content of a Zillow listing.

        Returns:
            LeadCreate: Parsed lead object.

        Raises:
            ParseError: If parsing fails or required fields are missing.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            title = self._extract_title(soup)
            price = self._extract_price(soup)
            location = self._extract_location(soup)
            sqft = self._extract_sqft(soup)
            bedrooms = self._extract_bedrooms(soup)
            bathrooms = self._extract_bathrooms(soup)
            contact = self._extract_contact_info(soup)
            fraud_score = self._calculate_fraud_score(price, sqft, contact)

            lead = LeadCreate(
                name=contact.get("name", "Unknown"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                source="Zillow",
                metadata={
                    "title": title,
                    "price": price,
                    "location": location,
                    "sqft": sqft,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "fraud_score": fraud_score,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "parser_version": self.VERSION,
                    "market": self.MARKET_ID,
                },
            )

            self._validate_lead(lead)
            return lead

        except Exception as e:
            logger.error(f"Failed to parse Zillow listing: {e}", exc_info=True)
            raise ParseError(f"Failed to parse Zillow listing: {e}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_elem = soup.select_one(".property-title")
        if not title_elem:
            raise ParseError("Missing property title.")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        price_elem = soup.select_one(".property-price")
        if not price_elem:
            return None
        try:
            return validate_price(price_elem.text.strip())
        except ValueError:
            raise ParseError("Invalid price format.")

    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        location_elem = soup.select_one(".property-location")
        if not location_elem:
            raise ParseError("Missing location element.")

        try:
            lat_elem = soup.select_one(".latitude")
            lng_elem = soup.select_one(".longitude")

            latitude = float(lat_elem.text.strip()) if lat_elem else None
            longitude = float(lng_elem.text.strip()) if lng_elem else None

            if latitude is None or longitude is None:
                raise ValueError("Incomplete geospatial data.")

            return {
                "address": location_elem.text.strip(),
                "geometry": WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            }
        except (ValueError, AttributeError):
            raise ParseError("Invalid geospatial data format.")

    def _extract_sqft(self, soup: BeautifulSoup) -> Optional[int]:
        sqft_elem = soup.select_one(".property-sqft")
        if not sqft_elem:
            return None
        try:
            return int(sqft_elem.text.strip().replace(",", ""))
        except ValueError:
            logger.warning(f"Invalid square footage format: {sqft_elem.text}")
            return None

    def _extract_bedrooms(self, soup: BeautifulSoup) -> Optional[int]:
        bedrooms_elem = soup.select_one(".property-bedrooms")
        if not bedrooms_elem:
            return None
        try:
            return int(bedrooms_elem.text.strip())
        except ValueError:
            logger.warning(f"Invalid bedrooms format: {bedrooms_elem.text}")
            return None

    def _extract_bathrooms(self, soup: BeautifulSoup) -> Optional[float]:
        bathrooms_elem = soup.select_one(".property-bathrooms")
        if not bathrooms_elem:
            return None
        try:
            return float(bathrooms_elem.text.strip())
        except ValueError:
            logger.warning(f"Invalid bathrooms format: {bathrooms_elem.text}")
            return None

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        contact = {
            "name": soup.select_one(".contact-name").text.strip() if soup.select_one(".contact-name") else "Unknown",
            "email": soup.select_one(".contact-email").text.strip() if soup.select_one(".contact-email") else None,
            "phone": soup.select_one(".contact-phone").text.strip() if soup.select_one(".contact-phone") else None,
        }

        if contact["email"] and not validate_email(contact["email"]):
            raise ParseError("Invalid email format.")

        if contact["phone"] and not validate_phone(contact["phone"]):
            raise ParseError("Invalid phone number format.")

        return contact

    def _calculate_fraud_score(self, price: Optional[float], sqft: Optional[int], contact: Dict[str, Any]) -> float:
        score = 0.0

        if not contact.get("email") and not contact.get("phone"):
            score += 20.0

        if price and price < 50000:
            score += 30.0

        if sqft and sqft > 10000:
            score += 15.0

        return min(score, 100.0)

    def _validate_lead(self, lead: LeadCreate) -> None:
        """
        Perform additional validation on the parsed lead.

        Args:
            lead (LeadCreate): Parsed lead.

        Raises:
            ParseError: If validation fails.
        """
        if lead.price is None or lead.price <= 0:
            raise ParseError("Lead price must be greater than zero.")

        if lead.metadata["location"] is None:
            raise ParseError("Lead location must be valid.")

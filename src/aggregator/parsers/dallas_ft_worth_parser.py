from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from geoalchemy2.elements import WKTElement
from shapely.geometry import Point
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone
import logging

logger = logging.getLogger(__name__)

class DallasFtWorthParser:
    """
    Parser for Dallas/Ft. Worth (DFW) region real estate listings.
    Includes geospatial capabilities and advanced fraud detection.
    """

    MARKET_ID = "dallas_ft_worth"
    VERSION = "2.0"

    @staticmethod
    def parse(content: str) -> LeadCreate:
        """
        Parse a DFW real estate listing into a structured LeadCreate object.

        Args:
            content (str): Raw HTML content of the listing.

        Returns:
            LeadCreate: Parsed and validated lead object.

        Raises:
            ParseError: If parsing fails or critical fields are missing.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            title = DallasFtWorthParser._extract_title(soup)
            price = DallasFtWorthParser._extract_price(soup)
            location = DallasFtWorthParser._extract_location(soup)
            sqft = DallasFtWorthParser._extract_sqft(soup)
            bedrooms = DallasFtWorthParser._extract_bedrooms(soup)
            bathrooms = DallasFtWorthParser._extract_bathrooms(soup)
            contact = DallasFtWorthParser._extract_contact(soup)
            fraud_score = DallasFtWorthParser._calculate_fraud_score(contact, price, sqft)

            lead = LeadCreate(
                name=contact.get("name", "Unknown"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                price=price,
                location=location,
                source="DallasFtWorth",
                metadata={
                    "title": title,
                    "square_footage": sqft,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "fraud_score": fraud_score,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "parser_version": DallasFtWorthParser.VERSION
                },
            )
            return lead
        except Exception as e:
            logger.error(f"Failed to parse DFW listing: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse DFW listing: {str(e)}")

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        title_elem = soup.select_one(".listing-title")
        if not title_elem:
            raise ParseError("Missing title element.")
        return title_elem.text.strip()

    @staticmethod
    def _extract_price(soup: BeautifulSoup) -> Optional[float]:
        price_elem = soup.select_one(".price")
        if not price_elem:
            raise ParseError("Missing price element.")
        try:
            return float(price_elem.text.strip().replace("$", "").replace(",", ""))
        except ValueError:
            raise ParseError("Invalid price format.")

    @staticmethod
    def _extract_location(soup: BeautifulSoup) -> Dict[str, Any]:
        location_elem = soup.select_one(".location")
        if not location_elem:
            raise ParseError("Missing location element.")

        try:
            lat_elem = soup.select_one(".latitude")
            lng_elem = soup.select_one(".longitude")

            latitude = float(lat_elem.text.strip()) if lat_elem else None
            longitude = float(lng_elem.text.strip()) if lng_elem else None

            if latitude is None or longitude is None:
                raise ParseError("Incomplete geospatial coordinates.")

            return {
                "address": location_elem.text.strip(),
                "coordinates": Point(longitude, latitude).wkt
            }
        except ValueError:
            raise ParseError("Invalid geospatial coordinate format.")

    @staticmethod
    def _extract_sqft(soup: BeautifulSoup) -> Optional[int]:
        sqft_elem = soup.select_one(".square-footage")
        if not sqft_elem:
            return None
        try:
            return int(sqft_elem.text.strip().replace(",", ""))
        except ValueError:
            logger.warning(f"Invalid square footage format: {sqft_elem.text}")
            return None

    @staticmethod
    def _extract_bedrooms(soup: BeautifulSoup) -> Optional[int]:
        bedrooms_elem = soup.select_one(".bedrooms")
        if not bedrooms_elem:
            return None
        try:
            return int(bedrooms_elem.text.strip())
        except ValueError:
            logger.warning(f"Invalid bedrooms format: {bedrooms_elem.text}")
            return None

    @staticmethod
    def _extract_bathrooms(soup: BeautifulSoup) -> Optional[float]:
        bathrooms_elem = soup.select_one(".bathrooms")
        if not bathrooms_elem:
            return None
        try:
            return float(bathrooms_elem.text.strip())
        except ValueError:
            logger.warning(f"Invalid bathrooms format: {bathrooms_elem.text}")
            return None

    @staticmethod
    def _extract_contact(soup: BeautifulSoup) -> Dict[str, str]:
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

    @staticmethod
    def _calculate_fraud_score(contact: Dict[str, Any], price: Optional[float], sqft: Optional[int]) -> float:
        score = 0.0

        if not contact.get("email") and not contact.get("phone"):
            score += 30.0
        if price and price < 50000:
            score += 20.0
        if sqft and sqft > 10000:
            score += 15.0

        return min(score, 100.0)

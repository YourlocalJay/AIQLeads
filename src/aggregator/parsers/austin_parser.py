from typing import Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from src.aggregator.parsers.base_parser import BaseParser
from src.utils.validators import validate_price, validate_coordinates, validate_numeric

class AustinParser(BaseParser):
    """
    Parser for Austin-specific real estate leads. Optimized for geospatial compatibility,
    advanced validation, and fraud detection.
    """

    MARKET_ID = "austin"
    VERSION = "2.1"

    def parse_lead(self, content: str) -> LeadCreate:
        """
        Parse raw lead content into a structured LeadCreate schema.

        Args:
            content (str): Raw HTML or JSON content.

        Returns:
            LeadCreate: Parsed lead object.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            title = self._extract_title(soup)
            price = self._extract_price(soup)
            location = self._extract_location(soup)
            sqft = self._extract_sqft(soup)
            bedrooms = self._extract_bedrooms(soup)
            bathrooms = self._extract_bathrooms(soup)
            fraud_score = self._calculate_fraud_score(soup)

            lead = LeadCreate(
                title=title,
                price=price,
                location=location,
                sqft=sqft,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                market=self.MARKET_ID,
                metadata={
                    "fraud_score": fraud_score,
                    "timestamp": datetime.utcnow().isoformat(),
                    "parser_version": self.VERSION,
                },
            )

            if not self.validate_lead(lead):
                raise ParseError("Validation failed for parsed lead.")

            return lead

        except Exception as e:
            raise ParseError(f"Failed to parse Austin lead: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract and validate the title of the listing."""
        title_elem = soup.select_one(".listing-title")
        if not title_elem:
            raise ParseError("Missing title element")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extract and validate the price."""
        price_elem = soup.select_one(".price")
        if not price_elem:
            raise ParseError("Missing price element")
        try:
            return validate_price(price_elem.text.strip())
        except ValueError as e:
            raise ParseError(f"Invalid price format: {e}")

    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract geospatial data and address."""
        location_elem = soup.select_one(".location")
        if not location_elem:
            raise ParseError("Missing location element")

        lat_elem = soup.select_one(".latitude")
        lon_elem = soup.select_one(".longitude")

        if not lat_elem or not lon_elem:
            raise ParseError("Missing geospatial coordinates")

        try:
            latitude, longitude = validate_coordinates(
                lat_elem.text.strip(), lon_elem.text.strip()
            )
            return {
                "address": location_elem.text.strip(),
                "coordinates": Point(longitude, latitude),
            }
        except ValueError as e:
            raise ParseError(f"Invalid geospatial coordinate format: {e}")

    def _extract_sqft(self, soup: BeautifulSoup) -> int:
        """Extract square footage."""
        sqft_elem = soup.select_one(".sqft")
        if not sqft_elem:
            return 0  # Default to 0 if missing
        try:
            return validate_numeric(sqft_elem.text.strip())
        except ValueError as e:
            raise ParseError(f"Invalid square footage format: {e}")

    def _extract_bedrooms(self, soup: BeautifulSoup) -> int:
        """Extract the number of bedrooms."""
        bed_elem = soup.select_one(".bedrooms")
        if not bed_elem:
            return 0  # Default to 0 if missing
        try:
            return validate_numeric(bed_elem.text.strip())
        except ValueError as e:
            raise ParseError(f"Invalid bedrooms format: {e}")

    def _extract_bathrooms(self, soup: BeautifulSoup) -> float:
        """Extract the number of bathrooms."""
        bath_elem = soup.select_one(".bathrooms")
        if not bath_elem:
            return 0.0  # Default to 0 if missing
        try:
            return validate_numeric(bath_elem.text.strip(), allow_float=True)
        except ValueError as e:
            raise ParseError(f"Invalid bathrooms format: {e}")

    def _calculate_fraud_score(self, soup: BeautifulSoup) -> float:
        """Calculate a fraud score based on suspicious patterns in the listing."""
        contact_elem = soup.select_one(".contact-info")
        if not contact_elem:
            return 75.0  # High fraud score for missing contact info

        price_elem = soup.select_one(".price")
        if price_elem and validate_price(price_elem.text.strip()) < 50000:
            return 85.0  # Very high fraud score for unrealistic prices

        return 10.0  # Low fraud score for well-documented listings

    def validate_lead(self, lead: LeadCreate) -> bool:
        """Validate the parsed lead for consistency and completeness."""
        required_fields = ["title", "price", "location"]
        for field in required_fields:
            if not getattr(lead, field):
                return False
        return True

    def __repr__(self) -> str:
        return f"<AustinParser version={self.VERSION}>"

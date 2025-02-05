from typing import Dict, Any
from bs4 import BeautifulSoup
from shapely.geometry import Point
from datetime import datetime
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from src.aggregator.parsers.base_parser import BaseParser
from src.utils.validators import (
    validate_price,
    validate_geospatial_coordinates,
)
import logging

logger = logging.getLogger(__name__)


class AustinParser(BaseParser):
    """
    Parser for Austin-specific real estate leads.
    Handles advanced geospatial compatibility, validation, and metadata extraction.
    """

    MARKET_ID = "austin"
    VERSION = "2.1"

    def parse_lead(self, content: str) -> LeadCreate:
        """
        Parse raw lead content into a structured LeadCreate schema.

        Args:
            content (str): Raw HTML content of the lead.

        Returns:
            LeadCreate: Parsed lead object.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            # Extract fields
            title = self._extract_title(soup)
            price = self._extract_price(soup)
            location = self._extract_location(soup)
            sqft = self._extract_sqft(soup)
            bedrooms = self._extract_bedrooms(soup)
            bathrooms = self._extract_bathrooms(soup)
            fraud_score = self._calculate_fraud_score(soup)

            # Create lead object
            return LeadCreate(
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
        except Exception as e:
            logger.error(f"Failed to parse Austin lead: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse Austin lead: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_elem = soup.select_one(".listing-title")
        if not title_elem:
            raise ParseError("Missing title element")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> float:
        price_elem = soup.select_one(".price")
        if not price_elem:
            raise ParseError("Missing price element")
        price_str = price_elem.text.strip().replace("$", "").replace(",", "")
        return validate_price(price_str)

    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        location_elem = soup.select_one(".location")
        lat_elem = soup.select_one(".latitude")
        lon_elem = soup.select_one(".longitude")

        if not location_elem or not lat_elem or not lon_elem:
            raise ParseError("Incomplete location data")

        latitude = float(lat_elem.text.strip())
        longitude = float(lon_elem.text.strip())

        if not validate_geospatial_coordinates(latitude, longitude):
            raise ParseError("Invalid geospatial coordinates")

        return {
            "address": location_elem.text.strip(),
            "coordinates": Point(longitude, latitude),
        }

    def _extract_sqft(self, soup: BeautifulSoup) -> int:
        sqft_elem = soup.select_one(".sqft")
        if not sqft_elem:
            return 0  # Default to 0 if missing
        try:
            return int(sqft_elem.text.strip().replace(",", ""))
        except ValueError:
            raise ParseError("Invalid square footage format")

    def _extract_bedrooms(self, soup: BeautifulSoup) -> int:
        bedrooms_elem = soup.select_one(".bedrooms")
        if not bedrooms_elem:
            return 0  # Default to 0 if missing
        try:
            return int(bedrooms_elem.text.strip())
        except ValueError:
            raise ParseError("Invalid bedrooms format")

    def _extract_bathrooms(self, soup: BeautifulSoup) -> float:
        bathrooms_elem = soup.select_one(".bathrooms")
        if not bathrooms_elem:
            return 0.0  # Default to 0 if missing
        try:
            return float(bathrooms_elem.text.strip())
        except ValueError:
            raise ParseError("Invalid bathrooms format")

    def _calculate_fraud_score(self, soup: BeautifulSoup) -> float:
        """
        Calculate a fraud score based on suspicious patterns in the listing.
        Examples:
            - Missing contact info increases score.
            - Unusually low prices significantly increase score.

        Returns:
            float: Fraud score (0 to 100).
        """
        contact_elem = soup.select_one(".contact-info")
        price_elem = soup.select_one(".price")

        fraud_score = 0.0

        # Missing contact info
        if not contact_elem:
            fraud_score += 50.0

        # Unrealistic pricing
        if (
            price_elem
            and float(price_elem.text.strip().replace("$", "").replace(",", "")) < 50000
        ):
            fraud_score += 40.0

        return min(fraud_score, 100.0)

    def validate_lead(self, lead: LeadCreate) -> bool:
        """
        Validate the parsed lead for consistency and completeness.

        Args:
            lead (LeadCreate): Parsed lead object.

        Returns:
            bool: True if the lead passes all validation checks, otherwise False.
        """
        required_fields = ["title", "price", "location"]
        for field in required_fields:
            if not getattr(lead, field):
                return False
        return True

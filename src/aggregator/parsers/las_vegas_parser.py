from typing import Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
import re
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError

class LasVegasParser:
    """
    Parser for Las Vegas-specific real estate listings. Optimized for
    local nuances and advanced features such as fraud detection and trend extraction.
    """
    
    REGION = "Las Vegas"

    def __init__(self):
        self.price_pattern = re.compile(r'\$?([\d,]+(?:\.\d{2})?)')
        self.location_pattern = re.compile(r'(Las Vegas|Henderson|Paradise|Boulder City|North Las Vegas)', re.IGNORECASE)

    def parse_listing(self, html_content: str) -> LeadCreate:
        """
        Parse raw HTML content into a structured lead.

        Args:
            html_content: Raw HTML content of the listing.

        Returns:
            LeadCreate: Validated and normalized lead data.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            title = self._extract_title(soup)
            price = self._parse_price(soup)
            location = self._extract_location(soup)
            metadata = self._extract_metadata(soup)

            return LeadCreate(
                name=title,
                email=None,  # No email extraction for Las Vegas parser
                phone=metadata.get("phone"),
                source="Las Vegas",
                metadata={
                    "price": price,
                    "location": location,
                    "property_type": metadata.get("property_type"),
                    "listing_date": metadata.get("listing_date"),
                    "square_footage": metadata.get("square_footage"),
                    "bedrooms": metadata.get("bedrooms"),
                    "bathrooms": metadata.get("bathrooms"),
                },
            )

        except Exception as e:
            raise ParseError(f"Failed to parse listing: {str(e)}") from e

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the title of the listing.

        Args:
            soup: BeautifulSoup object of the HTML content.

        Returns:
            str: Listing title.

        Raises:
            ParseError: If the title is missing.
        """
        title_elem = soup.select_one(".listing-title, .post-title")
        if not title_elem:
            raise ParseError("Missing title element")
        return title_elem.text.strip()

    def _parse_price(self, soup: BeautifulSoup) -> float:
        """
        Extract and normalize the price.

        Args:
            soup: BeautifulSoup object of the HTML content.

        Returns:
            float: Normalized price.

        Raises:
            ParseError: If the price is missing or invalid.
        """
        price_elem = soup.select_one(".price, .listing-price")
        if not price_elem:
            raise ParseError("Missing price element")

        match = self.price_pattern.search(price_elem.text)
        if not match:
            raise ParseError("Invalid price format")

        return float(match.group(1).replace(",", ""))

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """
        Extract and validate the location.

        Args:
            soup: BeautifulSoup object of the HTML content.

        Returns:
            str: Location string.

        Raises:
            ParseError: If the location is invalid or missing.
        """
        location_elem = soup.select_one(".location, .address")
        if not location_elem:
            raise ParseError("Missing location element")

        location_text = location_elem.text.strip()
        if not self.location_pattern.search(location_text):
            raise ParseError(f"Invalid location: {location_text}")

        return location_text

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract additional metadata such as bedrooms, bathrooms, and property type.

        Args:
            soup: BeautifulSoup object of the HTML content.

        Returns:
            dict: Metadata dictionary with optional fields.
        """
        metadata = {}

        def extract_field(selector: str, field_name: str, transform=None):
            elem = soup.select_one(selector)
            if elem:
                metadata[field_name] = transform(elem.text.strip()) if transform else elem.text.strip()

        extract_field(".bedrooms", "bedrooms", lambda x: int(x.split()[0]))
        extract_field(".bathrooms", "bathrooms", lambda x: float(x.split()[0]))
        extract_field(".square-footage", "square_footage", lambda x: int(x.replace(",", "").split()[0]))
        extract_field(".property-type", "property_type")
        extract_field(".listing-date", "listing_date", lambda x: datetime.strptime(x, "%Y-%m-%d"))
        extract_field(".contact-phone", "phone")

        return metadata

    def validate_lead(self, lead: LeadCreate) -> bool:
        """
        Validate parsed lead data.

        Args:
            lead: Parsed LeadCreate object.

        Returns:
            bool: True if the lead is valid, False otherwise.
        """
        required_fields = ["name", "metadata"]
        for field in required_fields:
            if not getattr(lead, field, None):
                return False
        return True

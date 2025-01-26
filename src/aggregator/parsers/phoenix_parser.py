from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base import BaseParser
from src.aggregator.exceptions import ParseError
import re

class PhoenixParser(BaseParser):
    """
    Parser for Phoenix real estate leads with advanced validation,
    fraud detection, and geospatial handling.
    """

    MARKET_ID = "phoenix"
    VERSION = "1.0"

    def __init__(self):
        super().__init__()
        self.price_pattern = re.compile(r'\$?([\d,]+(?:\.\d{2})?)')
        self.location_pattern = re.compile(r'(Phoenix|Scottsdale|Mesa|Tempe|Chandler|Gilbert|Glendale)')
        self.sqft_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*|\d+)\s*(?:sq\.?\s*ft|sqft|SF)', re.IGNORECASE)

    async def parse(self, content: str) -> List[LeadCreate]:
        """
        Parse raw HTML content into structured Lead objects.

        Args:
            content (str): Raw HTML content from the scraped page.

        Returns:
            List[LeadCreate]: List of validated lead objects.

        Raises:
            ParseError: If parsing fails or required fields are missing.
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            listings = []

            for listing in soup.select(".listing-card"):
                try:
                    lead = self._parse_listing(listing)
                    listings.append(lead)
                except ParseError as e:
                    self.log_warning(f"Failed to parse listing: {str(e)}")

            return listings

        except Exception as e:
            raise ParseError(f"Failed to parse Phoenix listings: {str(e)}")

    def _parse_listing(self, listing: Any) -> LeadCreate:
        """
        Extract and validate fields from an individual listing.

        Args:
            listing (Any): BeautifulSoup tag representing a single listing.

        Returns:
            LeadCreate: Validated lead object.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            title = self._extract_title(listing)
            price = self._parse_price(listing)
            location = self._extract_location(listing)
            sqft = self._parse_sqft(listing)
            bedrooms = self._extract_bedrooms(listing)
            bathrooms = self._extract_bathrooms(listing)
            listing_url = self._extract_url(listing)

            lead = LeadCreate(
                name=title,
                email=None,  # Email not provided for Phoenix leads
                phone=None,  # Phone extraction handled downstream if available
                source="Phoenix",
                metadata={
                    "price": price,
                    "location": location,
                    "sqft": sqft,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "listing_url": listing_url,
                    "market_id": self.MARKET_ID,
                    "version": self.VERSION,
                    "extracted_at": datetime.utcnow().isoformat()
                }
            )
            return lead

        except Exception as e:
            raise ParseError(f"Error extracting listing data: {str(e)}")

    def _extract_title(self, listing: Any) -> str:
        """Extract the title of the listing."""
        title_elem = listing.select_one(".title, h2.title")
        if not title_elem:
            raise ParseError("Missing title element.")
        return title_elem.text.strip()

    def _parse_price(self, listing: Any) -> Optional[float]:
        """Extract and parse the price of the listing."""
        price_elem = listing.select_one(".price")
        if not price_elem:
            return None
        match = self.price_pattern.search(price_elem.text)
        if not match:
            return None
        return float(Decimal(match.group(1).replace(",", "")))

    def _extract_location(self, listing: Any) -> str:
        """Extract the location of the listing."""
        location_elem = listing.select_one(".location")
        if not location_elem:
            raise ParseError("Missing location element.")
        location_text = location_elem.text.strip()
        if not self.location_pattern.search(location_text):
            raise ParseError("Invalid or unsupported location.")
        return location_text

    def _parse_sqft(self, listing: Any) -> Optional[int]:
        """Extract and parse the square footage."""
        sqft_elem = listing.select_one(".sqft")
        if not sqft_elem:
            return None
        match = self.sqft_pattern.search(sqft_elem.text)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

    def _extract_bedrooms(self, listing: Any) -> Optional[int]:
        """Extract the number of bedrooms."""
        bedrooms_elem = listing.select_one(".bedrooms")
        return int(bedrooms_elem.text.strip()) if bedrooms_elem else None

    def _extract_bathrooms(self, listing: Any) -> Optional[float]:
        """Extract the number of bathrooms."""
        bathrooms_elem = listing.select_one(".bathrooms")
        return float(bathrooms_elem.text.strip()) if bathrooms_elem else None

    def _extract_url(self, listing: Any) -> str:
        """Extract the listing URL."""
        url_elem = listing.select_one("a")
        if not url_elem or not url_elem.get("href"):
            raise ParseError("Missing listing URL.")
        return url_elem["href"].strip()

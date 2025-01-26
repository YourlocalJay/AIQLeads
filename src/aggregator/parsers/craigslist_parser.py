from typing import Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_price, validate_location, validate_contact
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class CraigslistParser:
    """
    Parser for Craigslist real estate listings. This parser processes raw HTML content
    and converts it into structured data adhering to the Lead schema.

    Attributes:
        MARKET_ID (str): Identifier for the Craigslist market.
        VERSION (str): Parser version for tracking.
    """

    MARKET_ID = "craigslist"
    VERSION = "2.0"

    def parse(self, content: str) -> LeadCreate:
        """
        Parse raw Craigslist listing content into a validated LeadCreate instance.

        Args:
            content (str): Raw HTML content of the listing.

        Returns:
            LeadCreate: Structured lead data.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            # Extract and validate title
            title = self._extract_title(soup)
            
            # Extract and validate price
            price = self._extract_price(soup)
            
            # Extract and validate location
            location = self._extract_location(soup)
            
            # Extract additional metadata
            metadata = self._extract_metadata(soup)

            # Extract contact information
            contact = self._extract_contact(soup)

            # Build and return the LeadCreate instance
            return LeadCreate(
                title=title,
                price=price,
                location=location,
                metadata=metadata,
                source="Craigslist",
                contact=contact,
                market=self.MARKET_ID,
                parser_version=self.VERSION,
                extracted_at=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Error parsing Craigslist listing: {str(e)}", exc_info=True)
            raise ParseError(f"Error parsing Craigslist listing: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract and validate the listing title."""
        title_elem = soup.select_one(".posting-title")
        if not title_elem:
            raise ParseError("Missing title element.")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extract and validate the listing price."""
        price_elem = soup.select_one(".price")
        if not price_elem:
            raise ParseError("Missing price element.")

        try:
            price = validate_price(price_elem.text)
            return price
        except ValueError as e:
            logger.warning(f"Invalid price format: {price_elem.text}")
            raise ParseError("Invalid price format.") from e

    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract and validate the listing location."""
        location_elem = soup.select_one(".location")
        if not location_elem:
            raise ParseError("Missing location element.")

        try:
            location = validate_location(location_elem.text)
            return location
        except ValueError as e:
            logger.warning(f"Invalid location format: {location_elem.text}")
            raise ParseError("Invalid location format.") from e

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional metadata from the listing."""
        metadata = {}

        # Example: Posting date
        date_elem = soup.select_one(".posting-date")
        if date_elem:
            try:
                metadata["posting_date"] = datetime.strptime(date_elem.text.strip(), "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid posting date format: {date_elem.text}")

        # Example: Property details (bedrooms, bathrooms, sqft)
        details_elem = soup.select_one(".property-details")
        if details_elem:
            metadata["details"] = details_elem.text.strip()

        return metadata

    def _extract_contact(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information from the listing."""
        contact = {}

        email_elem = soup.select_one(".reply-email")
        phone_elem = soup.select_one(".reply-phone")

        if email_elem:
            contact["email"] = validate_contact(email_elem.text, "email")

        if phone_elem:
            contact["phone"] = validate_contact(phone_elem.text, "phone")

        if not contact:
            logger.warning("No contact information found.")

        return contact

if __name__ == "__main__":
    # Example usage for testing
    sample_html = """
    <html>
        <div class='posting-title'>Beautiful Home</div>
        <div class='price'>$250,000</div>
        <div class='location'>Austin, TX</div>
        <div class='reply-email'>contact@example.com</div>
        <div class='reply-phone'>(123) 456-7890</div>
        <div class='posting-date'>2025-01-25</div>
    </html>
    """

    parser = CraigslistParser()
    try:
        lead = parser.parse(sample_html)
        print(lead)
    except ParseError as e:
        print(f"Failed to parse listing: {e}")

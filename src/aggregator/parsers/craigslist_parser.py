from typing import Dict, Any
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_price, validate_date, validate_email
import logging

logger = logging.getLogger(__name__)

class CraigslistParser:
    """
    Parser for Craigslist listings.

    This parser processes raw HTML content from Craigslist listings and converts
    it into structured data adhering to the Lead schema.

    Attributes:
        MARKET_ID (str): Unique identifier for the Craigslist market.
        VERSION (str): Version of the parser.
    """

    MARKET_ID = "craigslist"
    VERSION = "1.0"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def parse_listing(self, content: str) -> Dict[str, Any]:
        """
        Parse raw HTML content into structured lead data.

        This method retries up to 3 times with exponential backoff in case of recoverable errors.

        Args:
            content (str): Raw HTML content of a Craigslist listing.

        Returns:
            Dict[str, Any]: Parsed lead data with fields:
                - title (str)
                - price (float)
                - location (str)
                - posting_date (datetime)
                - contact_info (dict)

        Raises:
            ParseError: If parsing fails after retries.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            # Extract and validate title
            title_elem = soup.select_one(".posting-title")
            if not title_elem:
                raise ParseError("Missing title element.")
            title = title_elem.text.strip()

            # Extract and validate price
            price_elem = soup.select_one(".price")
            price = validate_price(price_elem.text) if price_elem else None
            if price is None:
                raise ParseError("Invalid or missing price.")

            # Extract and validate location
            location_elem = soup.select_one(".location")
            location = location_elem.text.strip() if location_elem else "Unknown"

            # Extract and validate posting date
            date_elem = soup.select_one(".posting-date")
            posting_date = validate_date(date_elem["datetime"], "%Y-%m-%dT%H:%M:%S") if date_elem else None
            if posting_date is None:
                raise ParseError("Invalid or missing posting date.")

            # Extract and validate contact information
            contact_info = self._extract_contact_info(soup)

            return {
                "title": title,
                "price": price,
                "location": location,
                "posting_date": posting_date,
                "contact_info": contact_info,
                "source": "Craigslist",
                "metadata": {
                    "parser_version": self.VERSION,
                    "market_id": self.MARKET_ID,
                    "parsed_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to parse listing: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse listing: {str(e)}")

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract contact information from the listing HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            Dict[str, Any]: Contact information including name, email, and phone.

        Raises:
            ParseError: If contact information cannot be extracted or validated.
        """
        try:
            email_elem = soup.select_one(".reply-email")
            phone_elem = soup.select_one(".reply-phone")

            email = email_elem.text.strip() if email_elem else None
            if email and not validate_email(email):
                raise ParseError("Invalid email format.")

            phone = phone_elem.text.strip() if phone_elem else None
            phone = self._normalize_phone(phone) if phone else None

            return {
                "email": email,
                "phone": phone
            }

        except Exception as e:
            logger.error(f"Failed to extract contact information: {str(e)}")
            raise ParseError(f"Contact extraction failed: {str(e)}")

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """
        Normalize phone number format.

        Args:
            phone (str): Raw phone number.

        Returns:
            str: Normalized phone number.
        """
        return phone.replace("(", "").replace(")", "").replace("-", "").strip()

if __name__ == "__main__":
    # Example usage for testing
    sample_html = """<html><div class='posting-title'>Test Listing</div>
    <div class='price'>$1,200</div>
    <div class='location'>Austin, TX</div>
    <time class='posting-date' datetime='2025-01-25T14:30:00'></time>
    <div class='reply-email'>test@example.com</div>
    <div class='reply-phone'>(123) 456-7890</div></html>"""

    parser = CraigslistParser()
    try:
        parsed_data = parser.parse_listing(sample_html)
        print(parsed_data)
    except ParseError as e:
        print(f"Error: {e}")

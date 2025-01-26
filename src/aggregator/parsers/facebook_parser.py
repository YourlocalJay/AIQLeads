from typing import Dict, Any, List
from datetime import datetime
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class FacebookParser:
    """
    Parser for Facebook Marketplace property listings with robust validation
    and normalization logic.
    """

    @staticmethod
    def parse_listing(raw_html: str) -> List[LeadCreate]:
        """
        Parse raw HTML content from Facebook Marketplace into structured leads.

        Args:
            raw_html (str): The raw HTML content of the Facebook Marketplace page.

        Returns:
            List[LeadCreate]: A list of parsed and validated leads.

        Raises:
            ParseError: If the HTML parsing or lead extraction fails.
        """
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            leads = []

            for item in soup.select("div[data-testid='marketplace_listing']"):
                try:
                    lead = FacebookParser._extract_lead(item)
                    leads.append(lead)
                except ParseError as e:
                    logger.warning(f"Skipping invalid listing: {e}")
                    continue

            if not leads:
                raise ParseError("No valid leads found in the provided HTML.")

            return leads

        except Exception as e:
            logger.error(f"Failed to parse Facebook Marketplace listings: {e}")
            raise ParseError(f"FacebookParser error: {e}")

    @staticmethod
    def _extract_lead(item: Any) -> LeadCreate:
        """
        Extract a single lead from a Facebook Marketplace listing.

        Args:
            item (Any): The HTML element containing the listing details.

        Returns:
            LeadCreate: The extracted and validated lead.

        Raises:
            ParseError: If critical fields are missing or invalid.
        """
        try:
            title_elem = item.select_one("span[dir='auto']")
            price_elem = item.select_one("div[aria-label*='$']")
            location_elem = item.select_one("div[aria-label*='Located in']")
            url_elem = item.select_one("a")

            title = title_elem.text.strip() if title_elem else None
            price = FacebookParser._parse_price(price_elem.text if price_elem else None)
            location = location_elem.text.strip() if location_elem else None
            url = "https://www.facebook.com" + url_elem["href"] if url_elem else None

            if not title or not url:
                raise ParseError("Missing required fields: title or URL.")

            return LeadCreate(
                name=title,
                price=price,
                source="Facebook Marketplace",
                metadata={
                    "location": location,
                    "listing_url": url,
                    "extracted_at": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Failed to extract lead: {e}")
            raise ParseError(f"Lead extraction error: {e}")

    @staticmethod
    def _parse_price(price_str: str) -> Optional[float]:
        """
        Parse and validate the price string.

        Args:
            price_str (str): Raw price string.

        Returns:
            Optional[float]: The parsed price.

        Raises:
            ParseError: If the price cannot be parsed or is invalid.
        """
        try:
            if not price_str:
                return None

            price_str = price_str.replace("$", "").replace(",", "").strip()
            price = float(price_str)

            if price <= 0:
                raise ValueError("Price must be greater than zero.")

            return price

        except ValueError as e:
            logger.warning(f"Invalid price format: {price_str}")
            raise ParseError(f"Price parsing error: {e}")

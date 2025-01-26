from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re
import logging
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone

logger = logging.getLogger(__name__)

class FacebookParser:
    """
    Parser for Facebook Marketplace listings with advanced validation and error handling.
    """

    MARKET_ID = "facebook"
    VERSION = "1.1.0"

    def __init__(self):
        self.price_pattern = re.compile(r"\$?([\d,]+(?:\.\d{2})?)")
        self.phone_pattern = re.compile(r"\(\d{3}\) \d{3}-\d{4}")

    def parse_listing(self, content: str) -> LeadCreate:
        """
        Parse a single Facebook Marketplace listing into a validated LeadCreate instance.

        Args:
            content (str): Raw HTML content of the listing.

        Returns:
            LeadCreate: Validated lead data.

        Raises:
            ParseError: If parsing or validation fails.
        """
        try:
            logger.info("Parsing Facebook Marketplace listing...")
            soup = BeautifulSoup(content, "html.parser")

            title = self._extract_title(soup)
            price = self._extract_price(soup)
            location = self._extract_location(soup)
            contact = self._extract_contact_info(soup)

            metadata = {
                "market": self.MARKET_ID,
                "parser_version": self.VERSION,
                "extracted_at": datetime.utcnow().isoformat(),
            }

            lead = LeadCreate(
                name=contact["name"],
                email=contact.get("email"),
                phone=contact.get("phone"),
                price=price,
                location=location,
                source="Facebook",
                metadata=metadata,
            )

            self._validate_lead(lead)
            logger.info(f"Parsed lead: {lead}")

            return lead

        except Exception as e:
            logger.error(f"Failed to parse Facebook listing: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse Facebook listing: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_elem = soup.select_one(".title")
        if not title_elem:
            raise ParseError("Missing title element.")
        return title_elem.text.strip()

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        price_elem = soup.select_one(".price")
        if not price_elem:
            raise ParseError("Missing price element.")

        match = self.price_pattern.search(price_elem.text)
        if not match:
            raise ParseError("Invalid price format.")

        return float(match.group(1).replace(",", ""))

    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        location_elem = soup.select_one(".location")
        if not location_elem:
            raise ParseError("Missing location element.")

        location_text = location_elem.text.strip()
        return {"address": location_text}

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
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

    def _validate_lead(self, lead: LeadCreate) -> None:
        """
        Perform additional validation on the parsed lead.

        Args:
            lead (LeadCreate): Parsed lead.

        Raises:
            ParseError: If validation fails.
        """
        if not lead.price or lead.price <= 0:
            raise ParseError("Lead price must be greater than zero.")

        if not lead.location or not lead.location.get("address"):
            raise ParseError("Location data is missing or incomplete.")

    def parse_multiple_listings(self, listings: List[str]) -> List[LeadCreate]:
        """
        Parse multiple Facebook listings into a list of LeadCreate instances.

        Args:
            listings (List[str]): List of raw HTML content strings.

        Returns:
            List[LeadCreate]: Parsed leads.
        """
        parsed_leads = []
        for content in listings:
            try:
                lead = self.parse_listing(content)
                parsed_leads.append(lead)
            except ParseError as e:
                logger.warning(f"Skipping invalid listing: {str(e)}")
                continue
        return parsed_leads

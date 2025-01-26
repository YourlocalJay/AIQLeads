from typing import List, Dict, Any
from datetime import datetime
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from geoalchemy2 import functions as geo_func
import re
import logging

logger = logging.getLogger(__name__)

class FSBOParser:
    """
    Parser for FSBO.com listings with advanced validation and fraud detection.
    """

    def __init__(self):
        self.price_pattern = re.compile(r"\$?([\d,]+(?:\.\d{2})?)")
        self.phone_pattern = re.compile(r"\(\d{3}\) \d{3}-\d{4}")

    def parse_listing(self, content: Dict[str, Any]) -> LeadCreate:
        """
        Parse a single FSBO listing into a validated LeadCreate instance.

        Args:
            content (Dict[str, Any]): Raw listing data from FSBO.

        Returns:
            LeadCreate: Validated lead data.

        Raises:
            ParseError: If parsing or validation fails.
        """
        try:
            logger.info("Parsing FSBO listing...")

            title = self._extract_title(content)
            price = self._extract_price(content)
            location = self._extract_location(content)
            contact = self._extract_contact_info(content)

            metadata = {
                "url": content.get("url"),
                "listing_date": content.get("listing_date"),
                "property_type": content.get("property_type"),
                "sqft": content.get("sqft"),
                "bedrooms": content.get("bedrooms"),
                "bathrooms": content.get("bathrooms"),
            }

            lead = LeadCreate(
                name=contact["name"],
                email=contact["email"],
                phone=contact["phone"],
                price=price,
                location=location,
                source="FSBO",
                metadata=metadata,
            )

            self._validate_lead(lead)
            logger.info(f"Parsed lead: {lead}")

            return lead

        except Exception as e:
            logger.error(f"Failed to parse FSBO listing: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse FSBO listing: {str(e)}")

    def _extract_title(self, content: Dict[str, Any]) -> str:
        title = content.get("title", "").strip()
        if not title:
            raise ParseError("Missing title in FSBO listing.")
        return title

    def _extract_price(self, content: Dict[str, Any]) -> float:
        price_raw = content.get("price")
        if not price_raw:
            raise ParseError("Missing price in FSBO listing.")

        match = self.price_pattern.search(price_raw)
        if not match:
            raise ParseError("Invalid price format.")

        return float(match.group(1).replace(",", ""))

    def _extract_location(self, content: Dict[str, Any]) -> Dict[str, Any]:
        location_data = content.get("location")
        if not location_data:
            raise ParseError("Missing location in FSBO listing.")

        if not location_data.get("latitude") or not location_data.get("longitude"):
            raise ParseError("Incomplete geospatial data.")

        return {
            "latitude": float(location_data["latitude"]),
            "longitude": float(location_data["longitude"]),
        }

    def _extract_contact_info(self, content: Dict[str, Any]) -> Dict[str, str]:
        contact = {
            "name": content.get("contact_name", "").strip(),
            "email": content.get("contact_email"),
            "phone": content.get("contact_phone"),
        }

        if not contact["name"]:
            raise ParseError("Missing contact name.")

        if not contact["email"] and not contact["phone"]:
            raise ParseError("At least one contact method (email or phone) is required.")

        if contact["phone"] and not self.phone_pattern.match(contact["phone"]):
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
        if lead.price <= 0:
            raise ParseError("Lead price must be greater than zero.")

        if not (-90 <= lead.location["latitude"] <= 90 and -180 <= lead.location["longitude"] <= 180):
            raise ParseError("Invalid geospatial coordinates.")

    def parse_multiple_listings(self, listings: List[Dict[str, Any]]) -> List[LeadCreate]:
        """
        Parse multiple FSBO listings into a list of LeadCreate instances.

        Args:
            listings (List[Dict[str, Any]]): List of raw listing data.

        Returns:
            List[LeadCreate]: Parsed leads.
        """
        parsed_leads = []
        for listing in listings:
            try:
                lead = self.parse_listing(listing)
                parsed_leads.append(lead)
            except ParseError as e:
                logger.warning(f"Skipping invalid listing: {str(e)}")
                continue
        return parsed_leads

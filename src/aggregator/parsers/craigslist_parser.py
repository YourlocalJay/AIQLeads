from typing import Dict, Any, Optional
from datetime import datetime
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
from geoalchemy2.shape import to_shape
import logging

logger = logging.getLogger(__name__)

class CraigslistParser:
    """
    Parses raw Craigslist listing data into structured LeadCreate objects.
    """

    REQUIRED_FIELDS = ["title", "price", "location"]

    def parse_listing(self, raw_data: Dict[str, Any]) -> LeadCreate:
        """
        Parses a single Craigslist listing.

        Args:
            raw_data: Raw JSON or dictionary representing a Craigslist listing.

        Returns:
            LeadCreate: A validated lead object ready for database storage.

        Raises:
            ParseError: If required fields are missing or invalid.
        """
        try:
            self._validate_required_fields(raw_data)

            title = raw_data.get("title", "").strip()
            price = self._parse_price(raw_data.get("price"))
            location = self._parse_location(raw_data.get("location"))
            description = raw_data.get("description", "").strip()
            contact_info = self._extract_contact_info(raw_data)

            lead = LeadCreate(
                name=title,
                email=contact_info.get("email"),
                phone=contact_info.get("phone"),
                source="Craigslist",
                metadata={
                    "description": description,
                    "price": price,
                    "location": location,
                    "posting_date": raw_data.get("posting_date"),
                    "listing_url": raw_data.get("url"),
                    "extracted_at": datetime.utcnow().isoformat(),
                }
            )

            return lead

        except Exception as e:
            logger.error(f"Error parsing Craigslist listing: {str(e)}")
            raise ParseError(f"Parsing failed for Craigslist listing: {str(e)}")

    def _validate_required_fields(self, raw_data: Dict[str, Any]) -> None:
        """
        Validates that all required fields are present in the raw data.

        Args:
            raw_data: Raw JSON or dictionary representing a Craigslist listing.

        Raises:
            ParseError: If required fields are missing.
        """
        missing_fields = [field for field in self.REQUIRED_FIELDS if not raw_data.get(field)]
        if missing_fields:
            raise ParseError(f"Missing required fields: {', '.join(missing_fields)}")

    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Parses the price field, converting it to a float if valid.

        Args:
            price_str: Raw price string from the listing.

        Returns:
            Optional[float]: Parsed price as a float, or None if invalid.

        Raises:
            ParseError: If the price format is invalid.
        """
        if not price_str:
            return None

        try:
            cleaned_price = price_str.replace("$", "").replace(",", "").strip()
            return float(cleaned_price)
        except ValueError:
            raise ParseError(f"Invalid price format: {price_str}")

    def _parse_location(self, location_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """
        Extracts and validates location coordinates.

        Args:
            location_data: Dictionary containing location details (latitude and longitude).

        Returns:
            Optional[Dict[str, float]]: A dictionary with 'latitude' and 'longitude' keys.

        Raises:
            ParseError: If location data is missing or invalid.
        """
        if not location_data:
            raise ParseError("Location data is missing.")

        try:
            lat = float(location_data["latitude"])
            lng = float(location_data["longitude"])
            return {"latitude": lat, "longitude": lng}
        except (KeyError, ValueError):
            raise ParseError("Invalid location data format.")

    def _extract_contact_info(self, raw_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Extracts contact information from the listing data.

        Args:
            raw_data: Raw JSON or dictionary representing a Craigslist listing.

        Returns:
            Dict[str, Optional[str]]: A dictionary containing 'email' and 'phone'.

        Raises:
            ParseError: If contact information is missing or invalid.
        """
        contact_info = {
            "email": raw_data.get("contact_email"),
            "phone": raw_data.get("contact_phone"),
        }

        if not contact_info["email"] and not contact_info["phone"]:
            raise ParseError("Contact information is missing.")

        return contact_info

    def validate_lead(self, lead: LeadCreate) -> bool:
        """
        Validates a LeadCreate object for completeness and correctness.

        Args:
            lead: The LeadCreate object to validate.

        Returns:
            bool: True if the lead is valid.

        Raises:
            ParseError: If validation fails.
        """
        if not lead.name or not lead.metadata.get("price") or not lead.metadata.get("location"):
            raise ParseError("Lead validation failed: Missing critical fields.")

        return True

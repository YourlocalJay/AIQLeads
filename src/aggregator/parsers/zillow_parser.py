from typing import Dict, Any, List
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ZillowParser:
    """
    Parser for Zillow listings with robust validation and data cleaning.
    """

    @staticmethod
    def parse_listing(listing_data: Dict[str, Any]) -> LeadCreate:
        """
        Parse a single Zillow listing into a structured LeadCreate object.

        Args:
            listing_data: Raw listing data from Zillow.

        Returns:
            LeadCreate: A validated and structured lead object.

        Raises:
            ParseError: If any required field is missing or invalid.
        """
        try:
            # Extract and validate essential fields
            title = ZillowParser._validate_field(listing_data, "title", str)
            price = ZillowParser._parse_price(listing_data.get("price"))
            location = ZillowParser._validate_field(listing_data, "location", dict)
            bedrooms = ZillowParser._parse_bedrooms(listing_data.get("bedrooms"))
            bathrooms = ZillowParser._parse_bathrooms(listing_data.get("bathrooms"))
            square_footage = ZillowParser._parse_square_footage(listing_data.get("sqft"))
            contact_info = ZillowParser._extract_contact_info(listing_data)

            # Build LeadCreate object
            lead = LeadCreate(
                name=title,
                email=contact_info.get("email"),
                phone=contact_info.get("phone"),
                source="Zillow",
                metadata={
                    "price": price,
                    "location": location,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "square_footage": square_footage,
                    "listing_url": listing_data.get("url"),
                    "extracted_at": datetime.utcnow().isoformat(),
                },
            )
            return lead

        except Exception as e:
            logger.error(f"Failed to parse Zillow listing: {str(e)}")
            raise ParseError(f"Error parsing Zillow listing: {str(e)}")

    @staticmethod
    def _validate_field(data: Dict[str, Any], field_name: str, expected_type: type) -> Any:
        """
        Validate a required field exists and matches the expected type.

        Args:
            data: The raw listing data.
            field_name: The field name to validate.
            expected_type: The expected type of the field.

        Returns:
            The validated field value.

        Raises:
            ParseError: If the field is missing or invalid.
        """
        value = data.get(field_name)
        if not isinstance(value, expected_type):
            raise ParseError(f"Missing or invalid field '{field_name}': Expected {expected_type}, got {type(value)}")
        return value

    @staticmethod
    def _parse_price(price_str: str) -> float:
        """
        Parse and validate the price field.

        Args:
            price_str: Raw price string.

        Returns:
            The parsed price as a float.

        Raises:
            ParseError: If the price is missing or invalid.
        """
        try:
            price = float(price_str.replace("$", "").replace(",", ""))
            if price <= 0:
                raise ValueError("Price must be greater than zero.")
            return price
        except Exception as e:
            raise ParseError(f"Invalid price format: {str(e)}")

    @staticmethod
    def _parse_bedrooms(bedrooms: Any) -> int:
        """
        Parse and validate the number of bedrooms.

        Args:
            bedrooms: Raw bedrooms data.

        Returns:
            The number of bedrooms as an integer.

        Raises:
            ParseError: If the data is invalid.
        """
        try:
            return int(bedrooms)
        except Exception:
            raise ParseError("Invalid bedrooms value.")

    @staticmethod
    def _parse_bathrooms(bathrooms: Any) -> float:
        """
        Parse and validate the number of bathrooms.

        Args:
            bathrooms: Raw bathrooms data.

        Returns:
            The number of bathrooms as a float.

        Raises:
            ParseError: If the data is invalid.
        """
        try:
            return float(bathrooms)
        except Exception:
            raise ParseError("Invalid bathrooms value.")

    @staticmethod
    def _parse_square_footage(sqft: Any) -> Optional[int]:
        """
        Parse and validate the square footage.

        Args:
            sqft: Raw square footage data.

        Returns:
            The square footage as an integer or None if unavailable.
        """
        if not sqft:
            return None
        try:
            return int(sqft.replace(",", ""))
        except Exception:
            raise ParseError("Invalid square footage value.")

    @staticmethod
    def _extract_contact_info(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract and validate contact information.

        Args:
            data: The raw listing data.

        Returns:
            A dictionary containing email and phone information.

        Raises:
            ParseError: If contact info is invalid.
        """
        email = data.get("email")
        phone = data.get("phone")

        if not email and not phone:
            raise ParseError("Missing contact information: At least one of email or phone is required.")

        return {
            "email": email,
            "phone": phone,
        }

    def __repr__(self) -> str:
        return "<ZillowParser>"

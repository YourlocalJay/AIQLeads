from typing import List, Dict, Any
from datetime import datetime
from src.schemas.lead_schema import LeadCreate
from src.aggregator.exceptions import ParseError
import logging

logger = logging.getLogger(__name__)

class LinkedInParser:
    """
    Parses LinkedIn scraped data into structured leads.
    Handles advanced normalization, validation, and schema transformations.
    """

    REQUIRED_FIELDS = ["name", "title", "profile_url", "company"]

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[LeadCreate]:
        """
        Parse raw LinkedIn listing data into validated LeadCreate instances.

        Args:
            raw_data: List of raw dictionaries from LinkedIn scraper.

        Returns:
            List[LeadCreate]: Validated and normalized lead instances.

        Raises:
            ParseError: If parsing or validation fails.
        """
        logger.info(f"Parsing {len(raw_data)} LinkedIn listings.")
        leads = []

        for listing in raw_data:
            try:
                lead = self._parse_single_listing(listing)
                leads.append(lead)
            except ParseError as e:
                logger.warning(f"Skipping listing due to error: {str(e)}")
                continue

        logger.info(f"Successfully parsed {len(leads)} leads.")
        return leads

    def _parse_single_listing(self, listing: Dict[str, Any]) -> LeadCreate:
        """
        Parse and validate a single LinkedIn listing.

        Args:
            listing: Raw LinkedIn listing data.

        Returns:
            LeadCreate: Validated and normalized lead instance.

        Raises:
            ParseError: If required fields are missing or validation fails.
        """
        self._validate_required_fields(listing)

        try:
            lead = LeadCreate(
                name=listing.get("name", "Unknown").strip(),
                email=self._extract_email(listing.get("contact_info", {})),
                phone=self._normalize_phone(listing.get("contact_info", {}).get("phone")),
                source="LinkedIn",
                metadata={
                    "profile_url": listing["profile_url"],
                    "company": listing["company"],
                    "title": listing["title"],
                    "extracted_at": datetime.utcnow(),
                },
            )
            return lead

        except Exception as e:
            raise ParseError(f"Failed to parse listing: {str(e)}")

    def _validate_required_fields(self, listing: Dict[str, Any]) -> None:
        """
        Validate that all required fields are present in the listing.

        Args:
            listing: Raw LinkedIn listing data.

        Raises:
            ParseError: If required fields are missing.
        """
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in listing or not listing[field]]
        if missing_fields:
            raise ParseError(f"Missing required fields: {', '.join(missing_fields)}")

    @staticmethod
    def _extract_email(contact_info: Dict[str, Any]) -> str:
        """
        Extract and validate email from contact info.

        Args:
            contact_info: Dictionary containing contact details.

        Returns:
            str: Validated email address.

        Raises:
            ParseError: If email is invalid.
        """
        email = contact_info.get("email")
        if email and "@" in email:
            return email.strip()
        raise ParseError("Invalid or missing email.")

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """
        Normalize phone number format.

        Args:
            phone: Raw phone number string.

        Returns:
            str: Normalized phone number.
        """
        if not phone:
            return ""

        # Example normalization: remove non-numeric characters
        return "".join(filter(str.isdigit, phone))

# Example usage
if __name__ == "__main__":
    parser = LinkedInParser()
    sample_data = [
        {
            "name": "John Doe",
            "title": "Real Estate Agent",
            "profile_url": "https://linkedin.com/in/johndoe",
            "company": "ABC Realty",
            "contact_info": {
                "email": "johndoe@example.com",
                "phone": "(555) 123-4567",
            },
        }
    ]
    leads = parser.parse(sample_data)
    for lead in leads:
        print(lead)

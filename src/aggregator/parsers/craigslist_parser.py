"""
Craigslist data parser with enhanced validation and optimization.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from geoalchemy2.elements import WKTElement
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone, validate_price
from src.utils.text_processor import clean_text, extract_phone_numbers

logger = logging.getLogger(__name__)

class CraigslistParser(BaseParser):
    """
    Optimized parser for Craigslist listings with enhanced validation
    and text processing capabilities.
    """

    MARKET_ID = "craigslist"
    VERSION = "2.1"

    async def parse_async(self, data: Dict[str, Any]) -> LeadCreate:
        """
        Parse Craigslist listing data with advanced validation.

        Args:
            data: Raw listing data from Craigslist API

        Returns:
            LeadCreate: Validated lead object
        """
        try:
            listing_id = data.get('id')
            contact = await self._extract_contact_info(data)
            location = self._extract_location(data)
            price = self._extract_price(data)
            
            description = clean_text(data.get('description', ''))
            
            # Enhanced metadata extraction
            metadata = {
                "title": data.get("title"),
                "price": price,
                "posting_date": data.get("created"),
                "category": data.get("category"),
                "subcategory": data.get("subcategory"),
                "fraud_score": self._calculate_fraud_score(data, description),
                "extracted_at": datetime.utcnow().isoformat(),
                "parser_version": self.VERSION,
                "attributes": self._extract_attributes(data),
                "keywords": self._extract_keywords(description)
            }

            lead = LeadCreate(
                source_id=listing_id,
                market=self.MARKET_ID,
                contact_name=contact.get("name", "Unknown"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                company_name=contact.get("company_name", "Individual"),
                location=location,
                metadata=metadata
            )

            await self._validate_lead(lead)
            return lead

        except Exception as e:
            logger.error(f"Failed to parse Craigslist listing {data.get('id')}: {e}", exc_info=True)
            raise ParseError(f"Failed to parse Craigslist listing: {str(e)}")

    async def _extract_contact_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate contact information with enhanced phone extraction."""
        contact = {
            'name': data.get('contact_name', 'Unknown'),
            'email': data.get('from_email'),
            'phone': None,
            'company_name': None
        }

        # Enhanced phone number extraction from description
        if not contact['phone'] and data.get('description'):
            phones = extract_phone_numbers(data['description'])
            if phones:
                contact['phone'] = phones[0]  # Use first valid phone number

        # Validate contact information
        if contact['email']:
            contact['email'] = contact['email'].lower()
            if not validate_email(contact['email']):
                contact['email'] = None

        if contact['phone'] and not validate_phone(contact['phone']):
            contact['phone'] = None

        if not (contact['email'] or contact['phone']):
            raise ParseError("No valid contact information found")

        return contact

    def _extract_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate location data with enhanced geocoding."""
        try:
            lat = data.get('geolocation', {}).get('lat')
            lon = data.get('geolocation', {}).get('lon')
            
            if not (lat and lon):
                raise ValueError("Missing coordinates")

            return {
                "coordinates": WKTElement(f"POINT({lon} {lat})", srid=4326),
                "address": data.get('address'),
                "neighborhood": data.get('neighborhood'),
                "city": data.get('city'),
                "state": data.get('state'),
                "raw_data": data.get('geolocation', {})
            }

        except Exception as e:
            logger.warning(f"Location extraction failed: {e}")
            raise ParseError(f"Invalid location data: {str(e)}")

    def _extract_price(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract and validate price with enhanced parsing."""
        try:
            price_str = data.get('price', '')
            if not price_str:
                return None
                
            # Remove currency symbols and normalize
            price_str = ''.join(c for c in price_str if c.isdigit() or c == '.')
            price = float(price_str)
            
            return validate_price(price)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Price extraction failed: {e}")
            return None

    def _extract_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract listing attributes with validation."""
        attributes = {}
        
        if 'attributes' in data:
            for attr in data['attributes']:
                key = attr.get('key', '').lower()
                value = attr.get('value')
                if key and value:
                    attributes[key] = value

        return attributes

    def _extract_keywords(self, description: str) -> List[str]:
        """Extract relevant keywords from description."""
        # Implement keyword extraction logic
        keywords = []
        # Add implementation
        return keywords

    def _calculate_fraud_score(self, data: Dict[str, Any], description: str) -> float:
        """Calculate fraud risk score based on listing characteristics."""
        score = 0.0

        # Price analysis
        price = self._extract_price(data)
        if price:
            if price < 100:
                score += 30.0
            elif price > 1000000:
                score += 15.0

        # Description analysis
        if len(description) < 50:
            score += 20.0

        # Contact information completeness
        if not data.get('from_email'):
            score += 10.0

        # Location accuracy
        if not data.get('geolocation'):
            score += 15.0

        # Add more fraud detection rules

        return min(score, 100.0)

    async def _validate_lead(self, lead: LeadCreate) -> None:
        """Perform comprehensive lead validation."""
        if not lead.source_id:
            raise ParseError("Missing listing ID")

        if not lead.location:
            raise ParseError("Invalid location data")

        if lead.metadata.get('fraud_score', 0) > 80:
            raise ParseError("Lead failed fraud detection")

        if not lead.email and not lead.phone:
            raise ParseError("No valid contact methods")
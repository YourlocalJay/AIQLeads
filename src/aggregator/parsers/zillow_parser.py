"""
Zillow data parser optimized for GraphQL API responses.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from geoalchemy2.elements import WKTElement
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone, validate_price

logger = logging.getLogger(__name__)

class ZillowParser(BaseParser):
    """
    Parser for Zillow GraphQL API responses with enhanced validation,
    geospatial support, and fraud detection.
    """

    MARKET_ID = "zillow"
    VERSION = "2.1"

    async def parse_async(self, data: Dict[str, Any]) -> LeadCreate:
        """
        Parse Zillow GraphQL response data into a structured LeadCreate object.

        Args:
            data (Dict[str, Any]): GraphQL response data for a single listing

        Returns:
            LeadCreate: Parsed lead object

        Raises:
            ParseError: If parsing fails or required fields are missing
        """
        try:
            # Extract core listing data
            listing_id = data.get('id')
            price = self._extract_price(data)
            location = self._extract_location(data)
            contact = await self._extract_contact_info(data)
            
            # Calculate risk metrics
            fraud_score = self._calculate_fraud_score(
                price=price,
                property_type=data.get('propertyType'),
                days_on_market=data.get('daysOnZillow'),
                contact=contact
            )

            lead = LeadCreate(
                source_id=listing_id,
                market=self.MARKET_ID,
                contact_name=contact.get("name", "Unknown"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                company_name=contact.get("company_name", "FSBO"),
                location=location,
                metadata={
                    "property_type": data.get("propertyType"),
                    "price": price,
                    "days_on_market": data.get("daysOnZillow"),
                    "fraud_score": fraud_score,
                    "is_fsbo": data.get("isFSBO", False),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "parser_version": self.VERSION
                }
            )

            await self._validate_lead(lead)
            return lead

        except Exception as e:
            logger.error(f"Failed to parse Zillow listing {data.get('id')}: {e}", exc_info=True)
            raise ParseError(f"Failed to parse Zillow listing: {str(e)}")

    def _extract_price(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract and validate price from listing data."""
        price = data.get('price')
        if price is not None:
            try:
                return validate_price(price)
            except ValueError as e:
                logger.warning(f"Invalid price format: {price}")
                raise ParseError(f"Invalid price format: {str(e)}")
        return None

    def _extract_location(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate location data."""
        location_data = data.get('location', {})
        
        try:
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')

            if latitude is None or longitude is None:
                raise ValueError("Missing geospatial coordinates")

            return {
                "coordinates": WKTElement(f"POINT({longitude} {latitude})", srid=4326),
                "raw_data": location_data
            }

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid location data: {e}")
            raise ParseError(f"Invalid location data: {str(e)}")

    async def _extract_contact_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate contact information."""
        contact = {}
        
        # Handle agent data
        if 'agent' in data:
            agent_data = data['agent']
            contact.update({
                'name': agent_data.get('name'),
                'company_name': agent_data.get('brokerName'),
                'phone': agent_data.get('phoneNumber'),
                'email': agent_data.get('email')
            })
        
        # Handle FSBO data
        if data.get('isFSBO') and 'owner' in data:
            owner_data = data['owner']
            contact.update({
                'name': owner_data.get('name'),
                'phone': owner_data.get('phoneNumber'),
                'email': owner_data.get('email'),
                'company_name': 'FSBO'
            })

        # Validate contact data
        if contact.get('email'):
            if not validate_email(contact['email']):
                logger.warning(f"Invalid email format: {contact['email']}")
                contact['email'] = None

        if contact.get('phone'):
            if not validate_phone(contact['phone']):
                logger.warning(f"Invalid phone format: {contact['phone']}")
                contact['phone'] = None

        if not contact.get('email') and not contact.get('phone'):
            raise ParseError("No valid contact information available")

        return contact

    def _calculate_fraud_score(
        self,
        price: Optional[float],
        property_type: Optional[str],
        days_on_market: Optional[int],
        contact: Dict[str, Any]
    ) -> float:
        """Calculate fraud risk score based on listing attributes."""
        score = 0.0

        # Contact information checks
        if not contact.get('email') or not contact.get('phone'):
            score += 20.0

        # Price anomaly checks
        if price:
            if price < 50000:
                score += 30.0
            elif price > 10000000:
                score += 15.0

        # Listing duration checks
        if days_on_market and days_on_market < 1:
            score += 10.0

        # Property type validation
        if not property_type:
            score += 5.0

        return min(score, 100.0)

    async def _validate_lead(self, lead: LeadCreate) -> None:
        """
        Perform comprehensive validation on the parsed lead.

        Args:
            lead (LeadCreate): Parsed lead object

        Raises:
            ParseError: If validation fails
        """
        if not lead.source_id:
            raise ParseError("Missing listing ID")

        if not lead.location:
            raise ParseError("Invalid or missing location data")

        if lead.metadata.get('fraud_score', 0) > 80:
            raise ParseError("Lead failed fraud detection checks")

        # Ensure either email or phone is present
        if not lead.email and not lead.phone:
            raise ParseError("No valid contact methods available")

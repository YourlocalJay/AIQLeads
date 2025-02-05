"""
FSBO (For Sale By Owner) parser with enhanced validation and optimization.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from geoalchemy2.elements import WKTElement
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_price
from src.utils.optimization import ResultCache
from src.utils.performance import PerformanceOptimizer

logger = logging.getLogger(__name__)


class FSBOParser(BaseParser):
    """
    Optimized parser for FSBO listings with enhanced validation
    and performance monitoring.
    """

    MARKET_ID = "fsbo"
    VERSION = "2.1"

    def __init__(self):
        super().__init__()
        self.result_cache = ResultCache(ttl_seconds=1800)
        self.performance_optimizer = PerformanceOptimizer()

    async def parse_async(self, data: Dict[str, Any]) -> LeadCreate:
        """Parse FSBO listing with performance monitoring."""
        return await self.performance_optimizer.optimize_operation(
            "fsbo_parse", self._parse_listing, data
        )

    async def _parse_listing(self, data: Dict[str, Any]) -> LeadCreate:
        """Core parsing logic with optimization."""
        try:
            cache_key = f"fsbo_{data.get('id')}_{self.VERSION}"
            cached_result = await self.result_cache.get(cache_key)
            if cached_result:
                return cached_result

            listing_id = data.get("id")
            contact = await self._extract_contact_info(data)
            location = self._extract_location(data)
            price = self._extract_price(data)
            property_details = self._extract_property_details(data)

            metadata = {
                "price": price,
                "property_details": property_details,
                "listing_date": data.get("created_at"),
                "last_updated": data.get("updated_at"),
                "verification_score": await self._calculate_verification_score(data),
                "source_platform": data.get("source_platform"),
                "extracted_at": datetime.utcnow().isoformat(),
                "parser_version": self.VERSION,
                "property_features": self._extract_property_features(data),
                "seller_motivation": self._analyze_seller_motivation(data),
            }

            lead = LeadCreate(
                source_id=listing_id,
                market=self.MARKET_ID,
                contact_name=contact.get("name", "Owner"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                company_name="FSBO",
                location=location,
                metadata=metadata,
            )

            await self._validate_lead(lead)
            await self.result_cache.set(cache_key, lead)
            return lead

        except Exception as e:
            logger.error(
                f"Failed to parse FSBO listing {data.get('id')}: {e}", exc_info=True
            )
            raise ParseError(f"Failed to parse FSBO listing: {str(e)}")

    def _extract_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate location data."""
        try:
            location_data = data.get("location", {})
            lat = location_data.get("latitude")
            lon = location_data.get("longitude")

            if not (lat and lon):
                raise ValueError("Missing coordinates")

            return {
                "coordinates": WKTElement(f"POINT({lon} {lat})", srid=4326),
                "street_address": location_data.get("street_address"),
                "unit": location_data.get("unit"),
                "city": location_data.get("city"),
                "state": location_data.get("state"),
                "postal_code": location_data.get("postal_code"),
                "raw_data": location_data,
            }

        except Exception as e:
            logger.warning(f"Location extraction failed: {e}")
            raise ParseError(f"Invalid location data: {str(e)}")

    def _extract_price(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract and validate price information."""
        try:
            price_data = data.get("price", {})
            amount = price_data.get("amount")

            if not amount:
                return None

            return validate_price(amount)

        except (ValueError, TypeError) as e:
            logger.warning(f"Price extraction failed: {e}")
            return None

    def _extract_property_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive property details."""
        property_data = data.get("property", {})
        return {
            "type": property_data.get("property_type"),
            "bedrooms": property_data.get("bedrooms"),
            "bathrooms": property_data.get("bathrooms"),
            "square_feet": property_data.get("square_feet"),
            "lot_size": property_data.get("lot_size"),
            "year_built": property_data.get("year_built"),
            "zoning": property_data.get("zoning"),
            "parking": property_data.get("parking"),
            "construction_type": property_data.get("construction_type"),
        }

    def _extract_property_features(self, data: Dict[str, Any]) -> List[str]:
        """Extract and normalize property features."""
        features = data.get("property", {}).get("features", [])
        return [feature.lower().strip() for feature in features if feature]

    def _analyze_seller_motivation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze seller motivation factors."""
        description = data.get("description", "").lower()
        motivation_indicators = {
            "urgent_sale": any(
                term in description for term in ["urgent", "quick sale", "must sell"]
            ),
            "relocation": any(
                term in description for term in ["relocating", "moving", "transfer"]
            ),
            "investment": any(
                term in description for term in ["investment", "rental", "income"]
            ),
            "renovation": any(
                term in description for term in ["as-is", "fixer", "needs work"]
            ),
        }

        days_on_market = data.get("days_on_market", 0)
        price_changes = data.get("price_history", [])

        return {
            "indicators": motivation_indicators,
            "days_on_market": days_on_market,
            "price_changes": len(price_changes),
            "motivation_score": self._calculate_motivation_score(
                motivation_indicators, days_on_market, price_changes
            ),
        }

    def _calculate_motivation_score(
        self, indicators: Dict[str, bool], days_on_market: int, price_changes: List[Any]
    ) -> float:
        """Calculate seller motivation score."""
        score = 0.0

        # Indicator scoring
        score += sum(20.0 for indicator in indicators.values() if indicator)

        # Time on market scoring
        if days_on_market > 90:
            score += 25.0
        elif days_on_market > 60:
            score += 15.0
        elif days_on_market > 30:
            score += 10.0

        # Price change scoring
        if len(price_changes) >= 2:
            score += 25.0
        elif len(price_changes) == 1:
            score += 15.0

        return min(score, 100.0)

    async def _calculate_verification_score(self, data: Dict[str, Any]) -> float:
        """Calculate listing verification score."""
        score = 100.0
        deductions = []

        # Contact verification
        if not (
            data.get("owner", {}).get("email") or data.get("owner", {}).get("phone")
        ):
            deductions.append(30.0)

        # Property details completeness
        property_data = data.get("property", {})
        if not all(
            [
                property_data.get("property_type"),
                property_data.get("square_feet"),
                property_data.get("bedrooms"),
            ]
        ):
            deductions.append(20.0)

        # Image verification
        if not data.get("images", []):
            deductions.append(15.0)

        # Location verification
        if not data.get("location", {}).get("coordinates"):
            deductions.append(20.0)

        # Description quality
        description = data.get("description", "")
        if len(description) < 100:
            deductions.append(15.0)

        return max(0.0, score - sum(deductions))

    async def _validate_lead(self, lead: LeadCreate) -> None:
        """Perform comprehensive lead validation."""
        if not lead.source_id:
            raise ParseError("Missing listing ID")

        if not lead.location:
            raise ParseError("Invalid location data")

        if lead.metadata.get("verification_score", 0) < 40:
            raise ParseError("Lead failed verification checks")

        if not (lead.email or lead.phone):
            raise ParseError("No valid contact methods")

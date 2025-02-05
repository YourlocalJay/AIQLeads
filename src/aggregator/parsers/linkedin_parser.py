"""
LinkedIn parser with enhanced validation and performance optimization.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from geoalchemy2.elements import WKTElement
from src.schemas.lead_schema import LeadCreate
from src.aggregator.parsers.base_parser import BaseParser
from src.aggregator.exceptions import ParseError
from src.utils.validators import validate_email, validate_phone, validate_price
from src.utils.optimization import ResultCache
from src.utils.performance import PerformanceOptimizer

logger = logging.getLogger(__name__)


class LinkedInParser(BaseParser):
    """
    Optimized parser for LinkedIn data with enhanced validation
    and performance monitoring.
    """

    MARKET_ID = "linkedin"
    VERSION = "2.1"

    def __init__(self):
        super().__init__()
        self.result_cache = ResultCache(ttl_seconds=3600)
        self.performance_optimizer = PerformanceOptimizer()

    async def parse_async(self, data: Dict[str, Any]) -> LeadCreate:
        """Parse LinkedIn listing with performance monitoring."""
        return await self.performance_optimizer.optimize_operation(
            "linkedin_parse", self._parse_listing, data
        )

    async def _parse_listing(self, data: Dict[str, Any]) -> LeadCreate:
        """Core parsing logic with optimization."""
        try:
            cache_key = f"li_{data.get('id')}_{self.VERSION}"
            cached_result = await self.result_cache.get(cache_key)
            if cached_result:
                return cached_result

            listing_id = data.get("id")
            contact = await self._extract_contact_info(data)
            location = self._extract_location(data)

            metadata = {
                "company_info": self._extract_company_info(data),
                "job_details": self._extract_job_details(data),
                "posting_date": data.get("created_time"),
                "seniority_level": data.get("seniority_level"),
                "employment_type": data.get("employment_type"),
                "industry": data.get("industry"),
                "verification_score": await self._calculate_verification_score(data),
                "extracted_at": datetime.utcnow().isoformat(),
                "parser_version": self.VERSION,
                "engagement_metrics": self._extract_engagement_metrics(data),
            }

            lead = LeadCreate(
                source_id=listing_id,
                market=self.MARKET_ID,
                contact_name=contact.get("name", "Unknown"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                company_name=contact.get("company_name"),
                location=location,
                metadata=metadata,
            )

            await self._validate_lead(lead)
            await self.result_cache.set(cache_key, lead)
            return lead

        except Exception as e:
            logger.error(
                f"Failed to parse LinkedIn listing {data.get('id')}: {e}", exc_info=True
            )
            raise ParseError(f"Failed to parse LinkedIn listing: {str(e)}")

    async def _extract_contact_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate contact information."""
        contact = {
            "name": self._extract_name(data),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "company_name": data.get("company_name"),
        }

        if contact["email"]:
            contact["email"] = contact["email"].lower()
            if not validate_email(contact["email"]):
                contact["email"] = None

        if contact["phone"]:
            if not validate_phone(contact["phone"]):
                contact["phone"] = None

        if not (contact["email"] or contact["phone"]):
            alternative_contact = await self._extract_alternative_contact(data)
            contact.update(alternative_contact)

        return contact

    def _extract_name(self, data: Dict[str, Any]) -> str:
        """Extract and format name information."""
        recruiter_data = data.get("recruiter", {})
        if recruiter_data:
            parts = []
            if recruiter_data.get("first_name"):
                parts.append(recruiter_data["first_name"])
            if recruiter_data.get("last_name"):
                parts.append(recruiter_data["last_name"])
            if parts:
                return " ".join(parts)
        return "Unknown"

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
                "city": location_data.get("city"),
                "state": location_data.get("state"),
                "country": location_data.get("country"),
                "raw_data": location_data,
            }

        except Exception as e:
            logger.warning(f"Location extraction failed: {e}")
            raise ParseError(f"Invalid location data: {str(e)}")

    def _extract_company_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive company information."""
        company_data = data.get("company", {})
        return {
            "name": company_data.get("name"),
            "industry": company_data.get("industry"),
            "size": company_data.get("size"),
            "type": company_data.get("type"),
            "linkedin_url": company_data.get("linkedin_url"),
            "founded_year": company_data.get("founded_year"),
            "specialties": company_data.get("specialties", []),
        }

    def _extract_job_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed job information."""
        return {
            "title": data.get("title"),
            "description": data.get("description"),
            "requirements": data.get("requirements", []),
            "benefits": data.get("benefits", []),
            "skills": data.get("skills", []),
            "experience_level": data.get("experience_level"),
            "work_type": data.get("work_type"),
            "salary_range": self._extract_salary_range(data),
        }

    def _extract_salary_range(self, data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract and validate salary information."""
        salary_data = data.get("salary_range", {})
        if not salary_data:
            return None

        try:
            min_salary = validate_price(salary_data.get("min"))
            max_salary = validate_price(salary_data.get("max"))

            if min_salary and max_salary:
                return {
                    "min": min_salary,
                    "max": max_salary,
                    "currency": salary_data.get("currency", "USD"),
                }
            return None

        except ValueError:
            return None

    def _extract_engagement_metrics(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Extract engagement metrics for verification."""
        return {
            "views": data.get("view_count", 0),
            "applications": data.get("application_count", 0),
            "shares": data.get("share_count", 0),
            "saves": data.get("save_count", 0),
        }

    async def _calculate_verification_score(self, data: Dict[str, Any]) -> float:
        """Calculate verification score based on multiple factors."""
        score = 100.0
        deductions = []

        # Company verification
        if not data.get("company", {}).get("verified"):
            deductions.append(20.0)

        # Profile completeness
        company_info = data.get("company", {})
        if not all(
            [
                company_info.get("name"),
                company_info.get("industry"),
                company_info.get("size"),
            ]
        ):
            deductions.append(15.0)

        # Contact information
        if not (data.get("email") or data.get("phone")):
            deductions.append(25.0)

        # Engagement metrics
        engagement = self._extract_engagement_metrics(data)
        if engagement["views"] == 0:
            deductions.append(10.0)

        # Location verification
        if not data.get("location", {}).get("coordinates"):
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

"""
Lead validation and enrichment component for AIQLeads.

Handles:
- Data validation and cleaning
- Contact information verification
- Geospatial validation
- Basic fraud detection
- Data enrichment
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import asyncio
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from phonenumbers import parse as parse_phone, is_valid_number
from email_validator import validate_email, EmailNotValidError

from src.schemas.lead_schema import LeadCreate
from src.config import Settings
from src.monitoring import monitor
from src.cache import RedisCache

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Stores the results of lead validation"""
    is_valid: bool
    confidence_score: float
    validation_errors: list[str]
    enriched_data: Dict[str, Any]

class LeadValidator:
    """
    Comprehensive lead validation and enrichment system.
    
    Features:
    - Contact information validation
    - Address and geolocation verification
    - Fraud detection heuristics
    - Data enrichment
    """
    
    def __init__(
        self,
        settings: Settings,
        cache: RedisCache,
        min_confidence_score: float = 0.7
    ):
        """Initialize validator with configuration"""
        self.settings = settings
        self.cache = cache
        self.min_confidence_score = min_confidence_score
        self.geocoder = Nominatim(user_agent=settings.APP_NAME)
        
        # Compile regex patterns
        self.phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
        self.name_pattern = re.compile(r'^[a-zA-Z\s\'-]{2,50}$')
        
    @monitor.time_execution("lead_validation_time")
    async def validate_lead(self, lead: LeadCreate) -> ValidationResult:
        """
        Validate and enrich a lead.
        
        Args:
            lead: Lead data to validate
            
        Returns:
            ValidationResult with validation status and enriched data
        """
        errors = []
        enriched_data = {}
        confidence_scores = []
        
        try:
            # Basic contact validation
            name_score = await self._validate_name(lead.name)
            confidence_scores.append(name_score)
            
            if lead.email:
                email_score = await self._validate_email(lead.email)
                confidence_scores.append(email_score)
            
            if lead.phone:
                phone_score = await self._validate_phone(lead.phone)
                confidence_scores.append(phone_score)
                
            # Location validation
            if lead.address:
                location_score, geo_data = await self._validate_location(lead.address)
                confidence_scores.append(location_score)
                if geo_data:
                    enriched_data.update(geo_data)
            
            # Fraud detection
            fraud_score = await self._check_fraud_indicators(lead)
            confidence_scores.append(fraud_score)
            
            # Calculate overall confidence
            confidence_score = sum(confidence_scores) / len(confidence_scores)
            
            # Additional enrichment if confidence is high enough
            if confidence_score >= self.min_confidence_score:
                enriched = await self._enrich_lead_data(lead)
                enriched_data.update(enriched)
            
            is_valid = confidence_score >= self.min_confidence_score
            
            # Record metrics
            self._record_validation_metrics(is_valid, confidence_score, len(errors))
            
            return ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                validation_errors=errors,
                enriched_data=enriched_data
            )
            
        except Exception as e:
            logger.error(f"Lead validation failed: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_errors=errors,
                enriched_data={}
            )
    
    async def _validate_name(self, name: str) -> float:
        """Validate name format and check against patterns"""
        if not name or not self.name_pattern.match(name):
            return 0.0
        return 1.0
        
    async def _validate_email(self, email: str) -> float:
        """Validate email format and check domain"""
        try:
            valid = validate_email(email)
            # Check if disposable email domain
            domain = email.split('@')[1]
            if await self._is_disposable_domain(domain):
                return 0.3
            return 1.0
        except EmailNotValidError:
            return 0.0
            
    async def _validate_phone(self, phone: str) -> float:
        """Validate phone number format and region"""
        try:
            if not self.phone_pattern.match(phone):
                return 0.0
                
            parsed = parse_phone(phone)
            if not is_valid_number(parsed):
                return 0.0
                
            return 1.0
        except Exception:
            return 0.0
            
    async def _validate_location(self, address: str) -> tuple[float, Optional[Dict]]:
        """Validate address and get geolocation data"""
        try:
            location = await asyncio.to_thread(
                self.geocoder.geocode,
                address,
                exactly_one=True
            )
            
            if not location:
                return 0.0, None
                
            geo_data = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "formatted_address": location.address
            }
            
            return 1.0, geo_data
            
        except (GeocoderTimedOut, Exception) as e:
            logger.warning(f"Geocoding failed: {e}")
            return 0.0, None
            
    async def _check_fraud_indicators(self, lead: LeadCreate) -> float:
        """Check for potential fraud indicators"""
        fraud_indicators = 0
        total_checks = 5
        
        # Check for suspicious patterns
        if await self._is_disposable_domain(lead.email.split('@')[1]):
            fraud_indicators += 1
            
        if await self._is_known_spam_phone(lead.phone):
            fraud_indicators += 1
            
        if await self._is_blacklisted_address(lead.address):
            fraud_indicators += 1
            
        if await self._has_suspicious_activity(lead):
            fraud_indicators += 1
            
        if await self._is_duplicate_contact(lead):
            fraud_indicators += 1
            
        # Convert to confidence score (1 = no fraud indicators)
        return 1 - (fraud_indicators / total_checks)
        
    async def _enrich_lead_data(self, lead: LeadCreate) -> Dict[str, Any]:
        """Add additional data enrichment"""
        enriched = {}
        
        try:
            # Add social media profiles if available
            social = await self._find_social_profiles(lead)
            if social:
                enriched["social_profiles"] = social
            
            # Add market insights
            insights = await self._get_market_insights(lead)
            if insights:
                enriched["market_insights"] = insights
            
            # Add behavioral data
            behavior = await self._get_behavioral_data(lead)
            if behavior:
                enriched["behavioral_data"] = behavior
                
        except Exception as e:
            logger.warning(f"Data enrichment partially failed: {e}")
            
        return enriched
        
    async def _is_disposable_domain(self, domain: str) -> bool:
        """Check if email domain is a disposable service"""
        cache_key = f"disposable_domain:{domain}"
        
        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached == "1"
            
        # Implement actual check here
        is_disposable = False  # Replace with actual implementation
        
        # Cache result
        await self.cache.set(cache_key, "1" if is_disposable else "0", expire=86400)
        return is_disposable
        
    async def _is_known_spam_phone(self, phone: str) -> bool:
        """Check if phone number is known for spam"""
        cache_key = f"spam_phone:{phone}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached == "1"
            
        # Implement actual check here
        is_spam = False  # Replace with actual implementation
        
        await self.cache.set(cache_key, "1" if is_spam else "0", expire=86400)
        return is_spam
        
    async def _is_blacklisted_address(self, address: str) -> bool:
        """Check if address is blacklisted"""
        cache_key = f"blacklist_addr:{address}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached == "1"
            
        # Implement actual check here
        is_blacklisted = False  # Replace with actual implementation
        
        await self.cache.set(cache_key, "1" if is_blacklisted else "0", expire=86400)
        return is_blacklisted
        
    async def _has_suspicious_activity(self, lead: LeadCreate) -> bool:
        """Check for suspicious patterns in lead data"""
        # Implement suspicious activity detection
        return False
        
    async def _is_duplicate_contact(self, lead: LeadCreate) -> bool:
        """Check if contact info appears in multiple leads"""
        # Implement duplicate detection
        return False
        
    async def _find_social_profiles(self, lead: LeadCreate) -> Optional[Dict[str, str]]:
        """Find associated social media profiles"""
        # Implement social profile discovery
        return None
        
    async def _get_market_insights(self, lead: LeadCreate) -> Optional[Dict[str, Any]]:
        """Get market insights for lead's location"""
        # Implement market insights
        return None
        
    async def _get_behavioral_data(self, lead: LeadCreate) -> Optional[Dict[str, Any]]:
        """Get behavioral data insights"""
        # Implement behavioral analysis
        return None
        
    def _record_validation_metrics(
        self,
        is_valid: bool,
        confidence_score: float,
        error_count: int
    ) -> None:
        """Record validation metrics for monitoring"""
        monitor.record_gauge(
            "lead_validation_confidence",
            confidence_score
        )
        monitor.record_counter(
            "lead_validation_total",
            1,
            {"valid": str(is_valid)}
        )
        monitor.record_counter(
            "lead_validation_errors",
            error_count
        )
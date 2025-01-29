"""
Dynamic pricing engine for AIQLeads.

Features:
- Quality-based pricing adjustments
- Demand-driven price modulation
- Subscription tier discounts
- Market-based price optimization
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

from src.schemas.lead_schema import LeadCreate
from src.config import Settings
from src.cache import RedisCache
from src.monitoring import monitor

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """User subscription tiers"""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class PriceFactors:
    """Stores factors affecting lead price"""
    base_price: float
    quality_multiplier: float
    demand_multiplier: float
    tier_discount: float
    market_multiplier: float
    final_price: float

class PricingEngine:
    """
    Dynamic pricing engine for leads.
    
    Features:
    - Quality-based pricing based on lead verification and completeness
    - Demand-driven adjustments based on user interest
    - Subscription tier discounts
    - Market-based price optimization
    - Real-time price updates
    """
    
    def __init__(
        self,
        settings: Settings,
        cache: RedisCache,
        base_price: float = 10.0,
        min_price: float = 5.0,
        max_price: float = 50.0
    ):
        """
        Initialize pricing engine.
        
        Args:
            settings: Application settings
            cache: Redis cache for tracking metrics
            base_price: Starting price point for leads
            min_price: Minimum allowed price
            max_price: Maximum allowed price
        """
        self.settings = settings
        self.cache = cache
        self.base_price = base_price
        self.min_price = min_price
        self.max_price = max_price
        
        # Tier discounts (percentage)
        self.tier_discounts = {
            SubscriptionTier.BASIC: 0.0,
            SubscriptionTier.PRO: 0.15,
            SubscriptionTier.ENTERPRISE: 0.25
        }
        
        # Quality factor weights
        self.quality_weights = {
            "contact_score": 0.3,
            "property_score": 0.3,
            "engagement_score": 0.2,
            "freshness_score": 0.2
        }

    @monitor.time_execution("price_calculation_time")
    async def calculate_price(
        self,
        lead: LeadCreate,
        subscription_tier: SubscriptionTier,
        market_data: Optional[Dict[str, Any]] = None
    ) -> PriceFactors:
        """
        Calculate final lead price based on multiple factors.
        
        Args:
            lead: Lead to price
            subscription_tier: User's subscription tier
            market_data: Optional market insights
            
        Returns:
            PriceFactors containing price components and final price
        """
        try:
            # Calculate component multipliers
            quality_multiplier = await self._calculate_quality_multiplier(lead)
            demand_multiplier = await self._calculate_demand_multiplier(lead)
            tier_discount = self.tier_discounts[subscription_tier]
            market_multiplier = await self._calculate_market_multiplier(lead, market_data)
            
            # Calculate base price with quality and demand
            adjusted_base = self.base_price * quality_multiplier * demand_multiplier * market_multiplier
            
            # Apply tier discount
            final_price = adjusted_base * (1 - tier_discount)
            
            # Ensure price is within bounds
            final_price = max(min(final_price, self.max_price), self.min_price)
            
            # Record metrics
            self._record_price_metrics(lead, final_price, quality_multiplier, demand_multiplier)
            
            return PriceFactors(
                base_price=self.base_price,
                quality_multiplier=quality_multiplier,
                demand_multiplier=demand_multiplier,
                tier_discount=tier_discount,
                market_multiplier=market_multiplier,
                final_price=final_price
            )
            
        except Exception as e:
            logger.error(f"Price calculation failed: {e}", exc_info=True)
            monitor.record_counter("pricing_errors", 1)
            
            # Return default pricing on error
            return PriceFactors(
                base_price=self.base_price,
                quality_multiplier=1.0,
                demand_multiplier=1.0,
                tier_discount=0.0,
                market_multiplier=1.0,
                final_price=self.base_price
            )

    async def _calculate_quality_multiplier(self, lead: LeadCreate) -> float:
        """Calculate price multiplier based on lead quality"""
        try:
            # Calculate component scores
            contact_score = self._score_contact_info(lead)
            property_score = self._score_property_info(lead)
            engagement_score = await self._score_engagement(lead)
            freshness_score = self._score_freshness(lead)
            
            # Combine weighted scores
            quality_score = (
                self.quality_weights["contact_score"] * contact_score +
                self.quality_weights["property_score"] * property_score +
                self.quality_weights["engagement_score"] * engagement_score +
                self.quality_weights["freshness_score"] * freshness_score
            )
            
            # Convert to multiplier (0.5 - 2.0 range)
            return 0.5 + (quality_score * 1.5)
            
        except Exception as e:
            logger.warning(f"Quality calculation failed: {e}")
            return 1.0

    def _score_contact_info(self, lead: LeadCreate) -> float:
        """Score contact information completeness and validity"""
        score = 0.0
        total_checks = 4
        
        # Check email
        if lead.email and "@" in lead.email:
            score += 1
            
        # Check phone
        if lead.phone and len(lead.phone) >= 10:
            score += 1
            
        # Check name
        if lead.name and len(lead.name.split()) >= 2:
            score += 1
            
        # Check address
        if lead.address and len(lead.address) > 10:
            score += 1
            
        return score / total_checks

    def _score_property_info(self, lead: LeadCreate) -> float:
        """Score property information completeness"""
        score = 0.0
        total_checks = 5
        
        # Check price
        if lead.price and lead.price > 0:
            score += 1
            
        # Check bedrooms
        if lead.bedrooms and lead.bedrooms > 0:
            score += 1
            
        # Check bathrooms
        if lead.bathrooms and lead.bathrooms > 0:
            score += 1
            
        # Check square footage
        if lead.square_feet and lead.square_feet > 0:
            score += 1
            
        # Check location
        if lead.latitude and lead.longitude:
            score += 1
            
        return score / total_checks

    async def _score_engagement(self, lead: LeadCreate) -> float:
        """Score user engagement with the lead"""
        cache_key = f"lead_engagement:{lead.id}"
        
        try:
            engagement_data = await self.cache.get_json(cache_key)
            if not engagement_data:
                return 0.5  # Default score for new leads
                
            # Calculate engagement score
            views = engagement_data.get("views", 0)
            cart_adds = engagement_data.get("cart_adds", 0)
            purchases = engagement_data.get("purchases", 0)
            
            engagement_score = (
                (views * 0.2) +
                (cart_adds * 0.3) +
                (purchases * 0.5)
            ) / 10  # Normalize to 0-1
            
            return min(engagement_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Engagement scoring failed: {e}")
            return 0.5

    def _score_freshness(self, lead: LeadCreate) -> float:
        """Score lead freshness based on age"""
        if not lead.created_at:
            return 0.5
            
        age_hours = (datetime.utcnow() - lead.created_at).total_seconds() / 3600
        
        if age_hours < 24:
            return 1.0
        elif age_hours < 72:
            return 0.8
        elif age_hours < 168:  # 1 week
            return 0.6
        elif age_hours < 336:  # 2 weeks
            return 0.4
        else:
            return 0.2

    async def _calculate_demand_multiplier(self, lead: LeadCreate) -> float:
        """Calculate price multiplier based on demand"""
        cache_key = f"lead_demand:{lead.id}"
        
        try:
            demand_data = await self.cache.get_json(cache_key)
            if not demand_data:
                return 1.0  # Default multiplier
                
            # Calculate demand score
            views_24h = demand_data.get("views_24h", 0)
            cart_adds_24h = demand_data.get("cart_adds_24h", 0)
            purchases_24h = demand_data.get("purchases_24h", 0)
            
            demand_score = (
                (views_24h * 0.2) +
                (cart_adds_24h * 0.3) +
                (purchases_24h * 0.5)
            ) / 10  # Normalize
            
            # Convert to multiplier (0.8 - 1.5 range)
            return 0.8 + (demand_score * 0.7)
            
        except Exception as e:
            logger.warning(f"Demand calculation failed: {e}")
            return 1.0

    async def _calculate_market_multiplier(
        self,
        lead: LeadCreate,
        market_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate price multiplier based on market conditions"""
        try:
            if not market_data:
                return 1.0
                
            # Extract market factors
            avg_price = market_data.get("avg_price", 0)
            competition = market_data.get("competition_level", 0.5)
            growth_rate = market_data.get("market_growth", 0)
            
            if not avg_price:
                return 1.0
                
            # Calculate relative price position
            price_position = lead.price / avg_price if lead.price else 1.0
            
            # Combine factors
            market_score = (
                (price_position * 0.4) +
                (competition * 0.3) +
                (growth_rate * 0.3)
            )
            
            # Convert to multiplier (0.7 - 1.3 range)
            return 0.7 + (market_score * 0.6)
            
        except Exception as e:
            logger.warning(f"Market multiplier calculation failed: {e}")
            return 1.0

    def _record_price_metrics(
        self,
        lead: LeadCreate,
        final_price: float,
        quality_multiplier: float,
        demand_multiplier: float
    ) -> None:
        """Record pricing metrics for monitoring"""
        monitor.record_gauge(
            "lead_price",
            final_price,
            {"source": lead.source}
        )
        monitor.record_gauge(
            "quality_multiplier",
            quality_multiplier,
            {"source": lead.source}
        )
        monitor.record_gauge(
            "demand_multiplier",
            demand_multiplier,
            {"source": lead.source}
        )
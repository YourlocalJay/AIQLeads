from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import asyncio
import logging
import re
import uuid
import asyncpg
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException, PhoneNumberFormat
from aioredis import Redis
from cachetools import TTLCache
from aiqleads.models.lead_model import Lead, LeadScore
from aiqleads.core.project_tracking import ProjectTracker

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    timestamp: datetime
    lead_id: str

class LeadService:
    def __init__(
        self,
        redis: Redis = None,
        database: asyncpg.Pool = None,
        tracker: ProjectTracker = None,
        max_cache_size: int = 10000,
        cache_ttl: int = 86400  # 24 hours
    ):
        self.redis = redis
        self.database = database
        self.tracker = tracker or ProjectTracker()
        self._local_cache = TTLCache(maxsize=max_cache_size, ttl=cache_ttl)
        self._cache_lock = asyncio.Lock()
        self._duplicate_check_window = timedelta(days=30)
        self._phone_cache = TTLCache(maxsize=5000, ttl=3600)

        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0

    async def is_duplicate(self, lead: Lead) -> bool:
        """Check if a lead is duplicate using multi-layered verification."""
        try:
            fingerprint = await self._generate_fingerprint(lead)

            # Check local cache first
            async with self._cache_lock:
                if fingerprint in self._local_cache:
                    self.cache_hits += 1
                    return True
                self.cache_misses += 1

            # Check Redis if available
            if self.redis and await self.redis.exists(f"lead:{fingerprint}"):
                return True

            # Database check
            existing_lead = await self._check_database_duplicates(fingerprint)
            if existing_lead:
                await self._update_caches(fingerprint, existing_lead.id)
                return True

            return False
        except Exception as e:
            logger.error(f"Duplicate check failed for lead {lead.id}", exc_info=True)
            self.tracker.log_error("lead_service", "Duplicate check failed", str(e))
            return False

    async def _generate_fingerprint(self, lead: Lead) -> str:
        """Create a secure SHA-3 fingerprint for a lead."""
        email = lead.contact_info.email.lower().strip() if lead.contact_info.email else ''
        phone = await self._normalize_phone(lead.contact_info.phone) if lead.contact_info.phone else ''
        locations = ','.join(sorted(lead.preferences.locations))
        min_price = round(lead.preferences.price_range.get('min', 0.0), 2)
        max_price = round(lead.preferences.price_range.get('max', 0.0), 2)

        fingerprint_str = f"{email}:{phone}:{locations}:{min_price}:{max_price}"
        return hashlib.sha3_256(fingerprint_str.encode()).hexdigest()

    async def _normalize_phone(self, phone: str) -> str:
        """Normalize phone numbers into E.164 format."""
        try:
            parsed = phonenumbers.parse(phone, None)
            if not parsed or not phonenumbers.is_valid_number(parsed):
                return ''
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        except NumberParseException:
            return re.sub(r'\D', '', phone)[-10:]

    async def _check_database_duplicates(self, fingerprint: str) -> Optional[Lead]:
        """Check database for existing leads with same fingerprint."""
        try:
            query = """
                SELECT id, created_at FROM leads 
                WHERE fingerprint = $1 
                AND created_at > NOW() - INTERVAL '30 days'
                LIMIT 1
            """
            result = await self.database.fetchrow(query, fingerprint)
            return Lead(id=result['id']) if result else None
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            return None

    async def get_score(self, lead_id: str) -> Optional[LeadScore]:
        """Retrieve a lead score with caching."""
        try:
            async with self._cache_lock:
                if score := self._local_cache.get(lead_id):
                    return score

            if self.redis:
                redis_key = f"score:{lead_id}"
                if cached := await self.redis.get(redis_key):
                    return LeadScore.parse_raw(cached)

            query = "SELECT score_data FROM lead_scores WHERE lead_id = $1"
            result = await self.database.fetchval(query, lead_id)
            if not result:
                return None

            score = LeadScore.parse_raw(result)
            await self._update_caches(lead_id, score)
            return score
        except Exception as e:
            logger.error(f"Failed to retrieve score for {lead_id}", exc_info=True)
            return None

    async def store_score(self, lead_id: str, score: LeadScore):
        """Store a lead score in the database and cache."""
        try:
            query = """
                INSERT INTO lead_scores (lead_id, score_data)
                VALUES ($1, $2)
                ON CONFLICT (lead_id) DO UPDATE
                SET score_data = EXCLUDED.score_data
            """
            await self.database.execute(query, lead_id, score.json())

            await self._update_caches(lead_id, score)
        except Exception as e:
            logger.error(f"Failed to store score for {lead_id}", exc_info=True)
            raise

    async def _update_caches(self, key: str, value: Any):
        """Update local and Redis caches."""
        async with self._cache_lock:
            self._local_cache[key] = value

        if self.redis:
            await self.redis.setex(f"score:{key}", self._local_cache.ttl, value.json())

    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Return cache performance metrics."""
        return {
            "local_cache_size": len(self._local_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_ratio": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }

    async def clear_cache(self):
        """Clear all cached data."""
        async with self._cache_lock:
            self._local_cache.clear()

        if self.redis:
            await self.redis.flushdb()

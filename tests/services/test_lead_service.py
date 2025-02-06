import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio
import json
from aioredis import Redis
from asyncpg import Pool
from phonenumbers.phonenumberutil import NumberParseException

from aiqleads.services.lead_service import LeadService, CacheEntry
from aiqleads.models.lead_model import Lead, LeadScore, ContactInfo, LeadPreferences

@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    with patch('aioredis.Redis') as mock:
        mock.return_value = AsyncMock()
        yield mock

@pytest.fixture
def mock_db():
    """Mock database connection"""
    with patch('asyncpg.Pool') as mock:
        mock.return_value = AsyncMock()
        yield mock

@pytest.fixture
def lead_service(mock_redis, mock_db):
    """Create LeadService instance with mocked dependencies"""
    return LeadService(
        redis=mock_redis,
        database=mock_db,
        max_cache_size=100,
        cache_ttl=3600
    )

@pytest.fixture
def sample_lead():
    """Create a sample lead for testing"""
    return Lead(
        source="test",
        contact_info=ContactInfo(
            email="test@example.com",
            phone="+1-555-555-5555"
        ),
        preferences=LeadPreferences(
            property_types=["residential"],
            price_range={"min": 200000.0, "max": 500000.0},
            locations=["San Francisco, CA"]
        )
    )

class TestLeadService:
    """Test suite for LeadService"""

    @pytest.mark.asyncio
    async def test_duplicate_detection_local_cache(self, lead_service, sample_lead):
        """Test duplicate detection using local cache"""
        # First check should query all layers
        lead_service._generate_fingerprint = AsyncMock(return_value="test_fingerprint")
        first_check = await lead_service.is_duplicate(sample_lead)
        assert not first_check
        assert lead_service.cache_misses == 1

        # Add to cache
        async with lead_service._cache_lock:
            lead_service._local_cache["test_fingerprint"] = CacheEntry(
                timestamp=datetime.utcnow(),
                lead_id=str(sample_lead.id)
            )

        # Second check should hit local cache
        second_check = await lead_service.is_duplicate(sample_lead)
        assert second_check
        assert lead_service.cache_hits == 1

    @pytest.mark.asyncio
    async def test_duplicate_detection_redis(self, lead_service, sample_lead, mock_redis):
        """Test duplicate detection using Redis"""
        lead_service._generate_fingerprint = AsyncMock(return_value="test_fingerprint")
        mock_redis.exists = AsyncMock(return_value=True)

        is_duplicate = await lead_service.is_duplicate(sample_lead)
        assert is_duplicate
        mock_redis.exists.assert_called_once_with("lead:test_fingerprint")

    @pytest.mark.asyncio
    async def test_duplicate_detection_database(self, lead_service, sample_lead, mock_db):
        """Test duplicate detection using database"""
        lead_service._generate_fingerprint = AsyncMock(return_value="test_fingerprint")
        mock_db.fetchrow = AsyncMock(return_value={"id": str(sample_lead.id)})

        is_duplicate = await lead_service.is_duplicate(sample_lead)
        assert is_duplicate
        mock_db.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_phone_normalization(self, lead_service):
        """Test phone number normalization"""
        test_cases = [
            ("+1-555-555-5555", "+15555555555"),
            ("(555) 555-5555", "5555555555"),
            ("555.555.5555", "5555555555"),
            ("5555555555", "5555555555"),
            ("invalid", ""),  # Should handle invalid numbers gracefully
        ]

        for input_phone, expected in test_cases:
            normalized = await lead_service._normalize_phone(input_phone)
            assert normalized == expected

    @pytest.mark.asyncio
    async def test_score_caching(self, lead_service, sample_lead):
        """Test score caching mechanism"""
        lead_id = str(sample_lead.id)
        test_score = LeadScore(
            lead_id=lead_id,
            score=85.5,
            confidence=0.92,
            factors=[{"factor": "location", "weight": 0.7}],
            recommendations=["Follow up within 24 hours"]
        )

        # Test storing score
        await lead_service.store_score(lead_id, test_score)
        
        # Should be in local cache
        async with lead_service._cache_lock:
            assert lead_id in lead_service._local_cache
            cached_score = lead_service._local_cache[lead_id]
            assert cached_score.score == test_score.score

        # Should be in Redis
        lead_service.redis.setex.assert_called_once()

        # Test retrieving score
        retrieved_score = await lead_service.get_score(lead_id)
        assert retrieved_score.score == test_score.score
        assert retrieved_score.confidence == test_score.confidence
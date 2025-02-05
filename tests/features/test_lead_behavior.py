import pytest
from datetime import datetime, timedelta, timezone
from app.features.lead_behavior import LeadBehaviorExtractor, ValidationError


def create_interaction(action: str, timestamp: datetime) -> dict:
    """Helper to create interaction dictionary"""
    return {"action": action, "timestamp": timestamp.isoformat()}


def create_test_data(num_interactions: int = 5, hours_between: int = 1) -> dict:
    """Create test lead data with specified number of interactions"""
    now = datetime.now(timezone.utc)
    interactions = []

    actions = ["view", "click", "inquiry", "message", "schedule"]
    for i in range(num_interactions):
        timestamp = now - timedelta(hours=i * hours_between)
        action = actions[i % len(actions)]
        interactions.append(create_interaction(action, timestamp))

    return {
        "interactions": interactions,
        "first_seen": interactions[-1]["timestamp"],
        "last_seen": interactions[0]["timestamp"],
    }


@pytest.fixture
def extractor():
    config = {
        "min_interactions": 1,
        "max_interaction_gap_hours": 72,
        "engagement_weights": {
            "view": 1.0,
            "click": 2.0,
            "inquiry": 3.0,
            "message": 4.0,
            "schedule": 5.0,
        },
    }
    return LeadBehaviorExtractor(config)


@pytest.mark.asyncio
async def test_basic_extraction(extractor):
    """Test basic feature extraction"""
    lead_data = create_test_data(5)
    features = await extractor.extract(lead_data)

    # Check core features exist
    assert "total_interactions" in features
    assert "unique_action_types" in features
    assert "days_since_first" in features
    assert "days_since_last" in features

    # Verify values
    assert features["total_interactions"] == 5
    assert features["unique_action_types"] == 5


@pytest.mark.asyncio
async def test_action_frequencies(extractor):
    """Test action frequency calculations"""
    lead_data = create_test_data(10)  # Will create 2 of each action type
    features = await extractor.extract(lead_data)

    # Check frequencies sum to approximately 1
    frequencies = [v for k, v in features.items() if k.endswith("_frequency")]
    assert abs(sum(frequencies) - 1.0) < 0.0001

    # Check individual frequencies
    for action in ["view", "click", "inquiry", "message", "schedule"]:
        assert f"{action}_frequency" in features
        assert features[f"{action}_frequency"] == 0.2  # 2/10 for each type


@pytest.mark.asyncio
async def test_temporal_patterns(extractor):
    """Test temporal pattern extraction"""
    # Create interactions at specific times
    now = datetime.now(timezone.utc)
    interactions = [
        # Business hours
        create_interaction("view", now.replace(hour=10)),
        create_interaction("click", now.replace(hour=14)),
        # Non-business hours
        create_interaction("inquiry", now.replace(hour=20)),
        # Weekend
        create_interaction(
            "message", now.replace(hour=15, day=now.day - 2)
        ),  # Saturday
    ]

    lead_data = {
        "interactions": interactions,
        "first_seen": interactions[-1]["timestamp"],
        "last_seen": interactions[0]["timestamp"],
    }

    features = await extractor.extract(lead_data)

    assert "peak_hour" in features
    assert "business_hours_ratio" in features
    assert "weekend_ratio" in features


@pytest.mark.asyncio
async def test_engagement_metrics(extractor):
    """Test engagement score calculations"""
    lead_data = create_test_data(5)
    features = await extractor.extract(lead_data)

    assert "engagement_score_total" in features
    assert "engagement_score_avg" in features
    assert "engagement_score_median" in features

    # Verify engagement scores are calculated correctly
    weights = extractor.engagement_weights
    expected_total = sum(weights[i["action"]] for i in lead_data["interactions"])
    assert features["engagement_score_total"] == expected_total


@pytest.mark.asyncio
async def test_session_metrics(extractor):
    """Test session-based metrics"""
    # Create two distinct sessions
    now = datetime.now(timezone.utc)
    session1 = [
        create_interaction("view", now - timedelta(minutes=10)),
        create_interaction("click", now - timedelta(minutes=5)),
    ]
    session2 = [
        create_interaction("inquiry", now - timedelta(hours=24)),
        create_interaction("message", now - timedelta(hours=24, minutes=10)),
    ]

    lead_data = {
        "interactions": session1 + session2,
        "first_seen": session2[0]["timestamp"],
        "last_seen": session1[-1]["timestamp"],
    }

    features = await extractor.extract(lead_data)

    assert features["total_sessions"] == 2
    assert features["avg_actions_per_session"] == 2.0
    assert "avg_session_length_minutes" in features


@pytest.mark.asyncio
async def test_validation_errors(extractor):
    """Test validation error cases"""
    # Missing required fields
    with pytest.raises(ValidationError):
        await extractor.extract({"interactions": []})

    # Invalid interactions type
    with pytest.raises(ValidationError):
        await extractor.extract(
            {
                "interactions": "not a list",
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
            }
        )

    # Too few interactions
    extractor.min_interactions = 5
    with pytest.raises(ValidationError):
        await extractor.extract(create_test_data(3))


@pytest.mark.asyncio
async def test_cache_functionality(extractor):
    """Test that caching works for lead behavior features"""
    lead_data = create_test_data(5)

    # First call should compute
    features1 = await extractor.extract(lead_data)

    # Second call should hit cache
    features2 = await extractor.extract(lead_data)

    assert features1 == features2

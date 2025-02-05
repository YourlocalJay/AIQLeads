import pytest
from unittest.mock import AsyncMock, patch
from app.features.base import (
    BaseFeatureExtractor,
    FeatureExtractionError,
    ValidationError,
)


class TestFeatureExtractor(BaseFeatureExtractor):
    """Test implementation of BaseFeatureExtractor"""

    async def _compute_features(self, lead_data):
        return {"test_feature_1": 1.0, "test_feature_2": 2.0}


@pytest.fixture
def extractor():
    return TestFeatureExtractor()


@pytest.mark.asyncio
async def test_extract_basic_functionality(extractor):
    """Test basic feature extraction without cache"""
    lead_data = {"id": 1, "name": "Test Lead"}
    features = await extractor.extract(lead_data)

    assert isinstance(features, dict)
    assert "test_feature_1" in features
    assert "test_feature_2" in features
    assert features["test_feature_1"] == 1.0
    assert features["test_feature_2"] == 2.0


@pytest.mark.asyncio
async def test_extract_with_cache(extractor):
    """Test feature extraction with cache hit"""
    lead_data = {"id": 2, "name": "Test Lead 2"}
    cache_key = extractor._generate_cache_key(lead_data)

    # Mock cache hit
    cached_features = {"cached_feature": 3.0}
    with patch.object(extractor.cache, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = cached_features
        features = await extractor.extract(lead_data)

    assert features == cached_features
    mock_get.assert_called_once_with(cache_key)


@pytest.mark.asyncio
async def test_extract_validation_error(extractor):
    """Test validation error handling"""
    lead_data = {"id": 3, "name": "Test Lead 3"}

    # Override _compute_features to return invalid data
    async def invalid_compute(data):
        return {"invalid_feature": "not a number"}

    extractor._compute_features = invalid_compute

    with pytest.raises(ValidationError):
        await extractor.extract(lead_data)


@pytest.mark.asyncio
async def test_batch_extraction(extractor):
    """Test batch feature extraction"""
    leads_data = [{"id": i, "name": f"Test Lead {i}"} for i in range(5)]

    features = await extractor.extract_batch(leads_data)

    assert len(features) == len(leads_data)
    for feature_set in features:
        assert isinstance(feature_set, dict)
        assert "test_feature_1" in feature_set
        assert "test_feature_2" in feature_set


@pytest.mark.asyncio
async def test_cache_miss_sets_cache(extractor):
    """Test that cache misses result in cache updates"""
    lead_data = {"id": 4, "name": "Test Lead 4"}
    cache_key = extractor._generate_cache_key(lead_data)

    # Mock cache miss then set
    with patch.object(extractor.cache, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        with patch.object(extractor.cache, "set", new_callable=AsyncMock) as mock_set:
            features = await extractor.extract(lead_data)

            mock_set.assert_called_once()
            assert mock_set.call_args[0][0] == cache_key
            assert mock_set.call_args[0][1] == features


@pytest.mark.asyncio
async def test_compute_features_error(extractor):
    """Test error handling in _compute_features"""
    lead_data = {"id": 5, "name": "Test Lead 5"}

    # Override _compute_features to raise an error
    async def failing_compute(data):
        raise ValueError("Computation failed")

    extractor._compute_features = failing_compute

    with pytest.raises(FeatureExtractionError):
        await extractor.extract(lead_data)


@pytest.mark.asyncio
async def test_cache_key_consistency(extractor):
    """Test that cache keys are consistent for same data"""
    lead_data_1 = {"id": 6, "name": "Test Lead 6", "extra": "data"}
    lead_data_2 = {"name": "Test Lead 6", "id": 6, "extra": "data"}

    key_1 = extractor._generate_cache_key(lead_data_1)
    key_2 = extractor._generate_cache_key(lead_data_2)

    assert key_1 == key_2


@pytest.mark.asyncio
async def test_batch_size_respected(extractor):
    """Test that batch processing respects batch size limit"""
    extractor.batch_size = 2
    leads_data = [{"id": i} for i in range(5)]

    with patch.object(extractor, "extract", new_callable=AsyncMock) as mock_extract:
        await extractor.extract_batch(leads_data)

        # Should be called 5 times (not batched into 3)
        assert mock_extract.call_count == 5

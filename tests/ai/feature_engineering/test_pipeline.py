import pytest
from aiqleads.ai.feature_engineering import FeatureEngineeringPipeline
from aiqleads.ai.feature_engineering.pipeline import FeatureEngineeringConfig


@pytest.fixture
def sample_config() -> FeatureEngineeringConfig:
    return FeatureEngineeringConfig(
        preprocessing_steps=[],
        feature_extractors=[],
        validation_rules=[],
        storage_config={},
    )


@pytest.mark.asyncio
async def test_pipeline_initialization(sample_config):
    pipeline = FeatureEngineeringPipeline(sample_config)
    assert pipeline is not None
    assert pipeline.config == sample_config


@pytest.mark.asyncio
async def test_process_lead(sample_config):
    pipeline = FeatureEngineeringPipeline(sample_config)
    lead_data = {"id": "test_lead", "data": {}}
    result = await pipeline.process_lead(lead_data)
    assert isinstance(result, dict)

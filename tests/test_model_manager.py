import pytest
from datetime import datetime, timedelta
from ai_models.model_manager import ModelManager, ModelType, ModelUsageTracker
from ai_models.model_config import get_model_config, ModelConfig

@pytest.fixture
def model_tracker():
    return ModelUsageTracker()

@pytest.fixture
def model_manager():
    return ModelManager()

def test_model_usage_tracking(model_tracker):
    """Test basic usage tracking functionality"""
    model_type = ModelType.CLAUDE_3_5_SONNET
    
    # Log some usage
    model_tracker.log_usage(model_type)
    assert model_tracker.get_usage_count(model_type) == 1
    
    # Test cleanup
    old_time = datetime.now() - timedelta(hours=25)
    model_tracker.usage_logs[model_type.value].append(old_time)
    model_tracker.cleanup_old_logs()
    
    # Should only count recent usage
    assert model_tracker.get_usage_count(model_type) == 1

def test_model_switching(model_tracker):
    """Test model switching logic"""
    current_model = ModelType.CLAUDE_3_5_SONNET
    model_tracker.current_model = current_model
    
    # Add usage up to limit
    config = get_model_config(current_model.value)
    for _ in range(config.max_hourly_requests):
        model_tracker.log_usage(current_model)
    
    assert model_tracker.should_switch_model()
    
    # Test switching
    next_model = model_tracker.get_next_available_model()
    assert next_model != current_model
    assert model_tracker.switch_model()
    assert model_tracker.current_model != current_model

@pytest.mark.asyncio
async def test_process_request(model_manager):
    """Test request processing with fallback"""
    # Mock _call_model to simulate API calls
    async def mock_call(*args, **kwargs):
        return "Test response"
    
    model_manager._call_model = mock_call
    
    # Process multiple requests
    response = await model_manager.process_request("Test prompt")
    assert response == "Test response"
    
    # Test usage tracking
    assert model_manager.tracker.get_usage_count(
        model_manager.tracker.current_model
    ) == 1

@pytest.mark.asyncio
async def test_error_handling(model_manager):
    """Test error handling and fallback behavior"""
    call_count = 0
    
    # Mock _call_model to fail on first call
    async def mock_call(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("API Error")
        return "Fallback response"
    
    model_manager._call_model = mock_call
    
    # Should succeed with fallback
    response = await model_manager.process_request("Test prompt")
    assert response == "Fallback response"
    assert call_count == 2  # Original + fallback

def test_model_config_integration(model_tracker):
    """Test integration with model configurations"""
    model_type = ModelType.CLAUDE_3_5_SONNET
    config = get_model_config(model_type.value)
    
    # Log up to limit
    for _ in range(config.max_hourly_requests):
        model_tracker.log_usage(model_type)
    
    assert model_tracker.should_switch_model()
    
    # Verify next model selection
    next_model = model_tracker.get_next_available_model()
    next_config = get_model_config(next_model.value)
    assert next_config.max_hourly_requests > 0
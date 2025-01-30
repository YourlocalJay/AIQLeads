"""Test configuration and shared fixtures for AIQLeads"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.DEBUG)

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock Redis client for tests
@pytest.fixture
def mock_redis_client():
    with patch('redis.asyncio.Redis') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance

# System metrics mock for performance tests
@pytest.fixture
def mock_system_metrics():
    with patch('psutil.cpu_percent', return_value=50.0), \
         patch('psutil.virtual_memory', return_value=Mock(percent=60.0)), \
         patch('psutil.disk_io_counters', return_value=(1000, 2000)), \
         patch('psutil.net_io_counters', return_value=(3000, 4000)):
        yield

# Shared test data
@pytest.fixture
def test_items():
    return [f"item_{i}" for i in range(100)]

# Mock for high system load
@pytest.fixture
def mock_high_load():
    with patch('psutil.cpu_percent', return_value=95.0), \
         patch('psutil.virtual_memory', return_value=Mock(percent=90.0)):
        yield
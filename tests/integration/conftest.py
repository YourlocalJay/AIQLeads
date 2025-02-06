import pytest
from fastapi.testclient import TestClient
from aiqleads.core.config import Settings
from aiqleads.api.v1.app import create_app

@pytest.fixture(scope='session')
def settings():
    return Settings()

@pytest.fixture(scope='session')
def app(settings):
    return create_app(settings)

@pytest.fixture(scope='function')
def client(app):
    return TestClient(app)

@pytest.fixture(scope='session')
def auth_headers(settings):
    return {
        'Authorization': f'Bearer {settings.test_api_key}'
    }
import pytest
from src.services.api import APIIntegration
from src.services.validation import ValidationService


@pytest.fixture
def services():
    return {"api": APIIntegration("http://test"), "validation": ValidationService()}


def test_api_validation_flow(services, requests_mock):
    requests_mock.get("http://test/data", json={"status": "ok"})
    data = services["api"].request("GET", "data")
    validation = services["validation"].validate(data)
    assert validation["status"] == "success"

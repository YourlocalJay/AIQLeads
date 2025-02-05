import pytest
from src.services.validation import ValidationService
from src.services.alerts import AlertService
from src.services.rate_limiter import RateLimiter


@pytest.fixture
def services():
    return {
        "validation": ValidationService(),
        "alerts": AlertService("mock_webhook", "mock_key"),
        "rate_limiter": RateLimiter(None),
    }


def test_validation_flow(services):
    result = services["validation"].validate({"test": "data"})
    assert result["status"] == "success"


def test_rate_limit_integration(services):
    assert services["rate_limiter"].check_rate_limit("test", 100, 3600)


def test_alert_integration(services, mocker):
    mock_slack = mocker.patch("requests.post")
    services["alerts"].send_alert("warning", "test")
    assert mock_slack.called

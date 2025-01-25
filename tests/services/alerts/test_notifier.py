import pytest
from src.services.alerts.notifier import AlertService, AlertLevel

def test_slack_alert(requests_mock):
    service = AlertService('http://slack', 'pd_key')
    requests_mock.post('http://slack')
    service._send_slack(AlertLevel.WARNING, "Test alert", {"key": "value"})
    assert requests_mock.called

def test_pagerduty_alert(requests_mock):
    service = AlertService('http://slack', 'pd_key')
    requests_mock.post('https://events.pagerduty.com/v2/enqueue')
    service._trigger_pagerduty(AlertLevel.CRITICAL, "Critical alert", {"error": "timeout"})
    assert requests_mock.called
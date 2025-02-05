from typing import Dict, Any
from enum import Enum
import requests


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertService:
    def __init__(self, slack_webhook: str, pagerduty_key: str):
        self.slack_webhook = slack_webhook
        self.pagerduty_key = pagerduty_key

    def send_alert(
        self, level: AlertLevel, message: str, details: Dict[str, Any]
    ) -> None:
        if level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            self._trigger_pagerduty(level, message, details)
        self._send_slack(level, message, details)

    def _send_slack(
        self, level: AlertLevel, message: str, details: Dict[str, Any]
    ) -> None:
        payload = {
            "text": f"[{level.value.upper()}] {message}",
            "attachments": [
                {"fields": [{"title": k, "value": str(v)} for k, v in details.items()]}
            ],
        }
        requests.post(self.slack_webhook, json=payload)

    def _trigger_pagerduty(
        self, level: AlertLevel, message: str, details: Dict[str, Any]
    ) -> None:
        payload = {
            "incident": {
                "title": message,
                "urgency": "high" if level == AlertLevel.CRITICAL else "low",
                "details": details,
            }
        }
        requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            headers={"Authorization": f"Token token={self.pagerduty_key}"},
            json=payload,
        )

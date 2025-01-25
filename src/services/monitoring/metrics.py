from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class MetricType:
    API_RESPONSE_TIME = "api_response_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    VALIDATION_TIME = "validation_time"
    RATE_LIMIT = "rate_limit"

class MetricsCollector:
    def __init__(self):
        self.start_time = None
        self.metrics = {}

    def start_timer(self) -> None:
        self.start_time = time.time()

    def record_metric(self, metric_type: str, value: float) -> None:
        self.metrics[metric_type] = value

    def stop_timer(self, metric_type: str) -> float:
        if self.start_time is None:
            raise ValueError("Timer not started")
        duration = time.time() - self.start_time
        self.record_metric(metric_type, duration)
        return duration

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
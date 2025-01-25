import pytest
from src.services.monitoring.metrics import MetricsCollector, MetricType

def test_metrics_collection():
    collector = MetricsCollector()
    collector.start_timer()
    collector.stop_timer(MetricType.API_RESPONSE_TIME)
    
    metrics = collector.get_metrics()
    assert MetricType.API_RESPONSE_TIME in metrics

def test_metric_recording():
    collector = MetricsCollector()
    collector.record_metric(MetricType.ERROR_RATE, 0.5)
    
    metrics = collector.get_metrics()
    assert metrics[MetricType.ERROR_RATE] == 0.5
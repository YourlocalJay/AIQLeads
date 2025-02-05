import pytest
import time
from prometheus_client import REGISTRY

from .schema_monitoring import SchemaMetrics


@pytest.fixture
def schema_metrics():
    metrics = SchemaMetrics()
    yield metrics
    # Clear registered metrics after each test
    for metric in list(REGISTRY._names_to_collectors.values()):
        REGISTRY.unregister(metric)


class TestSchemaMonitoring:
    @pytest.mark.asyncio
    async def test_validation_time_tracking(self, schema_metrics):
        endpoint = "/test/endpoint"
        schema_version = "1.0"

        with schema_metrics.track_validation_time(endpoint, schema_version):
            time.sleep(0.005)  # Simulate validation work

        # Verify metrics were recorded
        metric = schema_metrics.validation_duration.labels(
            endpoint=endpoint, schema_version=schema_version
        )
        assert metric._sum.get() > 0

    @pytest.mark.asyncio
    async def test_validation_time_threshold(self, schema_metrics):
        endpoint = "/test/endpoint"
        schema_version = "1.0"

        with pytest.warns(UserWarning):
            with schema_metrics.track_validation_time(endpoint, schema_version):
                time.sleep(0.015)  # Exceed 10ms threshold

    def test_cache_hit_ratio_tracking(self, schema_metrics):
        # Simulate cache operations
        for _ in range(85):
            schema_metrics.track_cache_operation("get", hit=True)
        for _ in range(15):
            schema_metrics.track_cache_operation("get", hit=False)

        # Verify hit ratio is tracked
        samples = list(schema_metrics.cache_hit_ratio.collect()[0].samples)
        assert len(samples) > 0

        # Verify hit ratio calculation
        hits = schema_metrics.cache_operations.labels(
            operation="get", status="hit"
        )._value.get()
        total = (
            hits
            + schema_metrics.cache_operations.labels(
                operation="get", status="miss"
            )._value.get()
        )
        assert (hits / total) >= 0.85  # Meets threshold

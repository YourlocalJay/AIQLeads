"""
Tests for AI-focused monitoring system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import random
from app.core.ai_monitoring import (
    AIOperationMetrics,
    AIAnomalyDetector,
    track_ai_operation,
    monitor,
)


@pytest.fixture
def sample_metrics():
    """Create sample AI operation metrics."""
    return AIOperationMetrics(
        operation_id="test_op_1",
        model_name="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        duration_ms=1000.0,
        cost=0.03,
        success=True,
        region="test_region",
        lead_id="test_lead",
        prompt_chars=500,
        response_chars=250,
        cache_hit=False,
    )


@pytest.fixture
def anomaly_detector():
    """Create anomaly detector instance."""
    return AIAnomalyDetector(window_size=10)


class TestAIMonitoring:
    @pytest.mark.asyncio
    async def test_basic_metric_recording(self, sample_metrics):
        """Test basic metric recording functionality."""
        await monitor.record_operation(sample_metrics)

        # Check regional metrics
        region_metrics = monitor.get_region_metrics("test_region")
        assert region_metrics is not None
        assert region_metrics.total_operations == 1
        assert region_metrics.successful_operations == 1
        assert region_metrics.total_tokens == 150
        assert region_metrics.total_cost == 0.03

        # Check model metrics
        model_metrics = monitor.get_model_metrics("gpt-4")
        assert model_metrics is not None
        assert model_metrics.total_calls == 1
        assert model_metrics.total_tokens == 150
        assert model_metrics.total_cost == 0.03
        assert model_metrics.error_count == 0

    @pytest.mark.asyncio
    async def test_failed_operation_recording(self):
        """Test recording of failed operations."""
        failed_metrics = AIOperationMetrics(
            operation_id="test_failed_op",
            model_name="gpt-4",
            prompt_tokens=100,
            completion_tokens=0,
            total_tokens=100,
            duration_ms=500.0,
            cost=0.02,
            success=False,
            error_type="APIError",
            region="test_region",
            lead_id="test_lead",
        )

        await monitor.record_operation(failed_metrics)

        region_metrics = monitor.get_region_metrics("test_region")
        assert region_metrics.failed_operations == 1
        assert region_metrics.error_rates["APIError"] == 1

        model_metrics = monitor.get_model_metrics("gpt-4")
        assert model_metrics.error_count == 1

    @pytest.mark.asyncio
    async def test_cost_analysis(self, sample_metrics):
        """Test cost analysis functionality."""
        # Record multiple operations
        await monitor.record_operation(sample_metrics)

        # Create and record another metric with different cost
        another_metric = AIOperationMetrics(
            operation_id="test_op_2",
            model_name="gpt-4",
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            duration_ms=1500.0,
            cost=0.06,
            success=True,
            region="test_region",
            lead_id="test_lead_2",
        )
        await monitor.record_operation(another_metric)

        # Get cost analysis
        analysis = monitor.get_cost_analysis(
            start_time=datetime.now() - timedelta(hours=1), region="test_region"
        )

        assert analysis["total_operations"] == 2
        assert analysis["total_tokens"] == 450
        assert analysis["total_cost"] == 0.09
        assert analysis["success_rate"] == 1.0

    def test_anomaly_detection(self, anomaly_detector, sample_metrics):
        """Test anomaly detection system."""
        # Add normal metrics to establish baseline
        for _ in range(5):
            normal_metric = AIOperationMetrics(
                operation_id=f"normal_op_{_}",
                model_name="gpt-4",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                duration_ms=1000.0,
                cost=0.03,
                success=True,
            )
            anomaly_detector.add_metric(normal_metric)

        # Add anomalous metric
        anomalous_metric = AIOperationMetrics(
            operation_id="anomalous_op",
            model_name="gpt-4",
            prompt_tokens=1000,  # 10x normal
            completion_tokens=500,
            total_tokens=1500,
            duration_ms=5000.0,  # 5x normal
            cost=0.30,  # 10x normal
            success=True,
        )

        anomalies = anomaly_detector.detect_anomalies(anomalous_metric)
        assert anomalies["high_token_usage"]
        assert anomalies["high_cost"]
        assert anomalies["high_latency"]

    @pytest.mark.asyncio
    async def test_decorator_usage(self):
        """Test the AI operation tracking decorator."""

        @track_ai_operation(model_name="gpt-4", region="test_region")
        async def test_ai_function():
            return "success", {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "cost": 0.03,
            }

        result = await test_ai_function()
        assert result == "success"

        model_metrics = monitor.get_model_metrics("gpt-4")
        assert model_metrics.total_calls == 1
        assert model_metrics.total_tokens == 150

    @pytest.mark.asyncio
    async def test_high_load_scenario(self):
        """Test monitoring system under high load."""

        async def generate_operation(i: int):
            metric = AIOperationMetrics(
                operation_id=f"load_test_{i}",
                model_name="gpt-4",
                prompt_tokens=random.randint(50, 200),
                completion_tokens=random.randint(25, 100),
                total_tokens=random.randint(75, 300),
                duration_ms=random.uniform(500, 2000),
                cost=random.uniform(0.01, 0.06),
                success=random.random() > 0.1,  # 90% success rate
                region=random.choice(["region_1", "region_2", "region_3"]),
                lead_id=f"lead_{i}",
            )
            await monitor.record_operation(metric)

        # Run 100 concurrent operations
        tasks = [generate_operation(i) for i in range(100)]
        await asyncio.gather(*tasks)

        # Verify metrics were recorded correctly
        all_regions = ["region_1", "region_2", "region_3"]
        total_ops = sum(
            monitor.get_region_metrics(region).total_operations
            for region in all_regions
        )
        assert total_ops == 100

    @pytest.mark.asyncio
    async def test_anomaly_reporting(self, sample_metrics):
        """Test anomaly reporting functionality."""
        # Record normal operations
        await monitor.record_operation(sample_metrics)

        # Record anomalous operation
        anomalous_metrics = AIOperationMetrics(
            operation_id="anomalous_op",
            model_name="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            duration_ms=5000.0,
            cost=0.30,
            success=True,
            region="test_region",
            lead_id="test_lead",
        )
        await monitor.record_operation(anomalous_metrics)

        # Get anomaly report
        report = monitor.get_anomaly_report(
            start_time=datetime.now() - timedelta(hours=1)
        )

        assert len(report) > 0
        assert any(a["anomaly_type"] == "high_token_usage" for a in report)
        assert any(a["anomaly_type"] == "high_cost" for a in report)

    @pytest.mark.asyncio
    async def test_regional_analysis(self):
        """Test regional performance analysis."""
        regions = ["dallas", "austin", "houston"]
        operations_per_region = 10

        # Generate operations for each region
        for region in regions:
            for i in range(operations_per_region):
                metric = AIOperationMetrics(
                    operation_id=f"{region}_op_{i}",
                    model_name="gpt-4",
                    prompt_tokens=random.randint(50, 200),
                    completion_tokens=random.randint(25, 100),
                    total_tokens=random.randint(75, 300),
                    duration_ms=random.uniform(500, 2000),
                    cost=random.uniform(0.01, 0.06),
                    success=random.random() > 0.1,
                    region=region,
                    lead_id=f"{region}_lead_{i}",
                )
                await monitor.record_operation(metric)

        # Verify regional metrics
        for region in regions:
            metrics = monitor.get_region_metrics(region)
            assert metrics.total_operations == operations_per_region
            assert metrics.leads_processed <= operations_per_region
            assert metrics.avg_latency > 0


if __name__ == "__main__":
    pytest.main([__file__])

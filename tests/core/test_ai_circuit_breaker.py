"""
Tests for AI-enhanced circuit breaker implementation.
"""
import pytest
import asyncio
import random
from datetime import datetime, timedelta
from app.core.ai_circuit_breaker import (
    AICircuitBreaker,
    CircuitState,
    FailureEvent,
    AICircuitStats,
    registry,
    ai_circuit_protected,
    CircuitBreakerError
)

[Previous test code remains the same...]

    async def test_persistent_storage(self, circuit):
        """Test circuit state persistence."""
        # Record some state
        await circuit.on_success(0.1, "test_region", 5)
        await circuit.on_failure(
            error=ValueError("test"),
            response_time=0.1,
            retry_count=1,
            priority_level=5,
            region="test_region",
            lead_id="test_lead",
            model_version="test_model"
        )
        
        # Create new instance with same storage
        new_circuit = AICircuitBreaker(
            name="test_circuit",
            failure_threshold=0.5,
            recovery_timeout=1.0,
            persistence_path=":memory:"  # Same in-memory storage
        )
        
        # State should be restored
        assert new_circuit.stats.total_requests == 2
        assert new_circuit.stats.successful_requests == 1
        assert new_circuit.stats.failed_requests == 1

class TestAICircuitStats:
    def test_stats_initialization(self):
        """Test statistics initialization."""
        stats = AICircuitStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert len(stats.recent_failures) == 0
        assert len(stats.state_transitions) == 0

    def test_region_tracking(self):
        """Test region-specific statistics tracking."""
        stats = AICircuitStats()
        
        # Record successes and failures for different regions
        stats.record_success(0.1, "region1", 5)
        stats.record_success(0.2, "region1", 5)
        stats.record_success(0.1, "region2", 5)
        
        stats.record_failure(FailureEvent(
            timestamp=datetime.now(),
            error_type="ValueError",
            response_time=0.1,
            retry_count=1,
            priority_level=5,
            region="region1"
        ))
        
        # Check region stats
        assert stats.region_stats["region1"]["success"] == 2
        assert stats.region_stats["region1"]["failure"] == 1
        assert stats.region_stats["region2"]["success"] == 1
        assert stats.region_stats["region2"]["failure"] == 0

    def test_priority_tracking(self):
        """Test priority-level statistics tracking."""
        stats = AICircuitStats()
        
        # Record operations with different priority levels
        stats.record_success(0.1, "region1", 3)
        stats.record_success(0.1, "region1", 8)
        
        stats.record_failure(FailureEvent(
            timestamp=datetime.now(),
            error_type="ValueError",
            response_time=0.1,
            retry_count=1,
            priority_level=8
        ))
        
        # Check priority stats
        assert stats.priority_stats[3]["success"] == 1
        assert stats.priority_stats[8]["success"] == 1
        assert stats.priority_stats[8]["failure"] == 1

    def test_failure_rate_calculation(self):
        """Test failure rate calculation within time window."""
        stats = AICircuitStats()
        
        # Add some old failures (outside window)
        old_time = datetime.now() - timedelta(seconds=400)
        for _ in range(3):
            stats.record_failure(FailureEvent(
                timestamp=old_time,
                error_type="ValueError",
                response_time=0.1,
                retry_count=1,
                priority_level=5
            ))
        
        # Add recent failures
        for _ in range(2):
            stats.record_failure(FailureEvent(
                timestamp=datetime.now(),
                error_type="ValueError",
                response_time=0.1,
                retry_count=1,
                priority_level=5
            ))
        
        # Only recent failures should count in rate
        failure_rate = stats.get_failure_rate(window_seconds=300)
        assert failure_rate > 0 and failure_rate < 1

    def test_region_failure_rate(self):
        """Test region-specific failure rate calculation."""
        stats = AICircuitStats()
        
        # Add failures and successes for different regions
        stats.record_success(0.1, "region1", 5)
        stats.record_success(0.1, "region1", 5)
        stats.record_failure(FailureEvent(
            timestamp=datetime.now(),
            error_type="ValueError",
            response_time=0.1,
            retry_count=1,
            priority_level=5,
            region="region1"
        ))
        
        # Check region failure rate
        assert stats.get_region_failure_rate("region1") == 1/3
        assert stats.get_region_failure_rate("region2") == 0

@pytest.mark.asyncio
class TestIntegrationScenarios:
    async def test_real_world_scenario(self):
        """Test circuit breaker in a realistic scenario."""
        circuit = AICircuitBreaker(
            name="integration_test",
            failure_threshold=0.5,
            recovery_timeout=1.0,
            half_open_timeout=0.5,
            persistence_path=":memory:"
        )
        
        # Simulate mixed success/failure pattern
        for _ in range(20):
            if random.random() < 0.7:  # 70% success rate
                await circuit.on_success(
                    random.uniform(0.1, 0.5),
                    region=random.choice(["region1", "region2"]),
                    priority=random.randint(1, 10)
                )
            else:
                await circuit.on_failure(
                    error=ValueError("test"),
                    response_time=random.uniform(0.1, 0.5),
                    retry_count=random.randint(0, 2),
                    priority_level=random.randint(1, 10),
                    region=random.choice(["region1", "region2"]),
                    lead_id=f"lead_{random.randint(1, 100)}",
                    model_version=f"model_v{random.randint(1, 3)}"
                )
        
        # Analyze results
        stats = circuit.stats
        assert stats.total_requests == 20
        assert len(stats.region_stats) <= 2
        assert all(p >= 1 and p <= 10 for p in stats.priority_stats.keys())

    async def test_high_load_scenario(self):
        """Test circuit breaker under high load."""
        circuit = AICircuitBreaker(
            name="load_test",
            failure_threshold=0.5,
            recovery_timeout=1.0,
            persistence_path=":memory:"
        )
        
        # Simulate multiple concurrent operations
        async def operation(success: bool):
            if success:
                await circuit.on_success(
                    0.1,
                    region="test_region",
                    priority=5
                )
            else:
                await circuit.on_failure(
                    error=ValueError("test"),
                    response_time=0.1,
                    retry_count=1,
                    priority_level=5,
                    region="test_region",
                    lead_id="test_lead",
                    model_version="test_model"
                )
        
        # Run 100 concurrent operations
        tasks = []
        for i in range(100):
            tasks.append(operation(i % 2 == 0))  # Alternate success/failure
        
        await asyncio.gather(*tasks)
        
        # Verify results
        assert circuit.stats.total_requests == 100
        assert circuit.stats.successful_requests == 50
        assert circuit.stats.failed_requests == 50

    async def test_recovery_scenario(self):
        """Test full circuit recovery scenario."""
        circuit = AICircuitBreaker(
            name="recovery_test",
            failure_threshold=0.5,
            recovery_timeout=1.0,
            half_open_timeout=0.5,
            persistence_path=":memory:"
        )
        
        # Phase 1: Trip the circuit
        for _ in range(10):
            await circuit.on_failure(
                error=ValueError("test"),
                response_time=0.1,
                retry_count=1,
                priority_level=5,
                region="test_region",
                lead_id="test_lead",
                model_version="test_model"
            )
        
        assert circuit._state == CircuitState.OPEN
        
        # Phase 2: Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Phase 3: Successful recovery
        for _ in range(5):
            await circuit.on_success(0.1, "test_region", 5)
            
        # Circuit should be closed after successful recovery
        assert circuit._state == CircuitState.CLOSED

    async def test_adaptive_behavior(self):
        """Test circuit's adaptive behavior based on patterns."""
        circuit = AICircuitBreaker(
            name="adaptive_test",
            failure_threshold=0.5,
            recovery_timeout=1.0,
            persistence_path=":memory:"
        )
        
        # Phase 1: Create pattern of intermittent failures
        for _ in range(20):
            if random.random() < 0.3:  # 30% failure rate
                await circuit.on_failure(
                    error=ValueError("test"),
                    response_time=random.uniform(0.1, 0.5),
                    retry_count=random.randint(0, 2),
                    priority_level=random.randint(1, 10),
                    region="test_region",
                    model_version="test_model"
                )
            else:
                await circuit.on_success(
                    random.uniform(0.1, 0.5),
                    "test_region",
                    random.randint(1, 10)
                )
        
        # Save initial backoff time
        initial_backoff = await circuit._calculate_backoff_time()
        
        # Phase 2: Increase failure frequency
        for _ in range(10):
            await circuit.on_failure(
                error=ValueError("test"),
                response_time=0.1,
                retry_count=1,
                priority_level=8,  # High priority failures
                region="test_region",
                model_version="test_model"
            )
        
        # New backoff should be longer
        new_backoff = await circuit._calculate_backoff_time()
        assert new_backoff > initial_backoff

if __name__ == "__main__":
    pytest.main([__file__])
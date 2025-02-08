"""
Test suite for chat sequence validation
Tests initialization and exit procedures
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.chat.sequence import ChatSequence, SequenceState
from src.chat.validator import SequenceValidator

class TestChatSequence:
    @pytest.fixture
    def sequence(self):
        return ChatSequence(
            history_enabled=True,
            validation_strict=True
        )
        
    @pytest.fixture
    def validator(self):
        return SequenceValidator()
        
    def test_initialization_sequence(self, sequence, validator):
        """Test chat initialization sequence"""
        # Setup test data
        context = {
            "repository": "test-repo",
            "branch": "main",
            "access": "full",
            "history": []
        }
        
        # Run initialization
        result = sequence.initialize(context)
        
        # Validate initialization
        assert result.success
        assert validator.validate_initialization(result)
        assert sequence.state == SequenceState.ACTIVE
        
    def test_exit_sequence(self, sequence, validator):
        """Test chat exit sequence"""
        # Setup active sequence
        sequence.initialize({
            "repository": "test-repo",
            "branch": "main",
            "access": "full",
            "history": []
        })
        
        # Add some history
        sequence.add_interaction("test message")
        
        # Run exit sequence
        result = sequence.exit()
        
        # Validate exit
        assert result.success
        assert validator.validate_exit(result)
        assert sequence.state == SequenceState.CLOSED
        
    def test_continuation_data(self, sequence):
        """Test continuation data preservation"""
        # Initial data
        initial_data = {
            "key": "value",
            "timestamp": datetime.now()
        }
        
        # Set continuation data
        sequence.set_continuation_data(initial_data)
        
        # Get continuation data
        result = sequence.get_continuation_data()
        
        # Verify data preservation
        assert result["key"] == initial_data["key"]
        assert isinstance(result["timestamp"], datetime)
        
    def test_error_recovery(self, sequence, validator):
        """Test error recovery procedures"""
        # Simulate error condition
        sequence.state = SequenceState.ERROR
        
        # Attempt recovery
        recovery_result = sequence.recover()
        
        # Validate recovery
        assert recovery_result.success
        assert validator.validate_recovery(recovery_result)
        assert sequence.state == SequenceState.ACTIVE
        
    def test_validation_failure(self, sequence):
        """Test validation failure handling"""
        # Setup invalid data
        invalid_data = {
            "repository": None,
            "branch": "",
            "access": "invalid"
        }
        
        # Attempt initialization with invalid data
        with pytest.raises(ValueError):
            sequence.initialize(invalid_data)
            
        # Verify error state
        assert sequence.state == SequenceState.ERROR
        
    def test_history_tracking(self, sequence):
        """Test history tracking functionality"""
        # Initialize sequence
        sequence.initialize({
            "repository": "test-repo",
            "branch": "main",
            "access": "full",
            "history": []
        })
        
        # Add interactions
        messages = ["message 1", "message 2", "message 3"]
        for msg in messages:
            sequence.add_interaction(msg)
            
        # Verify history
        history = sequence.get_history()
        assert len(history) == len(messages)
        assert all(msg in str(h) for msg, h in zip(messages, history))
        
    def test_state_transitions(self, sequence):
        """Test state transition validation"""
        # Test valid transitions
        valid_transitions = [
            (SequenceState.INITIAL, SequenceState.ACTIVE),
            (SequenceState.ACTIVE, SequenceState.CLOSING),
            (SequenceState.CLOSING, SequenceState.CLOSED)
        ]
        
        for from_state, to_state in valid_transitions:
            sequence.state = from_state
            sequence.transition_to(to_state)
            assert sequence.state == to_state
            
        # Test invalid transition
        sequence.state = SequenceState.CLOSED
        with pytest.raises(ValueError):
            sequence.transition_to(SequenceState.ACTIVE)
            
    def test_integration_points(self, sequence, validator):
        """Test integration validation points"""
        # Setup test data
        test_points = [
            ("initialization", {"type": "start", "data": {}}),
            ("message_processing", {"type": "process", "data": {}}),
            ("state_change", {"type": "transition", "data": {}}),
            ("exit", {"type": "end", "data": {}})
        ]
        
        # Validate each integration point
        results = []
        for point_name, point_data in test_points:
            result = validator.validate_integration_point(
                point_name,
                point_data,
                sequence.state
            )
            results.append(result)
            
        # Verify all validations passed
        assert all(r.success for r in results)
        
    def test_sequence_recovery(self, sequence):
        """Test sequence recovery from saved state"""
        # Create saved state
        saved_state = {
            "sequence_id": "test-123",
            "repository": "test-repo",
            "branch": "main",
            "timestamp": datetime.now(),
            "history": ["message 1", "message 2"],
            "state": SequenceState.ACTIVE
        }
        
        # Recover sequence
        sequence.recover_from_state(saved_state)
        
        # Verify recovery
        assert sequence.state == saved_state["state"]
        assert len(sequence.get_history()) == len(saved_state["history"])
        
    def test_error_handling(self, sequence):
        """Test error handling procedures"""
        # Test various error conditions
        error_conditions = [
            ("invalid_state", ValueError),
            ("missing_data", KeyError),
            ("validation_error", AssertionError)
        ]
        
        for condition, error_type in error_conditions:
            # Simulate error
            with pytest.raises(error_type):
                sequence.simulate_error(condition)
                
            # Verify error handling
            assert sequence.has_error
            assert sequence.last_error.condition == condition
            
            # Clear error
            sequence.clear_error()
            assert not sequence.has_error
"""
Test suite for the project tracking functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from aiqleads.core.project_tracking import ProjectTracker

@pytest.fixture
def tracker():
    """Create a ProjectTracker instance for testing."""
    return ProjectTracker()

def test_tracker_initialization(tracker):
    """Test that ProjectTracker initializes correctly."""
    assert tracker is not None
    assert tracker.status == "initialized"
    assert isinstance(tracker.start_time, datetime)

def test_start_tracking(tracker):
    """Test starting a new tracking session."""
    tracker.start_tracking("test_component")
    assert tracker.current_component == "test_component"
    assert tracker.status == "active"

def test_pause_tracking(tracker):
    """Test pausing the tracking session."""
    tracker.start_tracking("test_component")
    tracker.pause_tracking()
    assert tracker.status == "paused"
    assert tracker.pause_time is not None

def test_resume_tracking(tracker):
    """Test resuming a paused tracking session."""
    tracker.start_tracking("test_component")
    tracker.pause_tracking()
    tracker.resume_tracking()
    assert tracker.status == "active"
    assert tracker.pause_time is None

def test_stop_tracking(tracker):
    """Test stopping the tracking session."""
    tracker.start_tracking("test_component")
    summary = tracker.stop_tracking()
    assert tracker.status == "completed"
    assert isinstance(summary, dict)
    assert "duration" in summary
    assert "component" in summary

def test_get_current_status(tracker):
    """Test retrieving the current tracking status."""
    status = tracker.get_current_status()
    assert isinstance(status, dict)
    assert "status" in status
    assert "start_time" in status

@pytest.mark.parametrize("invalid_component", [None, "", " ", 123])
def test_invalid_component_name(tracker, invalid_component):
    """Test handling of invalid component names."""
    with pytest.raises(ValueError):
        tracker.start_tracking(invalid_component)

def test_tracking_multiple_components(tracker):
    """Test tracking multiple components sequentially."""
    components = ["component1", "component2", "component3"]
    summaries = []
    
    for component in components:
        tracker.start_tracking(component)
        summary = tracker.stop_tracking()
        summaries.append(summary)
    
    assert len(summaries) == len(components)
    assert all(s["status"] == "completed" for s in summaries)

@patch('aiqleads.core.project_tracking.logging')
def test_logging_functionality(mock_logging, tracker):
    """Test that tracking events are properly logged."""
    tracker.start_tracking("test_component")
    tracker.stop_tracking()
    
    assert mock_logging.info.called
    assert mock_logging.debug.called

def test_error_handling(tracker):
    """Test error handling in tracking operations."""
    # Test stopping without starting
    with pytest.raises(RuntimeError):
        tracker.stop_tracking()
    
    # Test resuming without pausing
    tracker.start_tracking("test_component")
    with pytest.raises(RuntimeError):
        tracker.resume_tracking()

def test_duration_calculation(tracker):
    """Test accurate duration calculation."""
    tracker.start_tracking("test_component")
    with patch('aiqleads.core.project_tracking.datetime') as mock_datetime:
        # Mock a 1-hour duration
        mock_datetime.now.return_value = tracker.start_time.replace(hour=tracker.start_time.hour + 1)
        summary = tracker.stop_tracking()
        assert summary["duration"].total_seconds() == 3600

def test_component_history(tracker):
    """Test tracking history for multiple components."""
    components = ["component1", "component2"]
    
    for component in components:
        tracker.start_tracking(component)
        tracker.stop_tracking()
    
    history = tracker.get_tracking_history()
    assert len(history) == len(components)
    assert all(h["component"] in components for h in history)

@pytest.mark.parametrize("status_change", [
    ("start_tracking", "active"),
    ("pause_tracking", "paused"),
    ("stop_tracking", "completed")
])
def test_status_transitions(tracker, status_change):
    """Test all possible status transitions."""
    action, expected_status = status_change
    
    tracker.start_tracking("test_component")
    if action != "start_tracking":
        getattr(tracker, action)()
        assert tracker.status == expected_status

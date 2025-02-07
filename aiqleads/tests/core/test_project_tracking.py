"""Unit tests for project tracking system."""

import os
import json
import pytest
import shutil
from datetime import datetime
from typing import Dict
from pathlib import Path

from aiqleads.core.project_tracking import ProjectTracker, get_tracker

class TestProjectTracking:
    @pytest.fixture
    def tracker(self, tmp_path) -> ProjectTracker:
        """Create a fresh tracker instance for each test."""
        # Use temporary directory for tests
        test_base = tmp_path / "aiqleads"
        os.makedirs(test_base)
        return ProjectTracker(base_path=str(test_base))
        
    def test_singleton_pattern(self):
        """Test that get_tracker returns the same instance."""
        tracker1 = get_tracker()
        tracker2 = get_tracker()
        assert tracker1 is tracker2
        
    def test_component_registration(self, tracker):
        """Test component registration functionality."""
        # Test valid component registration
        success = tracker.register_component(
            "core/test_component.py",
            "core",
            "Test component"
        )
        assert success
        
        # Verify component was registered
        component = tracker.get_component_status("core/test_component.py")
        assert component is not None
        assert component["type"] == "core"
        assert component["description"] == "Test component"
        assert component["status"] == "registered"
        
        # Test invalid path
        success = tracker.register_component(
            "../invalid/path.py",
            "core",
            "Invalid component"
        )
        assert not success
        
    def test_edge_cases(self, tracker):
        """Test edge cases and error conditions."""
        # Test empty paths
        assert not tracker.register_component("", "core", "Empty path")
        assert not tracker.register_component(" ", "core", "Space path")
        
        # Test path traversal attempts
        assert not tracker.register_component("../../../etc/passwd", "core")
        assert not tracker.register_component("core/../../../etc/passwd", "core")
        assert not tracker.register_component("/etc/passwd", "core")
        
        # Test duplicate registration
        assert tracker.register_component("core/test.py", "core")
        assert not tracker.register_component("core/test.py", "core")
        
        # Test missing status updates
        assert not tracker.update_component_status("missing.py", "active")
        
        # Test invalid component types
        assert not tracker.register_component("core/test2.py", "invalid_type")
        
        # Test special characters in paths
        assert not tracker.register_component("core/test;.py", "core")
        assert not tracker.register_component("core/test*.py", "core")
        
        # Test long paths
        long_path = "core/" + "a" * 255 + ".py"
        assert not tracker.register_component(long_path, "core")
        
        # Test Unicode paths
        assert not tracker.register_component("core/测试.py", "core")
        
    def test_state_persistence(self, tracker, tmp_path):
        """Test state saving and loading."""
        # Register test component
        tracker.register_component("core/persist_test.py", "core")
        
        # Save state
        assert tracker._save_state()
        
        # Create new tracker instance
        new_tracker = ProjectTracker(base_path=str(tmp_path / "aiqleads"))
        
        # Verify state was loaded
        assert "core/persist_test.py".replace("/", ".") in new_tracker.components
        
        # Test corrupt state files
        status_file = tmp_path / "aiqleads/data/project_status.json"
        with open(status_file, 'w') as f:
            f.write("invalid json")
            
        # Should handle corrupt files gracefully
        newer_tracker = ProjectTracker(base_path=str(tmp_path / "aiqleads"))
        assert newer_tracker.current_status["status"] == "initialized"
        
    def test_concurrent_access(self, tracker):
        """Test concurrent component access."""
        # Register initial component
        assert tracker.register_component("core/concurrent.py", "core")
        
        # Simulate concurrent updates
        tracker1 = ProjectTracker(base_path=tracker.base_path)
        tracker2 = ProjectTracker(base_path=tracker.base_path)
        
        # Both try to update same component
        assert tracker1.update_component_status("core/concurrent.py", "active")
        assert tracker2.update_component_status("core/concurrent.py", "inactive")
        
        # Verify last write wins
        component = tracker.get_component_status("core/concurrent.py")
        assert component["status"] == "inactive"
        
    def test_error_recovery(self, tracker, tmp_path):
        """Test error recovery mechanisms."""
        # Register test component
        tracker.register_component("core/recovery_test.py", "core")
        
        # Corrupt data directory
        shutil.rmtree(os.path.join(tracker.base_path, "data"))
        
        # Should recreate directory and continue
        assert tracker.register_component("core/another_test.py", "core")
        
        # Verify data directory was recreated
        assert os.path.exists(os.path.join(tracker.base_path, "data"))
        
    def test_status_history(self, tracker):
        """Test status history management."""
        # Create more than 10 status updates
        component_id = "core/history_test.py"
        tracker.register_component(component_id, "core")
        
        for i in range(15):
            tracker.update_component_status(
                component_id,
                f"status_{i}"
            )
            
        # Verify only last 10 updates kept
        status_data = tracker.export_status("test_status.json")
        assert len(tracker.status_history) <= 10
        
        # Verify chronological order
        for i in range(1, len(tracker.status_history)):
            assert tracker.status_history[i]["timestamp"] > \
                   tracker.status_history[i-1]["timestamp"]
                   
    @pytest.mark.parametrize("test_input,expected", [
        ("core/valid.py", True),
        ("../invalid.py", False),
        ("core/../invalid.py", False),
        ("invalid_dir/test.py", False),
        ("core/test/valid.py", True),
        ("core\\windows\\path.py", True),  # Windows paths
    ])
    def test_path_validation(self, tracker, test_input, expected):
        """Test path validation with various inputs."""
        assert tracker._validate_path(test_input) == expected
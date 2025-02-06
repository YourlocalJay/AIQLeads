"""Unit tests for project tracking system."""

import os
import json
import pytest
from datetime import datetime
from typing import Dict

from aiqleads.core.project_tracking import ProjectTracker, get_tracker

class TestProjectTracking:
    @pytest.fixture
    def tracker(self) -> ProjectTracker:
        """Create a fresh tracker instance for each test."""
        return ProjectTracker(base_path="aiqleads")
        
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
        
    def test_status_updates(self, tracker):
        """Test component status update functionality."""
        # Register a component first
        tracker.register_component(
            "utils/test_util.py",
            "util",
            "Test utility"
        )
        
        # Update its status
        success = tracker.update_component_status(
            "utils/test_util.py",
            "active",
            {"message": "Component activated"}
        )
        assert success
        
        # Verify status update
        component = tracker.get_component_status("utils/test_util.py")
        assert component["status"] == "active"
        assert component["details"]["message"] == "Component activated"
        
        # Test updating non-existent component
        success = tracker.update_component_status(
            "non/existent.py",
            "active"
        )
        assert not success
        
    def test_project_status(self, tracker):
        """Test project status tracking."""
        # Register some components
        components = [
            ("core/comp1.py", "core", "Core component 1"),
            ("core/comp2.py", "core", "Core component 2"),
            ("utils/util1.py", "util", "Utility 1")
        ]
        
        for path, type_, desc in components:
            tracker.register_component(path, type_, desc)
            tracker.update_component_status(path, "active")
            
        # Get project status
        status = tracker.get_project_status()
        
        assert status["components"] == 3
        assert len(status["active_components"]) == 3
        assert status["current_status"]["status"] != "initialized"
        assert status["last_update"] is not None
        
    def test_status_export(self, tracker, tmp_path):
        """Test status export functionality."""
        # Register and update a component
        tracker.register_component(
            "core/test.py",
            "core",
            "Test component"
        )
        tracker.update_component_status(
            "core/test.py",
            "active"
        )
        
        # Export status
        export_path = os.path.join(tmp_path, "status_export.json")
        success = tracker.export_status(export_path)
        assert success
        
        # Verify exported file
        assert os.path.exists(export_path)
        with open(export_path) as f:
            exported = json.load(f)
            
        assert "project_status" in exported
        assert "components" in exported
        assert "history" in exported
        assert len(exported["history"]) <= 10  # Should keep last 10 updates
        
    def test_path_validation(self, tracker):
        """Test path validation functionality."""
        # Valid paths
        assert tracker._validate_path("core/valid.py")
        assert tracker._validate_path("utils/valid.py")
        assert tracker._validate_path("aiqleads/core/valid.py")
        
        # Invalid paths
        assert not tracker._validate_path("../invalid.py")
        assert not tracker._validate_path("/absolute/path.py")
        assert not tracker._validate_path("../../invalid.py")

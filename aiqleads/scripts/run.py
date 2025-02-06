"""
Test runner for project tracking system.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from aiqleads.core.project_tracking import get_tracker
from aiqleads.utils.logging import setup_logger

logger = setup_logger(__name__)

def test_project_tracking():
    """Test the project tracking functionality."""
    try:
        # Initialize tracker
        tracker = get_tracker()
        logger.info("Initialized project tracker")
        
        # Test component registration
        test_components = [
            ("core/project_tracking.py", "core", "Project tracking system"),
            ("utils/logging.py", "util", "Logging utilities"),
            ("scripts/run.py", "script", "Test runner script")
        ]
        
        for path, comp_type, desc in test_components:
            success = tracker.register_component(path, comp_type, desc)
            assert success, f"Failed to register component: {path}"
            logger.info(f"Registered component: {path}")
            
            # Test status update
            success = tracker.update_component_status(
                path, 
                "active",
                {"message": "Component test successful"}
            )
            assert success, f"Failed to update status for: {path}"
            
            # Verify component status
            status = tracker.get_component_status(path)
            assert status["status"] == "active", f"Unexpected status for {path}"
            
        # Export test results
        output_path = os.path.join(project_root, "aiqleads", "tests", "tracking_test_results.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        success = tracker.export_status(output_path)
        assert success, "Failed to export status"
        logger.info(f"Exported test results to: {output_path}")
        
        # Get project status
        status = tracker.get_project_status()
        logger.info("Project Status:")
        logger.info(f"- Components: {status['components']}")
        logger.info(f"- Active Components: {len(status['active_components'])}")
        logger.info(f"- Last Update: {status['last_update']}")
        
        return True
        
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_project_tracking()
    sys.exit(0 if success else 1)

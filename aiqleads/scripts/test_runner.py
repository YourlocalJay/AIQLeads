"""
Test runner script for AIQLeads project tracking system.
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from aiqleads.utils.logging import setup_logger

logger = setup_logger(__name__)

def run_tests():
    """Run project tracking tests."""
    logger.info("Starting AIQLeads project tracking tests")
    
    try:
        # Run pytest
        test_path = os.path.join(project_root, "tests")
        result = pytest.main([
            test_path,
            "-v",
            "--tb=short",
            "--capture=no"  # Show print statements
        ])
        
        if result == 0:
            logger.info("All tests passed successfully!")
            return True
        else:
            logger.error(f"Test execution failed with code: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

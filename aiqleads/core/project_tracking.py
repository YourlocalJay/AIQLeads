"""Core project tracking functionality for AIQLeads MVP
Manages component status, dependencies, and prevents duplicates"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from ..utils.logging import setup_logger
from ..utils.validation import validate_path
from ..utils.database import StatusStore

logger = setup_logger(__name__)

class ComponentStatus:
    NOT_STARTED = "🔴 Not Started"
    IN_PROGRESS = "🟡 In Progress"
    REVIEW = "🟣 In Review"
    TESTING = "🔵 Testing"
    COMPLETED = "🟢 Completed"
    BLOCKED = "⭕ Blocked"

class ProjectTracker:
    """Core project tracking functionality."""
    
    def __init__(self):
        self.store = StatusStore()
        self.load_reference_structure()
    
    def load_reference_structure(self):
        """Load the reference project structure."""
        structure_path = Path(__file__).parent.parent.parent / 'docs' / 'PROJECT_STRUCTURE.md'
        with open(structure_path) as f:
            self.reference_structure = f.read()
    
    def calculate_component_hash(self, component_def: Dict) -> str:
        """Generate unique hash for component functionality."""
        return hashlib.sha256(
            json.dumps(component_def, sort_keys=True).encode()
        ).hexdigest()[:12]
    
    def check_duplicate_functionality(self, component_type: str, 
                                   component_def: Dict) -> Optional[str]:
        """Check if similar functionality already exists."""
        component_hash = self.calculate_component_hash(component_def)
        return self.store.find_duplicate(component_type, component_hash)
    
    def register_component(self, component_type: str, component_id: str, 
                         component_def: Dict) -> bool:
        """Register a new component if no duplicate exists."""
        if not validate_path(component_id, self.reference_structure):
            logger.error(f"Invalid component path: {component_id}")
            return False
            
        duplicate = self.check_duplicate_functionality(component_type, component_def)
        if duplicate:
            logger.warning(
                f"Similar functionality exists in {duplicate}. "
                f"Avoid creating duplicate: {component_id}"
            )
            return False
            
        return self.store.register_component(
            component_type, component_id, component_def
        )
    
    def update_status(self, component_id: str, status: str, 
                     notes: Optional[str] = None) -> bool:
        """Update component status with validation."""
        if not validate_path(component_id, self.reference_structure):
            logger.error(f"Invalid component path: {component_id}")
            return False
            
        return self.store.update_status(component_id, status, notes)
    
    def generate_report(self) -> Dict:
        """Generate current project status report."""
        return self.store.generate_report()
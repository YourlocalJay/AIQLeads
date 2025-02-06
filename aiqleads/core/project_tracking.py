"""
AIQLeads Project Tracking System
Handles component registration, status tracking, and path validation.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class ProjectTracker:
    def __init__(self, base_path: str = "aiqleads"):
        """Initialize the project tracker."""
        self.base_path = base_path
        self.components: Dict[str, Dict] = {}
        self.status_history: List[Dict] = []
        self.current_status: Dict = {
            "status": "initialized",
            "last_update": None,
            "active_component": None
        }
        
        # Load project structure for path validation
        self.project_structure = self._load_project_structure()
        
    def _load_project_structure(self) -> Dict:
        """Load project structure from PROJECT_STRUCTURE.md."""
        try:
            structure_path = os.path.join("docs", "PROJECT_STRUCTURE.md")
            with open(structure_path, 'r') as f:
                content = f.read()
            # Parse the markdown structure (simplified for now)
            return {"root": "aiqleads"}
        except Exception as e:
            logger.error(f"Failed to load project structure: {e}")
            return {"root": "aiqleads"}

    def register_component(self, 
                         component_path: str, 
                         component_type: str,
                         description: str = "") -> bool:
        """
        Register a new component in the tracking system.
        
        Args:
            component_path: Path to the component relative to base_path
            component_type: Type of component (e.g., 'core', 'util', 'script')
            description: Optional description of the component
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            if not self._validate_path(component_path):
                logger.error(f"Invalid component path: {component_path}")
                return False
                
            full_path = os.path.join(self.base_path, component_path)
            component_id = component_path.replace('/', '.')
            
            self.components[component_id] = {
                "path": full_path,
                "type": component_type,
                "description": description,
                "registered_at": datetime.now().isoformat(),
                "status": "registered",
                "last_modified": None
            }
            
            logger.info(f"Registered component: {component_id}")
            self._update_status(f"Component registered: {component_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register component: {e}")
            return False

    def update_component_status(self, 
                              component_path: str, 
                              status: str,
                              details: Optional[Dict] = None) -> bool:
        """
        Update the status of a registered component.
        
        Args:
            component_path: Path to the component
            status: New status to set
            details: Optional status details
            
        Returns:
            bool: True if update successful
        """
        component_id = component_path.replace('/', '.')
        
        if component_id not in self.components:
            logger.error(f"Component not registered: {component_id}")
            return False
            
        try:
            self.components[component_id].update({
                "status": status,
                "last_modified": datetime.now().isoformat(),
                "details": details or {}
            })
            
            self._update_status(f"Component {component_id} status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update component status: {e}")
            return False

    def _validate_path(self, path: str) -> bool:
        """
        Validate a path against the project structure.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path is valid
        """
        if not path.startswith(self.base_path):
            path = os.path.join(self.base_path, path)
            
        # Basic validation - ensure path is within project
        normalized_path = os.path.normpath(path)
        if not normalized_path.startswith(self.base_path):
            return False
            
        # TODO: Add more thorough validation against project_structure
        return True

    def _update_status(self, status_msg: str) -> None:
        """Update the current status and add to history."""
        status_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": status_msg,
            "active_component": self.current_status["active_component"]
        }
        
        self.current_status.update({
            "status": status_msg,
            "last_update": status_entry["timestamp"]
        })
        
        self.status_history.append(status_entry)

    def get_component_status(self, component_path: str) -> Optional[Dict]:
        """Get the current status of a component."""
        component_id = component_path.replace('/', '.')
        return self.components.get(component_id)

    def get_project_status(self) -> Dict:
        """Get the overall project status."""
        return {
            "current_status": self.current_status,
            "components": len(self.components),
            "last_update": self.current_status["last_update"],
            "active_components": [
                k for k, v in self.components.items() 
                if v["status"] in ["active", "in_progress"]
            ]
        }

    def export_status(self, output_path: str) -> bool:
        """Export the current project status to a file."""
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "project_status": self.get_project_status(),
                "components": self.components,
                "history": self.status_history[-10:]  # Last 10 status updates
            }
            
            with open(output_path, 'w') as f:
                json.dump(status_data, f, indent=2)
                
            logger.info(f"Exported status to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export status: {e}")
            return False

# Singleton instance
_project_tracker: Optional[ProjectTracker] = None

def get_tracker(base_path: str = "aiqleads") -> ProjectTracker:
    """Get or create the project tracker instance."""
    global _project_tracker
    if _project_tracker is None:
        _project_tracker = ProjectTracker(base_path)
    return _project_tracker

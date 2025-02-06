"""
AIQLeads Project Tracking System
Handles component registration, status tracking, and path validation.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path

from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class ProjectTracker:
    """Manages project components and their status."""
    
    def __init__(self, base_path: str = "aiqleads"):
        """Initialize the project tracker."""
        self.base_path = base_path
        self.data_dir = os.path.join(base_path, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.components: Dict[str, Dict] = {}
        self.status_history: List[Dict] = []
        self.current_status: Dict = {
            "status": "initialized",
            "last_update": None,
            "active_component": None
        }
        
        # Load project structure for path validation
        self.project_structure = self._load_project_structure()
        
        # Load existing state if available
        self._load_state()
        
    def _load_project_structure(self) -> Dict:
        """Load project structure from PROJECT_STRUCTURE.md."""
        try:
            root = Path(__file__).parent.parent.parent
            structure_path = os.path.join(root, "docs", "PROJECT_STRUCTURE.md")
            if os.path.exists(structure_path):
                with open(structure_path, 'r') as f:
                    content = f.read()
                # Parse the markdown structure (simplified for now)
                return {"root": self.base_path}
            return {"root": self.base_path}
        except Exception as e:
            logger.error(f"Failed to load project structure: {e}")
            return {"root": self.base_path}
            
    def _load_state(self) -> None:
        """Load existing state from data files."""
        try:
            status_file = os.path.join(self.data_dir, "project_status.json")
            registry_file = os.path.join(self.data_dir, "component_registry.json")
            
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    self.current_status = data.get("project_status", self.current_status)
                    self.status_history = data.get("status_history", [])
                    
            if os.path.exists(registry_file):
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    self.components = data.get("components", {})
                    
        except Exception as e:
            logger.error(f"Failed to load existing state: {e}")
            
    def _save_state(self) -> bool:
        """Save current state to data files."""
        try:
            # Save project status
            status_data = {
                "version": "0.1.0",
                "last_update": datetime.now().isoformat(),
                "project_status": self.current_status,
                "status_history": self.status_history[-10:]  # Keep last 10 updates
            }
            
            status_file = os.path.join(self.data_dir, "project_status.json")
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
            # Save component registry
            registry_data = {
                "version": "0.1.0",
                "last_update": datetime.now().isoformat(),
                "components": self.components
            }
            
            registry_file = os.path.join(self.data_dir, "component_registry.json")
            with open(registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

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
                
            # Check for duplicates
            if self._get_component_id(component_path) in self.components:
                logger.error(f"Component already registered: {component_path}")
                return False
                
            full_path = os.path.join(self.base_path, component_path)
            component_id = self._get_component_id(component_path)
            
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
            self._save_state()
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
        component_id = self._get_component_id(component_path)
        
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
            self._save_state()
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
            
        # Check for directory traversal
        if '..' in normalized_path:
            return False
            
        # Ensure path matches project structure
        allowed_dirs = ['core', 'utils', 'scripts', 'data', 'tests']
        path_parts = Path(path).parts
        if len(path_parts) > 1:
            if path_parts[1] not in allowed_dirs:
                return False
                
        return True

    def _get_component_id(self, path: str) -> str:
        """Generate a unique component ID from path."""
        return path.replace('/', '.')

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
        component_id = self._get_component_id(component_path)
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
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
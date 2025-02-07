"""
Project tracking implementation for AIQLeads chat sessions.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

class ProjectTracker:
    """
    Handles project state tracking, status updates, and continuation management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.status_file = Path("current_status.json")
        self.session_file = Path("last_session.md")
        self.tracking_file = Path("project_tracking.log")
        self._initialize_logging()
    
    def _initialize_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            filename=self.tracking_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start_session(self) -> None:
        """Initialize a new tracking session."""
        self.logger.info("Starting new tracking session")
        self._load_current_status()
    
    def _load_current_status(self) -> Dict:
        """Load current project status."""
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("No existing status file found")
            return self._create_initial_status()
    
    def _create_initial_status(self) -> Dict:
        """Create initial status structure."""
        initial_status = {
            "last_update": datetime.now().isoformat(),
            "components": {},
            "active_branch": "main",
            "last_component": None,
            "next_task": None
        }
        self._save_status(initial_status)
        return initial_status
    
    def _save_status(self, status: Dict) -> None:
        """Save current status to file."""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def update_status(
        self,
        component_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Update status for a specific component.
        
        Args:
            component_id: Path or identifier of the component
            status: Current status of the component
            notes: Optional notes about the status update
        """
        current_status = self._load_current_status()
        
        current_status["components"][component_id] = {
            "status": status,
            "last_update": datetime.now().isoformat(),
            "notes": notes
        }
        
        current_status["last_component"] = component_id
        self._save_status(current_status)
        self.logger.info(f"Updated status for {component_id}: {status}")
    
    def check_duplicate_functionality(
        self,
        component_type: str,
        component_def: Dict
    ) -> bool:
        """
        Check for duplicate component implementations.
        
        Args:
            component_type: Type of component to check
            component_def: Component definition to compare
            
        Returns:
            bool: True if duplicates found
        """
        current_status = self._load_current_status()
        
        for comp_id, comp_info in current_status["components"].items():
            if (
                comp_info.get("type") == component_type
                and comp_info.get("definition") == component_def
            ):
                self.logger.warning(
                    f"Duplicate functionality found: {comp_id}"
                )
                return True
        return False
    
    def generate_report(self) -> Dict:
        """
        Generate current status report.
        
        Returns:
            Dict containing current project status
        """
        current_status = self._load_current_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": current_status,
            "active_components": [
                comp_id for comp_id, comp_info 
                in current_status["components"].items()
                if comp_info["status"] == "active"
            ],
            "next_task": current_status["next_task"]
        }
    
    def verify_component(self, component_info: Dict) -> bool:
        """
        Verify component state matches expected state.
        
        Args:
            component_info: Dict containing component path and expected state
            
        Returns:
            bool: True if verification passes
        """
        current_status = self._load_current_status()
        component_id = component_info["path"]
        
        if component_id not in current_status["components"]:
            self.logger.error(f"Component not found: {component_id}")
            return False
            
        actual_state = current_status["components"][component_id]
        expected_state = component_info["expected_state"]
        
        if actual_state != expected_state:
            self.logger.error(
                f"State mismatch for {component_id}:"
                f"Expected {expected_state}, got {actual_state}"
            )
            return False
            
        return True
    
    def log_activity(self, activity_data: Dict) -> None:
        """
        Log specific activity data.
        
        Args:
            activity_data: Dictionary containing activity details
        """
        self.logger.info(
            f"Activity: {activity_data['activity']} - "
            f"Status: {activity_data['status']}"
        )
    
    def generate_continuation_message(self) -> str:
        """
        Generate continuation message for next session.
        
        Returns:
            str: Formatted continuation message
        """
        status = self._load_current_status()
        
        template = self._load_continuation_template()
        return template.format(
            branch=status.get("active_branch", "main"),
            last_component=status.get("last_component", "None"),
            current_status=status.get("status", "Unknown"),
            next_task=status.get("next_task", "None")
        )
    
    def _load_continuation_template(self) -> str:
        """Load continuation message template."""
        return '''
I'm continuing work on the AIQLeads project. IMPORTANT: This is an existing project with an established structure - do not create new root directories or modify the structure. All changes must be made within the existing structure.

First, please review these files in order:
1. aiqleads/docs/CONTINUATION_PROCEDURE.md
2. aiqleads/docs/UNIVERSAL_PROMPT.md
3. docs/PROJECT_STRUCTURE.md
4. REPOSITORY_STATUS.md

CRITICAL RULES:
- All changes must be inside the aiqleads/ directory
- Never modify the core project structure
- Never create alternate versions of existing files
- Use project_tracking.py for all status updates
- Always validate paths against PROJECT_STRUCTURE.md

Repository Information:
* GitHub Repository: https://github.com/YourlocalJay/AIQLeads
* Owner: YourlocalJay
* Access Type: Private repository
* Branch: {branch}

Current Status:
- Branch: {branch}
- Last Component: {last_component}
- Status: {current_status}
- Next Task: {next_task}

Recent Changes:
1. [Most recent change]
2. [Second most recent change]
3. [Third most recent change]

Development Focus:
- Primary Goal: [Goal]
- Components: [Components]
- Requirements: [Requirements]
'''
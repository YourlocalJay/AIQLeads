"""
Template generation system for AIQLeads
Handles all template and sequence generation
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
from ..utils.validation import validate_data, validate_file_path
from ..utils.logging import log_operation

class TemplateGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_dir = "aiqleads"
        self.end_trigger = "End of chat"
        self.templates = {
            "chat_end": self._load_template("chat_end"),
            "chat_start": self._load_template("chat_start")
        }
        
    def should_generate_end_sequence(self, message: str) -> bool:
        """Check if message should trigger end sequence"""
        return message.strip().lower() == self.end_trigger.lower()
        
    def generate_start_sequence(self, repository: Dict[str, str]) -> str:
        """Generate start sequence with repository info and required reading"""
        return f"""# Prompt for Next Chat
Please continue with repository: {repository.get('repo_url')}
- Branch: {repository.get('branch')}
- Owner: {repository.get('owner')}
- Access: {repository.get('access')}

Required Reading:
- aiqleads/docs/FILE_STRUCTURE_GUIDELINES.md - understand directory structure
- aiqleads/docs/CONTINUATION_PROCEDURE.md - review chat protocols
- aiqleads/data/project_status.json - check current state"""
        
    def generate_end_sequence(self, state: Dict[str, Any]) -> str:
        """Generate standardized end sequence using existing file structure"""
        try:
            # Validate state data and file paths
            if not validate_data(state, "end_sequence"):
                raise ValueError("Invalid state data")
                
            # Ensure all paths are within aiqleads directory
            self._validate_paths(state)
                
            # Load current project status from correct path
            status_path = os.path.join(self.base_dir, "data", "project_status.json")
            if not os.path.exists(status_path):
                raise FileNotFoundError(f"Project status file not found at {status_path}")
                
            with open(status_path, "r") as f:
                status = json.load(f)
                
            # Format template sections
            sections = {
                "repository": self._format_repository_section(state),
                "required_reading": self._format_required_reading()
            }
            
            # Generate continuation prompt
            template = self.templates["chat_end"]
            continuation = template.format(**sections)
            
            # Update project status
            self._update_project_status(status, state)
            
            # Log successful generation
            log_operation("end_sequence_generation", {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "sections": list(sections.keys())
            })
            
            return continuation
            
        except Exception as e:
            self.logger.error(f"Error generating end sequence: {e}")
            return self._generate_safe_continuation(state, str(e))
            
    def _validate_paths(self, state: Dict[str, Any]) -> None:
        """Ensure all paths are within aiqleads directory"""
        for path in state.get("active_files", []):
            if not validate_file_path(path, self.base_dir):
                raise ValueError(f"Invalid file path: {path} - Must be within {self.base_dir}/")
            
    def _format_repository_section(self, state: Dict[str, Any]) -> str:
        """Format repository information section"""
        required_fields = ["repo_url", "branch", "owner", "access"]
        for field in required_fields:
            if field not in state:
                self.logger.warning(f"Missing required field: {field}")
                state[field] = "UNKNOWN"
                
        return f"""Please continue with repository: {state['repo_url']}
- Branch: {state['branch']}
- Owner: {state['owner']}
- Access: {state['access']}"""

    def _format_required_reading(self) -> str:
        """Format required reading section"""
        return """Required Reading:
- aiqleads/docs/FILE_STRUCTURE_GUIDELINES.md - understand directory structure
- aiqleads/docs/CONTINUATION_PROCEDURE.md - review chat protocols
- aiqleads/data/project_status.json - check current state"""
            
    def _update_project_status(self, status: Dict[str, Any], state: Dict[str, Any]) -> None:
        """Update project status file with latest state"""
        status_path = os.path.join(self.base_dir, "data", "project_status.json")
        
        # Update timestamp
        status["last_updated"] = datetime.now().isoformat()
        
        # Update active files
        if "current_state" not in status:
            status["current_state"] = {}
        status["current_state"]["active_files"] = [
            f for f in state.get("active_files", [])
            if validate_file_path(f, self.base_dir)
        ]
        
        # Write updated status
        with open(status_path, "w") as f:
            json.dump(status, f, indent=4)
        
    def _load_template(self, template_name: str) -> str:
        """Load template from file"""
        templates = {
            "chat_end": """# Prompt for Next Chat
{repository}

{required_reading}""",
            "chat_start": """# Prompt for Next Chat
{repository}

{required_reading}"""
        }
        return templates.get(template_name, "")
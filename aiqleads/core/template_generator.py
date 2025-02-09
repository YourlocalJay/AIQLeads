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
            "chat_start": self._load_template("chat_start"),
            "continuation": self._load_template("continuation")
        }
        
    def should_generate_end_sequence(self, message: str) -> bool:
        """Check if message should trigger end sequence"""
        return message.strip().lower() == self.end_trigger.lower()
        
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
                "status": self._format_status_section(status),
                "tasks": self._format_tasks_section(status),
                "requirements": self._format_requirements_section(status),
                "files": self._format_files_section()
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
            
    def generate_start_sequence(self, state: Dict[str, Any]) -> str:
        """Generate standardized start sequence for new chats"""
        try:
            status_path = os.path.join(self.base_dir, "data", "project_status.json")
            with open(status_path, "r") as f:
                status = json.load(f)
                
            return f"""Please continue with repository: {state.get('repo_url')}
- Branch: {state.get('branch')}
- Owner: {state.get('owner')}
- Access: {state.get('access')}

Required Reading:
- {status.get('current_state', {}).get('active_files', [])[0]}  # Primary file
"""
        except Exception as e:
            self.logger.error(f"Error generating start sequence: {e}")
            return f"""Please continue with repository: {state.get('repo_url', 'UNKNOWN')}
- Branch: {state.get('branch', 'UNKNOWN')}
- Owner: {state.get('owner', 'UNKNOWN')}
- Access: {state.get('access', 'UNKNOWN')}"""
            
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
        
    def _format_status_section(self, status: Dict[str, Any]) -> str:
        """Format current status section using existing status"""
        completed = status.get("completed", [])
        current = status.get("current_state", {})
        
        status_lines = []
        for item in completed[-3:]:  # Show last 3 completed items
            status_lines.append(f"- {item}")
        
        if current:
            desc = current.get("description", "").strip()
            if desc:
                status_lines.append(f"- Current: {desc}")
                
        return "\n".join(status_lines)
        
    def _format_tasks_section(self, status: Dict[str, Any]) -> str:
        """Format next tasks section from status"""
        pending = status.get("pending", [])
        return "\n".join(f"- {task}" for task in pending)
        
    def _format_requirements_section(self, status: Dict[str, Any]) -> str:
        """Format critical requirements section from status"""
        requirements = status.get("critical_notes", [
            "Always use aiqleads/ directory structure",
            "Update existing files instead of creating new ones",
            "Follow FILE_STRUCTURE_GUIDELINES.md"
        ])
        return "\n".join(f"- {req}" for req in requirements)
        
    def _format_files_section(self) -> str:
        """Format files of interest section from registry"""
        registry_path = os.path.join(self.base_dir, "data", "component_registry.json")
        
        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)
                
            # Get active components
            active = registry.get("active_components", [])
            
            # Validate all paths
            valid_files = [
                file for file in active 
                if validate_file_path(file, self.base_dir)
            ]
            
            return "\n".join(f"- {file}" for file in valid_files)
            
        except FileNotFoundError:
            self.logger.error(f"Component registry not found at {registry_path}")
            return "- No active files found"
            
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

Current Status:
{status}

Next Tasks:
{tasks}

Critical Requirements:
{requirements}

Files of Interest:
{files}""",
            "chat_start": """Please continue with repository: {repo_url}
- Branch: {branch}
- Owner: {owner}
- Access: {access}

Required Reading:
- {primary_file}"""
        }
        return templates.get(template_name, "")
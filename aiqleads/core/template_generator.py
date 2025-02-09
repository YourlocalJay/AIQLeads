"""
Template generation system for AIQLeads
Handles all template and sequence generation
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from ..utils.validation import validate_data
from ..utils.logging import log_operation

class TemplateGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = {
            "chat_end": self._load_template("chat_end"),
            "chat_start": self._load_template("chat_start"),
            "continuation": self._load_template("continuation")
        }
        
    def generate_end_sequence(self, state: Dict[str, Any]) -> str:
        """Generate standardized end sequence"""
        try:
            # Validate state data
            if not validate_data(state, "end_sequence"):
                raise ValueError("Invalid state data")
                
            # Load current project status
            with open("aiqleads/data/project_status.json", "r") as f:
                status = json.load(f)
                
            # Format template sections
            sections = {
                "repository": self._format_repository_section(state),
                "status": self._format_status_section(status),
                "tasks": self._format_tasks_section(status),
                "requirements": self._format_requirements_section(),
                "files": self._format_files_section()
            }
            
            # Generate continuation prompt
            template = self.templates["chat_end"]
            continuation = template.format(**sections)
            
            # Log generation
            log_operation("end_sequence_generation", {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "sections": list(sections.keys())
            })
            
            return continuation
            
        except Exception as e:
            self.logger.error(f"Error generating end sequence: {e}")
            return self._generate_safe_continuation(state, str(e))
            
    def _format_repository_section(self, state: Dict[str, Any]) -> str:
        """Format repository information section"""
        return f"""Please continue with repository: {state.get('repo_url')}
- Branch: {state.get('branch')}
- Owner: {state.get('owner')}
- Access: {state.get('access')}"""
        
    def _format_status_section(self, status: Dict[str, Any]) -> str:
        """Format current status section"""
        completed = status.get("completed", [])
        current = status.get("current_state", {})
        
        status_lines = []
        for item in completed:
            status_lines.append(f"- {item}")
        
        if current:
            status_lines.append(f"- Current: {current.get('description', '')}")
            
        return "\n".join(status_lines)
        
    def _format_tasks_section(self, status: Dict[str, Any]) -> str:
        """Format next tasks section"""
        pending = status.get("pending", [])
        return "\n".join(f"- {task}" for task in pending)
        
    def _format_requirements_section(self) -> str:
        """Format critical requirements section"""
        requirements = [
            "Preserve all content",
            "No rewrites, only updates",
            "Add without removing",
            "Maintain history",
            "Use existing AIQLeads file structure",
        ]
        return "\n".join(f"- {req}" for req in requirements)
        
    def _format_files_section(self) -> str:
        """Format files of interest section"""
        # Load component registry
        with open("aiqleads/data/component_registry.json", "r") as f:
            registry = json.load(f)
            
        # Get active components
        active = registry.get("active_components", [])
        return "\n".join(f"- {file}" for file in active)
        
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
{files}

End of Chat."""
        }
        return templates.get(template_name, "")
        
    def _generate_safe_continuation(self, state: Dict[str, Any], error: str) -> str:
        """Generate safe continuation for error cases"""
        return f"""# Prompt for Next Chat
Please continue with repository: {state.get('repo_url', 'UNKNOWN')}
- Branch: {state.get('branch', 'UNKNOWN')}
- Owner: {state.get('owner', 'UNKNOWN')}
- Access: {state.get('access', 'UNKNOWN')}

Current Status:
- Error occurred: {error}
- Recovery needed

Next Tasks:
- Resolve end sequence error
- Verify system state
- Complete pending operations

Critical Requirements:
- Preserve all content
- Use existing file structure
- Maintain history
- Add without removing

End of Chat."""
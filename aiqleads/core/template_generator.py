"""
Template generator for AIQLeads chat sessions.
Handles creation of continuation messages and session documentation.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class TemplateGenerator:
    """
    Generates standardized templates for chat sessions.
    """
    
    def __init__(self):
        self.status_file = Path("current_status.json")
        self.template_dir = Path("templates")
        self._ensure_templates_exist()
    
    def _ensure_templates_exist(self) -> None:
        """Ensure all required templates exist."""
        self.template_dir.mkdir(exist_ok=True)
        
        templates = {
            "continuation": self._default_continuation_template(),
            "session_summary": self._default_session_template(),
            "status_update": self._default_status_template()
        }
        
        for name, content in templates.items():
            template_file = self.template_dir / f"{name}.txt"
            if not template_file.exists():
                template_file.write_text(content)
    
    def _default_continuation_template(self) -> str:
        """Default continuation message template."""
        return '''I'm continuing work on the AIQLeads project. IMPORTANT: This is an existing project with an established structure - do not create new root directories or modify the structure. All changes must be made within the existing structure.

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
* GitHub Repository: {repo_url}
* Owner: {owner}
* Access Type: {access_type}
* Branch: {branch}

Current Status:
- Branch: {branch}
- Last Component: {last_component}
- Status: {current_status}
- Next Task: {next_task}

Recent Changes:
{recent_changes}

Development Focus:
- Primary Goal: {goal}
- Components: {components}
- Requirements: {requirements}'''
    
    def _default_session_template(self) -> str:
        """Default session summary template."""
        return '''### {date}
#### Session Summary
- Completed: {completed}
- Current State: {current_state}
- Next Steps: {next_steps}
- Known Issues: {known_issues}'''
    
    def _default_status_template(self) -> str:
        """Default status update template."""
        return '''Component: {component_id}
Status: {status}
Last Update: {timestamp}
Notes: {notes}
Next Steps: {next_steps}'''
    
    def generate_continuation_message(
        self,
        status_data: Dict,
        recent_changes: List[str]
    ) -> str:
        """
        Generate continuation message from current status.
        
        Args:
            status_data: Current project status
            recent_changes: List of recent changes
            
        Returns:
            str: Formatted continuation message
        """
        template_file = self.template_dir / "continuation.txt"
        template = template_file.read_text()
        
        changes_formatted = "\n".join(
            f"{i+1}. {change}" for i, change in enumerate(recent_changes)
        )
        
        return template.format(
            repo_url=status_data.get("repo_url"),
            owner=status_data.get("owner"),
            access_type=status_data.get("access_type"),
            branch=status_data.get("branch"),
            last_component=status_data.get("last_component"),
            current_status=status_data.get("status"),
            next_task=status_data.get("next_task"),
            recent_changes=changes_formatted,
            goal=status_data.get("goal"),
            components=status_data.get("components"),
            requirements=status_data.get("requirements")
        )
    
    def generate_session_summary(
        self,
        completed: List[str],
        current_state: str,
        next_steps: List[str],
        known_issues: List[str]
    ) -> str:
        """
        Generate session summary.
        
        Args:
            completed: List of completed items
            current_state: Current state description
            next_steps: List of next steps
            known_issues: List of known issues
            
        Returns:
            str: Formatted session summary
        """
        template_file = self.template_dir / "session_summary.txt"
        template = template_file.read_text()
        
        return template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            completed="\n- ".join(completed),
            current_state=current_state,
            next_steps="\n- ".join(next_steps),
            known_issues="\n- ".join(known_issues)
        )
    
    def generate_status_update(
        self,
        component_id: str,
        status: str,
        notes: str,
        next_steps: List[str]
    ) -> str:
        """
        Generate status update.
        
        Args:
            component_id: Component identifier
            status: Current status
            notes: Status notes
            next_steps: List of next steps
            
        Returns:
            str: Formatted status update
        """
        template_file = self.template_dir / "status_update.txt"
        template = template_file.read_text()
        
        return template.format(
            component_id=component_id,
            status=status,
            timestamp=datetime.now().isoformat(),
            notes=notes,
            next_steps="\n- ".join(next_steps)
        )
    
    def load_custom_template(self, template_name: str) -> Optional[str]:
        """
        Load a custom template.
        
        Args:
            template_name: Name of template to load
            
        Returns:
            str: Template content if exists, None otherwise
        """
        template_file = self.template_dir / f"{template_name}.txt"
        if template_file.exists():
            return template_file.read_text()
        return None
    
    def save_custom_template(
        self,
        template_name: str,
        content: str
    ) -> None:
        """
        Save a custom template.
        
        Args:
            template_name: Name for the template
            content: Template content
        """
        template_file = self.template_dir / f"{template_name}.txt"
        template_file.write_text(content)
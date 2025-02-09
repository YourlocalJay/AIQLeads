"""
Chat end sequence implementation
Ensures consistent chat termination
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

class EndSequenceError(Exception):
    """Base class for end sequence errors"""
    pass

class StateError(EndSequenceError):
    """Error in system state"""
    pass

class DataError(EndSequenceError):
    """Error in data consistency"""
    pass

class ResourceError(EndSequenceError):
    """Error in resource management"""
    pass

class ChatEndSequence:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pending_operations = set()
        self.resources = set()
        self.state = {}
        
    def validate_end_conditions(self) -> bool:
        """Validate system state for end sequence"""
        # Check pending operations
        if self.pending_operations:
            raise StateError(f"Cannot end chat with pending operations: {self.pending_operations}")
            
        # Check data consistency
        if not self._verify_data_consistency():
            raise DataError("Data inconsistency detected")
            
        # Check resources
        if self.resources:
            raise ResourceError(f"Unclosed resources detected: {self.resources}")
            
        return True
        
    def collect_state(self) -> Dict[str, Any]:
        """Collect current system state"""
        return {
            "repository": {
                "url": self.state.get("repo_url"),
                "branch": self.state.get("branch"),
                "owner": self.state.get("owner"),
                "access": self.state.get("access_type")
            },
            "status": {
                "completed": self._list_completed_tasks(),
                "pending": self._list_pending_tasks(),
                "current": self._get_current_state()
            },
            "context": {
                "files": self._list_relevant_files(),
                "critical_rules": self._get_critical_rules(),
                "requirements": self._get_requirements()
            }
        }
        
    def generate_continuation(self) -> str:
        """Generate continuation prompt"""
        state = self.collect_state()
        
        # Format repository section
        repo_section = f"""# Prompt for Next Chat
Please continue with repository: {state['repository']['url']}
- Branch: {state['repository']['branch']}
- Owner: {state['repository']['owner']} 
- Access: {state['repository']['access']}"""

        # Format status section
        status = state['status']
        status_section = "\nCurrent Status:"
        for item in self._format_status(status):
            status_section += f"\n- {item}"
            
        # Format tasks section
        tasks_section = "\nNext Tasks:"
        for task in self._format_tasks(status['pending']):
            tasks_section += f"\n- {task}"
            
        # Format requirements section
        reqs_section = "\nCritical Requirements:"
        for rule in self._format_rules(state['context']['critical_rules']):
            reqs_section += f"\n- {rule}"
            
        # Format files section
        files_section = "\nFiles of Interest:"
        for file in self._format_files(state['context']['files']):
            files_section += f"\n- {file}"
            
        # Combine all sections
        continuation = f"""{repo_section}
{status_section}
{tasks_section}
{reqs_section}
{files_section}

End of Chat."""
        
        return continuation
        
    def execute_end_sequence(self) -> str:
        """Execute complete end sequence"""
        try:
            # Validate end conditions
            self.validate_end_conditions()
            
            # Collect final state
            state = self.collect_state()
            
            # Generate continuation data
            continuation = self.generate_continuation()
            
            # Cleanup resources
            self._cleanup_resources()
            
            # Final state verification
            self._verify_clean_state()
            
            return continuation
            
        except Exception as e:
            return self._handle_end_sequence_error(e)
            
    def _verify_data_consistency(self) -> bool:
        """Verify data consistency"""
        try:
            # Check state completeness
            required_fields = {"repo_url", "branch", "owner", "access_type"}
            if not all(field in self.state for field in required_fields):
                return False
                
            # Check status consistency
            if not self._verify_status_consistency():
                return False
                
            # Check context consistency
            if not self._verify_context_consistency():
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Data consistency check failed: {e}")
            return False
            
    def _cleanup_resources(self) -> None:
        """Clean up system resources"""
        for resource in self.resources:
            try:
                self.logger.info(f"Cleaning up resource: {resource}")
                # Resource cleanup logic here
                self.resources.remove(resource)
            except Exception as e:
                self.logger.error(f"Failed to cleanup resource {resource}: {e}")
                
    def _verify_clean_state(self) -> bool:
        """Verify clean system state"""
        return (
            len(self.pending_operations) == 0 and
            len(self.resources) == 0 and
            self._verify_data_consistency()
        )
        
    def _handle_end_sequence_error(self, error: Exception) -> str:
        """Handle end sequence errors"""
        self.logger.error(f"End sequence error: {error}")
        
        try:
            # Emergency cleanup
            self._emergency_cleanup()
            
            # Generate safe continuation
            return self._generate_safe_continuation(error)
            
        except Exception as e:
            self.logger.critical(f"Failed to handle end sequence error: {e}")
            return self._generate_minimal_continuation()
            
    def _generate_safe_continuation(self, error: Exception) -> str:
        """Generate continuation data for error case"""
        return f"""# Prompt for Next Chat
Please continue with repository: {self.state.get('repo_url', 'UNKNOWN')}
- Branch: {self.state.get('branch', 'UNKNOWN')}
- Owner: {self.state.get('owner', 'UNKNOWN')}
- Access: {self.state.get('access_type', 'UNKNOWN')}

Current Status:
- Error occurred during end sequence: {str(error)}
- Clean termination required

Next Tasks:
- Resolve end sequence error
- Verify system state
- Complete pending operations

Critical Requirements:
- Preserve all content
- No rewrites, only updates
- Maintain history
- Add without removing

End of Chat."""
        
    def _generate_minimal_continuation(self) -> str:
        """Generate minimal continuation for severe errors"""
        return """# Prompt for Next Chat
ERROR: End sequence failed
- Repository state unclear
- Manual verification required
- System recovery needed

End of Chat."""
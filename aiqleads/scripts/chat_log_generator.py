#!/usr/bin/env python3
import os
import json
import datetime
import git
import hashlib
import yaml

class ChatLogGenerator:
    SUPPORTED_MODELS = [
        'Claude 3.5 Haiku',
        'Claude 3.5 Sonnet',
        'Claude 3 Opus'
    ]

    def __init__(self, repo_path):
        """
        Initialize the chat log generator with repository context
        
        :param repo_path: Path to the git repository
        """
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        self.logs_dir = os.path.join(repo_path, 'aiqleads', 'logs', 'claude_chats')
        
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def validate_model(self, model):
        """
        Validate that the provided model is supported
        
        :param model: LLM model name
        :return: Validated model name or raise ValueError
        """
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported Claude model. Supported models are: {', '.join(self.SUPPORTED_MODELS)}")
        return model
    
    def generate_unique_chat_id(self):
        """
        Generate a unique identifier for the chat session
        
        :return: Unique chat identifier
        """
        current_time = datetime.datetime.now()
        return hashlib.md5(
            f"{current_time.isoformat()}_AIQLeads_Chat".encode()
        ).hexdigest()[:12]
    
    def track_file_changes(self):
        """
        Track changes in the repository
        
        :return: Dictionary of file changes
        """
        changes = {
            'added': [],
            'modified': [],
            'deleted': []
        }
        
        # Get diff between current and previous commit
        if len(list(self.repo.commits)) > 1:
            diff = self.repo.commits[0].diff(self.repo.commits[1])
            
            for change in diff:
                if change.change_type == 'A':
                    changes['added'].append(change.b_path)
                elif change.change_type == 'M':
                    changes['modified'].append(change.b_path)
                elif change.change_type == 'D':
                    changes['deleted'].append(change.b_path)
        
        return changes
    
    def generate_log_entry(self, 
                            llm_model='Claude 3.5 Sonnet', 
                            chat_title='Unnamed Development Chat', 
                            primary_focus='General Development'):
        """
        Generate a comprehensive log entry
        
        :param llm_model: Name of the LLM model used
        :param chat_title: Title or context of the chat
        :param primary_focus: Main area of development
        :return: Markdown log entry
        """
        # Validate model
        validated_model = self.validate_model(llm_model)
        
        current_time = datetime.datetime.now()
        file_changes = self.track_file_changes()
        chat_id = self.generate_unique_chat_id()
        
        # Calculate code impact
        def count_lines(file_path):
            try:
                with open(os.path.join(self.repo_path, file_path), 'r') as f:
                    return len(f.readlines())
            except Exception:
                return 0
        
        lines_added = sum(count_lines(f) for f in file_changes['added'])
        lines_modified = sum(count_lines(f) for f in file_changes['modified'])
        
        log_content = f"""# Claude Development Chat Log

## Metadata
- **Timestamp**: {current_time.isoformat()}
- **LLM Model**: {validated_model}
- **Chat ID**: {chat_id}
- **Chat Title**: {chat_title}
- **Primary Development Focus**: {primary_focus}

## Changes Made

### Files Added
{self._format_file_list(file_changes['added'])}

### Files Modified
{self._format_file_list(file_changes['modified'])}

### Files Deleted
{self._format_file_list(file_changes['deleted'])}

## Technical Details
- **Lines of Code Added**: {lines_added}
- **Lines of Code Modified**: {lines_modified}
- **Total Project Impact**: {'Significant' if lines_added + lines_modified > 100 else 'Minor'}

## Model Usage Notes
- Default model for this development session
- Switched due to usage limits or specific requirements

## Next Recommended Actions
- Review changes thoroughly
- Update project documentation
- Validate implementation details

## Potential Risks/Considerations
- Ensure compatibility across different Claude models
- Validate code consistency

---
"""
        return log_content
    
    def _format_file_list(self, file_list):
        """
        Format file list for markdown
        
        :param file_list: List of files
        :return: Formatted markdown list
        """
        if not file_list:
            return "- *No files*"
        
        return "\n".join(f"- `{f}`" for f in file_list)
    
    def save_log(self, log_content):
        """
        Save log to a markdown file
        
        :param log_content: Markdown log content
        """
        filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}_claude_chat_log.md"
        filepath = os.path.join(self.logs_dir, filename)
        
        with open(filepath, 'w') as log_file:
            log_file.write(log_content)
        
        # Stage and commit the log file
        self.repo.index.add([filepath])
        self.repo.index.commit(f"Add Claude chat log: {filename}")
    
    def run(self, **kwargs):
        """
        Generate and save log entry
        
        :param kwargs: Additional parameters for log generation
        """
        log_entry = self.generate_log_entry(**kwargs)
        self.save_log(log_entry)
        
        return log_entry

# Example usage
if __name__ == '__main__':
    generator = ChatLogGenerator('/path/to/repo')
    log = generator.run(
        llm_model='Claude 3.5 Sonnet',
        chat_title='AIQLeads Development Session',
        primary_focus='AI Cost Optimization'
    )
    print(log)
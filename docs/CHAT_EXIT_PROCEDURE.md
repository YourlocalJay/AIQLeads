# Chat Exit Procedure

This document outlines the exact steps that must be followed when ending a chat session.

## Trigger

When "End of chat" or "End chat" or "End session" is typed, the following procedure must be executed in order:

## 1. Change Review

### A. File Modification Review
```python
def review_changes():
    changes = {
        "modified_files": [],
        "modified_sections": [],
        "new_files": []
    }
    # Log must be detailed and specific
    return changes
```

### B. Section Update Review
- Document exact lines/sections modified
- Specify what content was added
- Never remove previous content
- Track section-specific changes

## 2. Status Report Generation

### A. Component Updates
```markdown
This Chat's Updates:
- Components Modified:
  - [component_path]: [specific_changes]
  - [component_path]: [specific_changes]

- Status Changes:
  - [component]: [old_status] → [new_status]
  - [component]: [old_status] → [new_status]

- Documentation Updates:
  - [doc_file]: Added section [section_name]
  - [doc_file]: Updated section [section_name]

- New Implementations:
  - [new_file]: [purpose]
  - [new_file]: [purpose]
```

## 3. Repository Status Update

### A. REPOSITORY_STATUS.md Update Rules
- ONLY ADD new content
- NEVER modify existing content
- NEVER remove old entries
- Add dated section at bottom

### B. Update Format
```markdown
### [YYYY-MM-DD] Chat Session Update
#### Changes Made
- [List of specific changes]

#### Current Status
- [Component status updates]

#### Next Steps
- [Immediate next tasks]

#### Known Issues
- [Current issues to address]
```

## 4. Continuation Message Generation

### A. Required Components
```markdown
Repository Information:
* GitHub Repository: https://github.com/YourlocalJay/AIQLeads
* Owner: YourlocalJay
* Access Type: [access_type]
* Branch: [branch_name]

This Chat's Context:
- Completed:
  - [specific_task]: [details]
  - [specific_task]: [details]
- Current State:
  - [component]: [state]
  - [component]: [state]
- Next Task:
  - [specific_next_task]

File Review Instructions:
1. aiqleads/docs/CONTINUATION_PROCEDURE.md
2. aiqleads/docs/UNIVERSAL_PROMPT.md
3. docs/PROJECT_STRUCTURE.md
4. REPOSITORY_STATUS.md

CRITICAL RULES:
- All changes must preserve existing content
- Never rewrite files, only update specific sections
- Add new content without removing old
- Maintain complete history
- No restructuring without approval
```

## Implementation Notes

### 1. File Updates
```python
def update_file(file_path, new_content):
    """
    Update file while preserving existing content.
    NEVER overwrite or remove existing content.
    """
    with open(file_path, 'r') as f:
        existing_content = f.read()
    
    # Add new content at appropriate section
    updated_content = append_to_section(
        existing_content, 
        new_content,
        section="appropriate_section"
    )
    
    with open(file_path, 'w') as f:
        f.write(updated_content)
```

### 2. Status Tracking
```python
def update_status(component, new_status):
    """
    Add new status while preserving history.
    NEVER remove old status entries.
    """
    status_history = load_status_history()
    status_history.append({
        "timestamp": datetime.now(),
        "component": component,
        "status": new_status
    })
    save_status_history(status_history)
```

### 3. Documentation Updates
```python
def update_documentation(doc_path, new_content):
    """
    Add to documentation while preserving history.
    NEVER remove or modify existing documentation.
    """
    existing_doc = load_documentation(doc_path)
    updated_doc = add_new_section(
        existing_doc,
        new_content,
        date=datetime.now()
    )
    save_documentation(doc_path, updated_doc)
```

## Integration Points

### 1. State Validation
```python
def validate_state():
    """
    Validate state before transition.
    Ensure all required data is present.
    """
    checksum = generate_state_checksum()
    validate_completeness()
    return {
        "checksum": checksum,
        "timestamp": datetime.now(),
        "status": "valid"
    }
```

### 2. Continuation Data Preparation
```python
def prepare_continuation_data():
    """
    Prepare data for initialization.
    Ensure all required context is included.
    """
    state = capture_current_state()
    validate_state()
    return format_continuation_data(state)
```

### 3. Error Recovery
```python
def handle_transition_error():
    """
    Handle errors during exit process.
    Ensure data consistency is maintained.
    """
    backup_state = create_state_backup()
    log_error_details()
    return generate_recovery_plan()
```

## Verification Checklist

Before completing chat exit:
- [ ] All changes are documented
- [ ] No content has been removed
- [ ] Status updates are additive
- [ ] History is preserved
- [ ] Continuation message is complete
- [ ] Next steps are clear
- [ ] State validation completed
- [ ] Integration checks passed
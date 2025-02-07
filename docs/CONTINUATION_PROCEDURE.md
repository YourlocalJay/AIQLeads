# Continuation Procedure

This document outlines the exact sequence of steps required for chat continuation in the AIQLeads project.

## Required File Access Sequence

### 1. Initial Files Review
ALWAYS review these files in this exact order:
```markdown
1. aiqleads/docs/CONTINUATION_PROCEDURE.md (this file)
2. aiqleads/docs/UNIVERSAL_PROMPT.md
3. docs/PROJECT_STRUCTURE.md
4. REPOSITORY_STATUS.md
```

### 2. Status Files
After reviewing the initial files, check:
```markdown
1. current_status.json
2. project_tracking.log
3. last_session.md
```

## Chat Initialization Steps

### 1. Verify Repository Access
```python
def verify_repository_access():
    required_paths = [
        "aiqleads/docs/CONTINUATION_PROCEDURE.md",
        "aiqleads/docs/UNIVERSAL_PROMPT.md",
        "docs/PROJECT_STRUCTURE.md",
        "REPOSITORY_STATUS.md"
    ]
    
    for path in required_paths:
        if not verify_file_exists(path):
            raise FileNotFoundError(f"Required file {path} not found")
```

### 2. Load Previous State
```python
def load_previous_state():
    # Load last session data
    with open("last_session.md", "r") as f:
        last_session = f.read()
    
    # Parse status
    current_status = json.load(open("current_status.json"))
    
    return {
        "last_session": last_session,
        "current_status": current_status
    }
```

### 3. Initialize Project Tracker
```python
def initialize_tracking():
    tracker = ProjectTracker()
    tracker.start_session()
    return tracker
```

## Session Management

### 1. Active Session Tracking
```python
def track_session_progress(tracker):
    tracker.log_activity({
        "timestamp": datetime.now(),
        "activity": "continuation_procedure",
        "status": "active"
    })
```

### 2. Component State Verification
```python
def verify_component_state(component_path):
    tracker = ProjectTracker()
    return tracker.verify_component({
        "path": component_path,
        "expected_state": load_expected_state()
    })
```

## Chat Termination Steps

### 1. Update Status Files
```python
def update_status_files(session_data):
    # Update current_status.json
    with open("current_status.json", "w") as f:
        json.dump(session_data["status"], f)
    
    # Update last_session.md
    with open("last_session.md", "w") as f:
        f.write(session_data["summary"])
```

### 2. Generate Continuation Message
```python
def generate_continuation_message():
    template = load_continuation_template()
    status = load_current_status()
    
    return template.format(
        branch=status["branch"],
        last_component=status["last_component"],
        current_status=status["status"],
        next_task=status["next_task"]
    )
```

## Validation Rules

### 1. Path Validation
- All paths must exist within the aiqleads/ directory
- Paths must match PROJECT_STRUCTURE.md
- No new root directories
- No duplicate implementations

### 2. Status Validation
- All components must have current status
- Status updates must be logged
- Changes must be documented
- Next steps must be defined

## Required Documentation Updates

### 1. Session Summary
```markdown
### [Current Date]
#### Session Summary
- Completed: [List completed items]
- Current State: [State of in-progress items]
- Next Steps: [Immediate next tasks]
- Known Issues: [Any outstanding issues]
```

### 2. Status Updates
```python
def document_status_updates():
    return {
        "component_id": "path/to/component",
        "status": "current_status",
        "changes": ["list", "of", "changes"],
        "next_steps": ["next", "steps"],
        "known_issues": ["known", "issues"]
    }
```

## Error Recovery

### 1. Handling Missing Files
```python
def recover_missing_files():
    try:
        verify_repository_access()
    except FileNotFoundError as e:
        log_error(e)
        restore_from_backup()
```

### 2. Status Inconsistency Recovery
```python
def recover_status():
    if status_is_inconsistent():
        backup_status = load_backup_status()
        restore_status(backup_status)
```

## Quality Assurance

### 1. Pre-Session Checklist
- [ ] All required files accessible
- [ ] Previous session data loaded
- [ ] Project tracker initialized
- [ ] Component states verified
- [ ] Status files current

### 2. Post-Session Checklist
- [ ] All changes documented
- [ ] Status files updated
- [ ] Continuation message generated
- [ ] Next steps defined
- [ ] Known issues logged
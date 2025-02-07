# Chat Initialization Procedure

This document outlines the exact steps that must be followed when starting a new chat session.

## Initial Setup Phase

### 1. Continuation Message Review
The AI must review the continuation message which includes:
```markdown
A. Repository Information
   - Repository URL
   - Owner
   - Access type
   - Branch

B. Previous Chat Context
   - Completed tasks
   - Current state
   - Next immediate task

C. File Review Order
   1. aiqleads/docs/CONTINUATION_PROCEDURE.md
   2. aiqleads/docs/UNIVERSAL_PROMPT.md
   3. docs/PROJECT_STRUCTURE.md
   4. REPOSITORY_STATUS.md

D. Critical Rules
   - Structure preservation
   - No rewrites policy
   - Update-only modifications
```

### 2. File Access Verification
```python
def verify_file_access():
    """
    Verify access to all required files.
    Must be done in specified order.
    """
    required_files = [
        "aiqleads/docs/CONTINUATION_PROCEDURE.md",
        "aiqleads/docs/UNIVERSAL_PROMPT.md",
        "docs/PROJECT_STRUCTURE.md",
        "REPOSITORY_STATUS.md"
    ]
    
    for file_path in required_files:
        if not file_exists(file_path):
            raise FileNotFoundError(
                f"Required file not accessible: {file_path}"
            )
```

### 3. Understanding Confirmation
The AI must explicitly confirm:
```markdown
A. Structure Preservation
   - Will maintain existing directory structure
   - Will not create new root directories
   - Will follow PROJECT_STRUCTURE.md

B. No-Rewrite Policy
   - Will never rewrite entire files
   - Will only update specific sections
   - Will preserve all existing content

C. Update-Only Approach
   - Will add to existing content
   - Will maintain history
   - Will track all changes incrementally
```

## Pre-Development Verification

### 1. Status Verification
```python
def verify_current_status():
    """
    Verify current project status before proceeding.
    """
    status = {
        "implementation_status": check_implementation_status(),
        "file_locations": verify_file_locations(),
        "duplicates": check_for_duplicates()
    }
    
    return status
```

### 2. Structure Validation
```python
def validate_structure():
    """
    Validate project structure against requirements.
    """
    structure = load_project_structure()
    current = get_current_structure()
    
    validate_against_rules(current, structure)
```

### 3. Development Prerequisites
The following must be confirmed before any development:

```markdown
A. No-Rewrite Confirmation
   - Verified update-only approach
   - Confirmed section-specific updates
   - Established content preservation

B. Status Verification
   - Current status loaded
   - File locations verified
   - No duplicates exist

C. Structure Validation
   - Directory structure verified
   - File organization confirmed
   - No unauthorized changes
```

## Implementation Requirements

### 1. File Modification Rules
```python
def update_file_content(file_path, new_content, section):
    """
    Update specific section while preserving file.
    """
    original = read_file(file_path)
    if not section_exists(original, section):
        raise ValueError(f"Section {section} not found")
    
    updated = update_section(original, section, new_content)
    write_file(file_path, updated)
```

### 2. Documentation Updates
```python
def update_documentation(doc_path, new_content):
    """
    Add to documentation preserving history.
    """
    existing = read_documentation(doc_path)
    updated = append_with_timestamp(existing, new_content)
    write_documentation(doc_path, updated)
```

### 3. Change Tracking
```python
def track_changes():
    """
    Track all changes incrementally.
    """
    return {
        "modified_files": get_modified_files(),
        "added_content": get_added_content(),
        "status_updates": get_status_updates()
    }
```

## Verification Process

### 1. Initial Checklist
- [ ] Continuation message reviewed
- [ ] Required files accessible
- [ ] Structure preservation confirmed
- [ ] No-rewrite policy acknowledged
- [ ] Update-only approach confirmed

### 2. Pre-Development Checklist
- [ ] Current status verified
- [ ] File locations confirmed
- [ ] No duplicates found
- [ ] Structure validated
- [ ] Prerequisites met

### 3. Final Verification
- [ ] Update approach confirmed
- [ ] History preservation assured
- [ ] Change tracking ready
- [ ] Documentation process clear

## Error Prevention

### 1. Common Issues
```markdown
A. Structure Violations
   - Creating new root directories
   - Reorganizing existing structure
   - Duplicate implementations

B. Content Loss
   - File rewrites
   - Content replacement
   - History deletion

C. Tracking Gaps
   - Missing status updates
   - Incomplete change logs
   - Lost context
```

### 2. Prevention Measures
```markdown
A. Strict Validation
   - File existence checks
   - Structure verification
   - Duplicate detection

B. Content Preservation
   - Section-specific updates
   - History maintenance
   - Incremental changes

C. Comprehensive Tracking
   - Change logging
   - Status updates
   - Context preservation
```
# Continuation Procedure

## Overview
This document outlines the procedures for handling chat continuations and end sequences in the AIQLeads system.

## End Sequence
The end sequence is triggered when "End of chat" is detected. This sequence:
1. Validates all file paths according to structure guidelines
2. Updates project status
3. Generates a standardized continuation prompt
4. Enforces directory structure compliance

### Trigger
- End sequence activates on exact match of "End of chat" (case insensitive)
- Validates current state before proceeding
- Checks file path compliance

### File Path Validation
- All paths must be within aiqleads/ directory
- Exception: MVP mode allows specific directories:
  - backend/
  - ai_models/
  - scraping/
  - services/
  - deployment/
  - tests/

### State Management
- Updates project_status.json with:
  - Last updated timestamp
  - Active files list
  - Current state
  - MVP mode status

### Testing
End sequence functionality can be tested using:
```python
python -m unittest aiqleads/tests/test_template_generator.py
```

Test coverage includes:
- End sequence trigger detection
- Path validation
- MVP mode validation
- Repository section formatting
- Project status updates
- Error handling

## Continuation Format
The generated continuation prompt includes:

1. Repository Information
   - URL
   - Branch
   - Owner
   - Access level

2. Current Status
   - Last 3 completed items
   - Current state description

3. Next Tasks
   - Pending items from status

4. Critical Requirements
   - Directory structure rules
   - File update guidelines
   - Path validation requirements

5. Files of Interest
   - Active component paths
   - Validated against structure rules

## Error Handling
- Invalid paths trigger ValueError
- Missing status file triggers FileNotFoundError
- All errors logged with context
- Fallback to safe continuation if error occurs

## Monitoring
- Operations logged with timestamps
- Status updates tracked
- Path validation results recorded
- Error states captured

## Best Practices
1. Always validate paths before operations
2. Update existing files instead of creating new ones
3. Maintain backward compatibility
4. Document all changes
5. Follow directory structure guidelines
6. Use appropriate test coverage

## MVP Mode
When MVP mode is enabled:
1. Different path validation rules apply
2. Additional requirements included
3. Special directory structure allowed
4. Custom validation logic used

## File Structure Integration
All operations must:
1. Follow FILE_STRUCTURE_GUIDELINES.md
2. Use aiqleads/ directory
3. Maintain existing structure
4. Update, don't recreate
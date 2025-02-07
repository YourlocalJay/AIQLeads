# Chat Procedures

This document outlines the standard operating procedures for managing chat interactions within the AIQLeads platform.

## Chat Initialization

### Starting a New Chat

1. Share Continuation Message
   - Use the continuation message from the previous chat session
   - Ensure all context is preserved

2. Required File Review Sequence
   ```markdown
   1. aiqleads/docs/CONTINUATION_PROCEDURE.md
   2. aiqleads/docs/UNIVERSAL_PROMPT.md
   3. docs/PROJECT_STRUCTURE.md
   4. REPOSITORY_STATUS.md
   ```

3. Initial Status Check
   ```python
   from aiqleads.core.project_tracking import ProjectTracker
   tracker = ProjectTracker()
   status_report = tracker.generate_report()
   ```

4. Structure Verification
   ```python
   # Verify no duplicate implementations exist
   tracker.check_duplicate_functionality(
       component_type="your_component_type",
       component_def={"purpose": "your_purpose"}
   )
   ```

5. Development Initialization
   - Update component status to "In Progress"
   - Follow established structure rules
   - Initialize change tracking
   - Verify documentation requirements

### Critical Rules
- All changes must be contained within the aiqleads/ directory
- Core project structure must remain unmodified
- No creation of alternate versions of existing files
- Use project_tracking.py for all status updates
- All paths must be validated against PROJECT_STRUCTURE.md

## Chat Termination

### Ending a Chat Session

1. Trigger Commands
   - "End of chat"
   - "End chat"
   - "End session"

2. Status Updates
   ```python
   # Update status of worked components
   tracker.update_status(
       component_id="current/component/path",
       status="current_status",
       notes="End of chat status + next steps"
   )
   ```

3. Session Documentation
   ```markdown
   ### [Current Date]
   #### Session Summary
   - Completed: [List completed items]
   - Current State: [State of in-progress items]
   - Next Steps: [Immediate next tasks]
   - Known Issues: [Any outstanding issues]
   ```

4. Continuation Message Generation
   ```markdown
   I'm continuing work on the AIQLeads project. IMPORTANT: This is an existing project with an established structure - do not create new root directories or modify the structure. All changes must be made within the existing structure.

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
   * GitHub Repository: https://github.com/YourlocalJay/AIQLeads
   * Owner: YourlocalJay
   * Access Type: Private repository
   * Branch: [Current Branch]

   Current Status:
   - Branch: [Current Branch]
   - Last Component: [Last worked on component]
   - Status: [Current status]
   - Next Task: [Next planned task]

   Recent Changes:
   1. [Most recent change]
   2. [Second most recent change]
   3. [Third most recent change]

   Development Focus:
   - Primary Goal: [Goal]
   - Components: [Components]
   - Requirements: [Requirements]
   ```

## Tracking and Validation

### Status Tracking
- Use ProjectTracker for all status updates
- Document all changes in real-time
- Maintain clear next steps
- Track known issues

### Structure Validation
- Verify paths against PROJECT_STRUCTURE.md
- Prevent duplicate implementations
- Maintain directory structure
- Follow established naming conventions

## Error Prevention

### Common Issues
1. Loss of context between chats
2. Inconsistent file locations
3. Duplicate implementations
4. Structure modification
5. Status tracking gaps

### Prevention Measures
1. Consistent file review order
2. Clear structure rules
3. Continuous status tracking
4. Detailed continuation context
5. Documentation preservation

## Documentation Requirements

### Session Documentation
- Date and time stamps
- Completed tasks
- Current state
- Next steps
- Known issues
- Status updates

### Change Tracking
- Component modifications
- Status updates
- Structure validations
- Issue documentation
- Next steps definition
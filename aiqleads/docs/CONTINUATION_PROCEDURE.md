# AIQLeads Project Continuation Procedure

## Repository Access Information
* GitHub Repository: https://github.com/YourlocalJay/AIQLeads
* Owner: YourlocalJay
* Access Type: Private repository
* Branch Strategy: GitFlow with protected main branch
* Primary Development Branch: Optimization
* Required Permissions: Write access

## Initial Setup (One-Time)
1. Share this message with the AI:
   ```
   I'm continuing work on the AIQLeads project. IMPORTANT: This is an existing project with an established structure - do not create new root directories or modify the structure. All changes must be made within the existing structure.

   First, please review these files in order:
   1. aiqleads/docs/CONTINUATION_PROCEDURE.md - Contains all project continuation procedures
   2. aiqleads/docs/UNIVERSAL_PROMPT.md - Contains current project status
   3. docs/PROJECT_STRUCTURE.md - Contains reference structure (DO NOT MODIFY)
   4. REPOSITORY_STATUS.md - Contains latest changes

   CRITICAL RULES:
   - All changes must be inside the aiqleads/ directory
   - Never modify the core project structure
   - Never create alternate versions of existing files
   - Use project_tracking.py for all status updates
   - Always validate paths against PROJECT_STRUCTURE.md before creating files
   - Always check for existing implementations before creating new files
   - All new files must follow established naming conventions
   - Documentation updates must preserve existing sections

   Project Information:
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
   - Primary Goal: [Current goal]
   - Components: [Components to work on]
   - Requirements: [Specific requirements]

   Important: When I type "End of chat" or "End chat" or "End session", please:
   1. Update all relevant status tracking
   2. Document the current state
   3. Generate a formatted continuation message for my next chat session
   4. Include all repository access information
   ```

## During Development

### Status Updates
Use project_tracking.py for all updates:
```python
from aiqleads.core.project_tracking import ProjectTracker
tracker = ProjectTracker()

# Update status
tracker.update_status(
    component_id="path/to/component",
    status="current_status",
    notes="Implementation details"
)
```

### Documentation Updates
- Preserve all section structures
- Add new content in appropriate sections
- Update status indicators consistently
- Maintain formatting standards

## End of Chat Procedure

### Trigger
When you're ready to end the chat, type one of:
- "End of chat"
- "End chat"
- "End session"

The AI will then:
1. Run through this end-of-chat procedure
2. Generate a continuation message for your next chat
3. Format all information for easy copying

### Steps
1. Update Project Status
2. Document Current State
3. Verify Documentation
4. Save Chat Context
5. Generate Continuation Message

## General Notes
- Always start by checking UNIVERSAL_PROMPT.md
- Follow established project structure
- Use status indicators consistently:
  - 🔴 Not Started
  - 🟡 In Progress
  - 🟣 In Review
  - 🔵 Testing
  - 🟢 Completed
  - ⭕ Blocked
- Keep all changes within aiqleads/ directory
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
   I'm continuing work on the AIQLeads project. Please first read:
   1. aiqleads/docs/UNIVERSAL_PROMPT.md
   2. docs/PROJECT_STRUCTURE.md
   3. REPOSITORY_STATUS.md
   ```

[... previous content ...]

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

### 1. Update Project Status
Run final status check:
```python
from aiqleads.core.project_tracking import ProjectTracker
tracker = ProjectTracker()

# Update status of worked components
tracker.update_status(
    component_id="current/component/path",
    status="current_status",
    notes="End of chat status"
)

# Generate final report
final_report = tracker.generate_report()
```

### 2. Document Current State
Add to REPOSITORY_STATUS.md:
```markdown
### [Current Date]
#### Session Summary
- Completed: [List completed items]
- Current State: [State of in-progress items]
- Next Steps: [Immediate next tasks]
- Known Issues: [Any outstanding issues]

#### Next Session
- Start Point: [Component/feature to continue with]
- Priority: [Most important tasks]
- Required Setup: [Any necessary preparation]
```

### 3. Verify Documentation
Ensure all documentation is current:
- [ ] UNIVERSAL_PROMPT.md reflects latest status
- [ ] Component documentation is updated
- [ ] All changes are committed
- [ ] Next steps are clearly documented

### 4. Save Chat Context
Create a new section in REPOSITORY_STATUS.md:
```markdown
### Chat Context [Date]
- Branch: [Current branch]
- Components Modified: [List of modified components]
- Implementation Status: [Current implementation state]
- Next Session Focus: [What to focus on next]
```

### 5. Generate Continuation Message
The AI will generate a formatted message containing:
```markdown
I'm continuing work on the AIQLeads project. Please review:

Repository Information:
* GitHub Repository: [URL]
* Owner: [Owner]
* Access Type: [Type]
* Branch: [Branch]

Current Status:
- Branch: [Current branch]
- Last Component: [Last modified component]
- Status: [Current status]
- Next Task: [Next task]

Recent Changes:
1. [Change 1]
2. [Change 2]
3. [Change 3]

Development Focus:
- Primary Goal: [Goal]
- Components: [Components]
- Requirements: [Requirements]

Please check:
1. aiqleads/docs/UNIVERSAL_PROMPT.md
2. docs/PROJECT_STRUCTURE.md
3. REPOSITORY_STATUS.md
```

## General Notes
- Always start by checking UNIVERSAL_PROMPT.md for latest project status
- Use status indicators consistently:
  - 🔴 Not Started
  - 🟡 In Progress
  - 🟣 In Review
  - 🔵 Testing
  - 🟢 Completed
  - ⭕ Blocked
- Keep all changes within aiqleads/ directory
- Follow established project structure
- Update status before and after each significant change
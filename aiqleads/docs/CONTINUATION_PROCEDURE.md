# AIQLeads Project Continuation Procedure

## Initial Setup (One-Time)
1. Share this message with the AI:
   ```
   I'm continuing work on the AIQLeads project. Please first read:
   1. aiqleads/docs/UNIVERSAL_PROMPT.md
   2. docs/PROJECT_STRUCTURE.md
   3. REPOSITORY_STATUS.md
   ```

## Session Start Procedure

### 1. Check Project Status
```python
from aiqleads.core.project_tracking import ProjectTracker
tracker = ProjectTracker()
status_report = tracker.generate_report()
```

### 2. Share Context
Share with the AI:
1. Current branch name
2. Last component you were working on
3. Any blockers or issues
4. Next planned task

Example:
```
Current Context:
- Branch: Optimization
- Last Component: aiqleads/core/project_tracking.py
- Status: In Progress
- Next Task: Implementing status dashboard
- Notes: Need to resolve rate limiting issue
```

### 3. Review Recent Changes
Check last changes in the branch:
```bash
git log -n 5 --oneline
```
Share the output with the AI.

### 4. Set Development Focus
Tell the AI what you want to accomplish in this session:
```
Development Focus:
- Primary Goal: [What you want to achieve]
- Components: [Which parts you'll be working on]
- Requirements: [Any specific requirements]
- Constraints: [Any limitations or constraints]
```

### 5. Verify Project Structure
```python
# Verify no duplicate implementations exist
tracker.check_duplicate_functionality(
    component_type="your_component_type",
    component_def={"purpose": "your_purpose"}
)
```

## During Development

### Status Updates
Update component status as you work:
```python
tracker.update_status(
    component_id="path/to/component",
    status="🟡 In Progress",
    notes="Current implementation details"
)
```

### Documentation Updates
Keep documentation current:
1. Update REPOSITORY_STATUS.md with progress
2. Add implementation notes to component docstrings
3. Update any relevant documentation files

## End of Session

### 1. Save Status
```python
# Update final status
tracker.update_status(
    component_id="path/to/component",
    status="current_status",
    notes="Session end state"
)
```

### 2. Document Progress
Add to the Notes section in REPOSITORY_STATUS.md:
```markdown
### [Current Date]
- Completed: [List of completed items]
- In Progress: [List of items still in progress]
- Next Steps: [What needs to be done next]
- Known Issues: [Any issues to be addressed]
```

### 3. Verify Changes
Run through verification checklist:
- [ ] All changes follow project structure
- [ ] No duplicate implementations introduced
- [ ] Documentation is updated
- [ ] Status tracking is current

### 4. Save Context
Save key information for next session:
```markdown
Next Session Start:
- Continue from: [component/feature]
- Priority tasks: [list]
- Open issues: [list]
- Required preparations: [list]
```

## Notes
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
# AIQLeads End of Chat Procedure

## Purpose
Define a standardized, repeatable process for concluding each chat interaction while preserving context and enabling seamless continuation.

## Trigger Conditions
An End of Chat procedure is initiated when:
- User types "End of chat"
- All immediate objectives have been addressed
- A clear set of next steps has been established

## Mandatory Documentation Update

### 1. Project Status Documentation
- Update `aiqleads/docs/PROJECT_STATUS.md`
- Include:
  * Completed tasks
  * Progress on current development tracks
  * Updates to key performance indicators
  * New identified risks or mitigation strategies

### 2. Change Tracking
- Document all modifications
- Specify:
  * Files changed
  * Nature of changes
  * Rationale for modifications
  * Potential impact on project

## Continuation Message Generation

### Required Components
```markdown
# AIQLeads Continuation Prompt

## Repository Context
- Repository: https://github.com/YourlocalJay/AIQLeads
- Owner: YourlocalJay
- Branch: [Current Branch]
- Access: Private Repository

## Completed in This Chat
- [Specific task/objective]
- [Specific task/objective]

## Current Project Status
[Summarize key points from PROJECT_STATUS.md]

## Recommended Next Steps
1. [Prioritized next action]
2. [Secondary action]
3. [Tertiary action]

## Critical Reminders
- Review all documentation before starting
- Maintain minimal development entropy
- Preserve strategic project alignment

## Timestamp
[Current Date and Time]
```

## Verification Checklist
Before Ending Chat, Confirm:
- [ ] Project status has been updated
- [ ] Changes are documented
- [ ] Continuation message is comprehensive
- [ ] Next steps are clear and actionable
- [ ] No critical tasks are left unaddressed

## Error Handling
If unable to complete full procedure:
1. Document incomplete items
2. Explain reason for incomplete procedure
3. Ensure critical information is preserved

## Philosophical Principles
- Treat each interaction as a strategic advancement
- Maintain continuous, traceable project development
- Prioritize clarity and purposeful progression

---

*Last Updated: [CURRENT_TIMESTAMP]*
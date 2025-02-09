# Chat Continuation Procedure

## Overview
This document outlines the standardized procedure for ending and continuing chat sessions.

## End Chat Trigger
To initiate the end sequence, type:
```
End chat sequence.
```

## Required Components
The system will automatically collect data from:
1. Project Status (aiqleads/data/project_status.json)
2. Component Registry (aiqleads/data/component_registry.json)
3. Template Generator (aiqleads/core/template_generator.py)
4. Project Tracking (aiqleads/core/project_tracking.py)

## State Collection
The system will gather:
1. Current repository state
2. Active branch information
3. Completed and pending tasks
4. Modified files
5. Critical requirements

## Output Format
The continuation prompt will always follow this format:
```
# Prompt for Next Chat
Please continue with repository: [url]
- Branch: [branch]
- Owner: [owner]
- Access: [access]

Current Status:
- [status items from project_status.json]

Next Tasks:
- [pending tasks from project_tracking.py]

Critical Requirements:
- [requirements from template_generator.py]

Files of Interest:
- [relevant files from component_registry.json]

End of Chat.
```

## Validation Steps
The system will:
1. Verify data consistency using utils/validation.py
2. Check project status in project_status.json
3. Validate component registry
4. Ensure clean resource closure

## Error Handling
If errors occur:
1. Log error details using utils/logging.py
2. Attempt cleanup procedures
3. Generate safe continuation data
4. Document error state

## Integration Points
- Project Status: data/project_status.json
- Component Registry: data/component_registry.json
- Validation System: utils/validation.py
- Logging System: utils/logging.py
- Template System: core/template_generator.py
- Project Tracking: core/project_tracking.py

## Implementation Notes
1. Never skip validation steps
2. Always generate continuation data
3. Include all critical rules
4. Document current state
5. Specify next tasks
6. End with "End of Chat."
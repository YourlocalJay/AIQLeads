# Universal Prompt Guidelines

## Overview
This document provides standardized guidelines for chat interactions.

## Starting a Chat
Begin each chat with repository information:
```
Please continue with repository: [url]
- Branch: [branch]
- Owner: [owner]
- Access: [access]
```

## During the Chat
1. Follow project tracking procedures
2. Use component registry for file references
3. Validate all operations
4. Log important changes

## Ending a Chat
To end a chat session:

1. Type the trigger phrase:
```
End chat sequence.
```

2. The system will automatically:
   - Collect current state
   - List completed/pending tasks
   - Include critical requirements
   - List relevant files
   - Output continuation prompt

3. The output will follow this format:
```
# Prompt for Next Chat
Please continue with repository: [url]
- Branch: [branch]
- Owner: [owner]
- Access: [access]

Current Status:
- [status items]

Next Tasks:
- [task items]

Critical Requirements:
- [requirement items]

Files of Interest:
- [file items]

End of Chat.
```

## Required Components
1. Project Status (project_status.json)
2. Component Registry (component_registry.json)
3. Validation System (validation.py)
4. Template System (template_generator.py)
5. Project Tracking (project_tracking.py)

## Critical Rules
1. Never skip validation
2. Always preserve content
3. No rewriting files
4. Add without removing
5. Maintain history

## Error Handling
If errors occur during end sequence:
1. System attempts recovery
2. Generates safe continuation
3. Documents error state
4. Ensures clean closure

## Notes
- End sequence is automatic
- Format is standardized
- State is preserved
- History is maintained
# File Structure Guidelines

## Directory Structure
All project files must be organized under the aiqleads/ directory:

```
aiqleads/
├── core/             # Core functionality
├── data/            # Data and state files
├── docs/            # Documentation
└── utils/           # Utility functions
```

## Core Principles
1. Use existing files
2. Don't create duplicate functionality
3. Follow established structure
4. Update, don't recreate

## Directory Usage

### core/
- Main functionality
- Business logic
- Core processes
- Current files:
  - template_generator.py
  - project_tracking.py

### data/
- State management
- Configuration
- Runtime data
- Current files:
  - project_status.json
  - component_registry.json

### docs/
- Documentation
- Procedures
- Guidelines
- Current files:
  - CONTINUATION_PROCEDURE.md
  - UNIVERSAL_PROMPT.md
  - MVP_TECHNICAL_DOCUMENTATION.md

### utils/
- Helper functions
- Shared utilities
- Support code
- Current files:
  - validation.py
  - logging.py

## Adding New Functionality

1. First check if functionality exists in:
   - core/template_generator.py
   - core/project_tracking.py
   - utils/validation.py
   - utils/logging.py

2. If similar functionality exists:
   - Update existing file
   - Add new methods/classes
   - Extend current functionality

3. If truly new functionality:
   - Use appropriate existing directory
   - Follow naming conventions
   - Update component registry

## Never Create
1. New root directories
2. Parallel implementations
3. Duplicate functionality
4. Alternate file structures

## Always
1. Use aiqleads/ structure
2. Update existing files
3. Follow directory purpose
4. Maintain registry

## When in Doubt
1. Check component_registry.json
2. Review existing files
3. Update don't create
4. Ask for clarification

## File Updates
When updating files:
1. Preserve existing content
2. Add new functionality
3. Maintain backwards compatibility
4. Document changes

## Documentation Updates
When updating docs:
1. Use existing files
2. Add new sections
3. Update relevant parts
4. Maintain structure
# Project Tracking System

## Overview
The project tracking system helps maintain the status of all components in the AIQLeads project. It prevents duplicate implementations, tracks progress, and ensures proper project organization.

## Key Features
- Component registration and validation
- Status tracking with history
- Progress metrics and reporting
- Duplicate functionality detection
- Path validation against project structure

## Project Status Indicators
- 🔴 Not Started
- 🟡 In Progress
- 🟣 In Review
- 🔵 Testing
- 🟢 Completed
- ⭕ Blocked

## Using the Tracking System

### Via Python API
```python
from aiqleads.core.project_tracking import ProjectTracker

# Initialize tracker
tracker = ProjectTracker()

# Register new component
tracker.register_component(
    component_type="api",
    component_id="api/v1/endpoints/leads.py",
    component_def={
        "purpose": "AI-driven Lead Management API",
        "functionality": ["lead_scoring", "lead_routing"]
    }
)

# Update status
tracker.update_status(
    component_id="api/v1/endpoints/leads.py",
    status="🟡 In Progress",
    notes="Implementing core lead scoring integration"
)

# Get status report
report = tracker.generate_report()
```

### Via CLI
The `track.py` utility provides command-line access to tracking functionality:

```bash
# Get component status
./track.py status api/v1/endpoints/leads.py

# Update component status
./track.py update api/v1/endpoints/leads.py "🟡 In Progress" --notes "Added validation"

# Generate full report
./track.py report
```

### Using the Initialization Scripts
1. First-time setup:
   ```bash
   python -m aiqleads.scripts.register_components
   ```

2. Verify registration:
   ```bash
   ./track.py report
   ```

## Integration Guidelines

### For New Components
1. Before creating any new component:
   - Check existing components via `track.py report`
   - Verify your path in PROJECT_STRUCTURE.md
   - Register your component using ProjectTracker

2. During development:
   - Update status as you progress
   - Add meaningful notes about changes
   - Keep dependency information current

3. Code integration:
   ```python
   from aiqleads.core.project_tracking import ProjectTracker
   
   class MyComponent:
       def __init__(self):
           self.tracker = ProjectTracker()
           
       def major_update(self):
           self.tracker.update_status(
               "path/to/component",
               "🟡 In Progress",
               "Implementing feature X"
           )
   ```

### For Existing Components
1. Monitor dependencies:
   - Check component status before use
   - Update dependency information
   - Report blocking issues

2. Status updates:
   - Use appropriate status indicators
   - Include relevant context in notes
   - Tag related components if needed

## Best Practices

### Status Updates
- Keep notes concise but informative
- Include relevant ticket/issue numbers
- Mention dependent components
- Update promptly when status changes

### Component Registration
- Follow naming conventions
- Include complete functionality list
- Define clear component purpose
- Set appropriate initial status

### Dependency Management
- Register all dependencies
- Update when dependencies change
- Note blocking dependencies
- Track dependency versions

### Reports and Monitoring
- Review full reports regularly
- Monitor completion metrics
- Track blocked components
- Identify bottlenecks

## Data Management

### Storage Location
All tracking data is stored in the `aiqleads/data/` directory:
- `project_status.json`: Current status and history
- `component_registry.json`: Component definitions

### Backup and Maintenance
- Data is versioned with git
- Regular backups recommended
- Clean old history periodically
- Validate data integrity

## Troubleshooting

### Common Issues
1. Component not found:
   - Verify path is correct
   - Check if registered
   - Validate against structure

2. Status update failed:
   - Verify component exists
   - Check status indicator
   - Validate permissions

3. Duplicate detection:
   - Review existing components
   - Check functionality hash
   - Update component definition

### Data Recovery
1. From git:
   ```bash
   git checkout -- aiqleads/data/
   ```

2. From backup:
   ```bash
   cp backup/project_status.json aiqleads/data/
   cp backup/component_registry.json aiqleads/data/
   ```

## Contact and Support
- Report issues in GitHub repository
- Tag with 'project-tracking'
- Include relevant logs
- Provide reproduction steps
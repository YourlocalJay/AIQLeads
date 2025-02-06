# AIQLeads Project Tracking System

This document describes the project tracking system implementation and usage.

## Overview

The project tracking system provides:
- Component registration and status tracking
- Path validation against project structure
- Status history and reporting
- Automated backup and monitoring

## Components

### Core Tracking System
- ProjectTracker class (`aiqleads/core/project_tracking.py`)
  - Component registration
  - Status updates
  - Path validation
  - Status export

### Data Storage
- `/data/project_status.json`: Current project status
- `/data/component_registry.json`: Component registry
- Daily backups in `/data/backups/`

### CLI Tools
- `scripts/run.py`: Test runner
- `scripts/test_runner.py`: Test execution
- Status monitoring and reporting tools

## Usage

### Component Registration
```python
from aiqleads.core.project_tracking import get_tracker

tracker = get_tracker()
tracker.register_component(
    "core/new_component.py",
    "core",
    "Component description"
)
```

### Status Updates
```python
tracker.update_component_status(
    "core/new_component.py",
    "active",
    {"details": "Component activated"}
)
```

### Status Reporting
```python
status = tracker.get_project_status()
tracker.export_status("status_report.json")
```

## Testing

Run the test suite:
```bash
python aiqleads/scripts/test_runner.py
```

## Troubleshooting

### Common Issues

1. Path Validation Errors
   - Ensure paths are relative to aiqleads/
   - Check PROJECT_STRUCTURE.md for valid paths

2. Component Registration
   - Components must have unique paths
   - Required fields: path, type, description
   
3. Status Updates
   - Component must be registered first
   - Valid status values: initialized, active, inactive, error

### Error Resolution

1. Invalid Paths
```python
# Correct:
tracker.register_component("core/component.py", ...)
# Incorrect:
tracker.register_component("/absolute/path/component.py", ...)
```

2. Component Not Found
```python
# First register:
tracker.register_component(path, type, desc)
# Then update:
tracker.update_component_status(path, status)
```

## Integration Guidelines

1. Always use the singleton instance:
```python
from aiqleads.core.project_tracking import get_tracker
tracker = get_tracker()
```

2. Validate paths before registration:
```python
if tracker._validate_path(component_path):
    tracker.register_component(...)
```

3. Keep component descriptions concise but informative

4. Regular status updates on component changes:
```python
tracker.update_component_status(
    path,
    status,
    {"message": "Clear status message"}
)
```
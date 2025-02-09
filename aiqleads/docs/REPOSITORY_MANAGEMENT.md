# AIQLeads Repository Management Guidelines

## Core Principles

1. **Minimal Entropy Approach**
   - Minimize unnecessary file creation
   - Ensure targeted, precise modifications
   - Maintain clear development trajectory

2. **Collaborative Development**
   - Support multi-model interaction
   - Preserve contextual integrity
   - Enable seamless continuation of work

## Directory Organization

### Core Structure
```
AIQLeads/
├── README.md
├── .env.example
├── backend/
├── ai_models/
├── scraping/
├── services/
├── deployment/
└── tests/
```

### File Placement Rules
- Match directory purpose
- Follow naming conventions
- Include proper documentation
- Add type hints
- Include tests

### Documentation Requirements
- Component description
- Usage examples
- Dependencies
- Configuration
- Testing approach

## Modification Guidelines
- Only make changes that directly advance project objectives
- Document every modification comprehensively
- Preserve context across interaction sessions

## Cleanup Procedures

### Structure Validation
```python
def validate_structure():
    validator = PathValidator()
    invalid_paths = validator.list_invalid_paths()
    return invalid_paths
```

### Component Registration
```python
def register_component(name, type, path):
    tracker = ProjectTracker()
    return tracker.register_component(
        component_id=path,
        component_type=type,
        component_def={"name": name}
    )
```

### Status Tracking
```python
def track_status(component_id, status, notes):
    tracker = ProjectTracker()
    return tracker.update_status(
        component_id=component_id,
        status=status,
        notes=notes
    )
```

## Branch Management

### Branch Rules
- `main`: Protected, requires review
- `feature/*`: For new features
- `fix/*`: For bug fixes
- `release/*`: For releases

### Branch Cleanup Strategies
- Delete after merge
- Archive if historically significant
- Document major changes
- Update affected components

## Maintenance Guidelines

### Regular Tasks
- Validate file locations
- Update component status
- Check documentation
- Review dependencies
- Test coverage

### Quality Checks
- Code formatting
- Type checking
- Security scans
- Performance tests
- AI cost analysis

### Documentation Updates
- Keep status current
- Update guidelines
- Document changes
- Track decisions

## Interaction Constraints
- Prioritize minimal, focused development
- Eliminate redundant or overlapping work
- Maintain a clear, strategic progression

## Continuation Protocols
- Always review previous session's context
- Identify and build upon completed objectives
- Address unresolved items systematically

## Quality Assurance
- Validate changes against project goals
- Ensure alignment with overall project strategy
- Maintain high standards of code and documentation quality

## Communication Principles
- Be precise and targeted in communication
- Provide complete context in each interaction
- Maintain transparency in decision-making process
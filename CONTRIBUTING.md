# Contributing to AIQLeads

## Development Workflow

### Branch Strategy
We use GitFlow with the following branches:

1. `main`
   - Production-ready code
   - Protected branch
   - Requires pull request review
   - Must pass all tests

2. `develop`
   - Integration branch
   - Feature branches merge here
   - Continuous testing

3. Feature Branches
   - Branch from: `develop`
   - Branch naming: `feature/[description]`
   - Merge to: `develop`
   - Delete after merge

4. Bugfix Branches
   - Branch from: `develop`
   - Branch naming: `bugfix/[description]`
   - Merge to: `develop`
   - Delete after merge

5. Release Branches
   - Branch from: `develop`
   - Branch naming: `release/[version]`
   - Merge to: `main` and `develop`
   - Tag with version

6. Hotfix Branches
   - Branch from: `main`
   - Branch naming: `hotfix/[description]`
   - Merge to: `main` and `develop`
   - Tag with version

### Commit Guidelines

#### Commit Messages
Use semantic commit messages:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

Example:
```
feat(auth): add OAuth2 authentication

Implement OAuth2 flow with Google provider
Add user profile sync

Closes #123
```

### Pull Requests

#### Creating PRs
1. Update branch from develop
2. Run tests locally
3. Update documentation
4. Create detailed PR description

#### PR Template
```markdown
### Changes
Describe your changes here

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

### Documentation
- [ ] Updated docs
- [ ] Added examples

### Related Issues
- Fixes #123
- Related to #456
```

#### Review Process
1. Code review by team members
2. Address feedback
3. Update tests if needed
4. Get final approval

### Code Style

#### Python
- Follow PEP 8
- Use Black formatter
- Maximum line length: 88
- Use type hints

Example:
```python
from typing import List, Optional

def process_data(items: List[str], limit: Optional[int] = None) -> dict:
    """Process input items with optional limit.

    Args:
        items: List of items to process
        limit: Optional processing limit

    Returns:
        Processed data dictionary
    """
    result = {}
    for item in items[:limit]:
        result[item] = len(item)
    return result
```

#### Documentation
- Use docstrings (Google style)
- Add type hints
- Include examples
- Update README.md

### Testing

#### Unit Tests
- Use pytest
- Follow AAA pattern
- Mock external services
- Name tests descriptively

Example:
```python
def test_process_data_with_limit():
    # Arrange
    items = ["a", "bb", "ccc"]
    limit = 2

    # Act
    result = process_data(items, limit)

    # Assert
    assert len(result) == 2
    assert result["a"] == 1
    assert result["bb"] == 2
```

#### Integration Tests
- Test API endpoints
- Use test database
- Clean up after tests
- Check error cases

### Documentation

#### API Documentation
- Use OpenAPI/Swagger
- Include examples
- Document errors
- Keep up to date

#### Code Documentation
- Add inline comments
- Write clear docstrings
- Update README.md
- Create examples

### Review Guidelines

#### Code Review
1. Check functionality
2. Verify tests
3. Review documentation
4. Check performance
5. Look for security issues

#### Review Checklist
- [ ] Follows style guide
- [ ] Has tests
- [ ] Updates docs
- [ ] Handles errors
- [ ] Performance considered

### Getting Help
- Check documentation
- Ask in team chat
- Open an issue
- Request review

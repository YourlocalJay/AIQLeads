# Contributing to AIQLeads

## Branch Strategy

We follow a strict GitFlow branching strategy:

### Main Branches
- `main`: Production-ready code
  - Protected branch
  - Requires PR review
  - Always deployable
- `develop`: Integration branch for features
  - Protected branch
  - Requires PR review
  - Base for feature branches

### Supporting Branches
- `feature/*`: New features
  - Branch from: `develop`
  - Merge to: `develop`
  - Naming: `feature/description-in-kebab-case`
  - Delete after merge
- `hotfix/*`: Emergency fixes
  - Branch from: `main`
  - Merge to: `main` and `develop`
  - Naming: `hotfix/issue-description`
- `release/*`: Release preparation
  - Branch from: `develop`
  - Merge to: `main` and `develop`
  - Naming: `release/vX.Y.Z`

## Development Process

1. Create feature branch from `develop`
2. Implement changes
3. Write/update tests
4. Update documentation
5. Submit pull request to `develop`
6. Delete branch after merge

## Code Standards

- Follow PEP 8 for Python code
- Write comprehensive tests
- Document all functions and classes
- Keep commits atomic and well-described

## Pull Request Process

1. Update relevant documentation
2. Update the README.md if needed
3. Update the changelog
4. Get review from at least one team member
5. Ensure CI passes

## Testing

- Write unit tests for all new code
- Maintain at least 80% code coverage
- Include integration tests where appropriate
- Test performance impact of changes

## Branch Cleanup

- Branches are automatically deleted after merge
- Stale branches (60+ days old) are marked for cleanup
- Archive important branches if needed
- Regular cleanup of stale branches

## Release Process

1. Create release branch
2. Update version numbers
3. Run final tests
4. Create PR to `main`
5. Tag release after merge
6. Merge changes back to `develop`
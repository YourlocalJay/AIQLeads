# AIQLeads Repository Cleanup Guide

## Overview
This document outlines the comprehensive cleanup strategy for the AIQLeads repository, focusing on code quality, dependency management, and maintainability.

## Quick Reference

### 🧹 Quick Cleanup
Run the cleanup script:
```bash
bash cleanup_script.sh
```

### 🛠 Development Setup
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install development dependencies
pip install -r requirements.txt
pip install black ruff isort pytest
```

## Cleanup Phases

### 1. Untracked Files
- Removes unnecessary files
- Consolidates documentation
- Cleans up cache and temporary files

### 2. Code Quality Tools
- Black: Code formatting
- Ruff: Linting
- isort: Import sorting

### 3. Continuous Integration
Automated via GitHub Actions:
- Code quality checks
- Dependency review
- Test coverage reporting

### 4. Pre-Commit Hooks
Automatically enforce:
- Trailing whitespace removal
- End of file fixes
- YAML validation
- Code formatting
- Import sorting

## Best Practices

### Dependency Management
- Regular updates via Dependabot
- License and vulnerability checks
- Explicit dependency allowlist

### Git Hygiene
- Use meaningful commit messages
- Keep branches clean
- Delete merged branches

## Troubleshooting
- If pre-commit fails, run `pre-commit run --all-files`
- Check GitHub Actions for detailed error logs

## Contributing
1. Install pre-commit hooks
2. Follow code quality guidelines
3. Pass all CI checks before merging

## License
See project root for licensing information.

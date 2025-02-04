#!/bin/bash

# Phase 1: Quick Wins Cleanup Script

# Identify and list untracked files
echo "Untracked files:"
git ls-files --others --exclude-standard

# Optional: Prompt for file deletion confirmation
read -p "Do you want to remove these untracked files? (y/n) " confirm
if [ "$confirm" = "y" ]; then
    git clean -fd
fi

# Create docs directory if not exists
mkdir -p docs

# Move and consolidate documentation
mv README.md docs/README.md 2>/dev/null
mv UPDATE.md docs/UPDATE.md 2>/dev/null
mv REVIEW.md docs/REVIEW.md 2>/dev/null

# Create a consolidated documentation file
cat docs/README.md docs/UPDATE.md docs/REVIEW.md > docs/PROJECT_DOCUMENTATION.md
rm docs/README.md docs/UPDATE.md docs/REVIEW.md 2>/dev/null

# Check Docker configurations
echo "Docker Configuration Status:"
if [ -f docker-compose.yml ] && [ -f Dockerfile ]; then
    echo "Multiple Docker config files detected. Review and consolidate."
fi

# Clean up potential cache and temporary files
find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" \) -exec rm -rf {} +
find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" \) -delete

echo "Quick cleanup completed!"

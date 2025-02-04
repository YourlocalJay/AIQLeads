#!/bin/bash

# Enhanced Cleanup Script for AIQLeads Project

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to log messages
log_message() {
    local color=$1
    local message=$2
    echo -e "${color}[CLEANUP] ${message}${NC}"
}

# Validate repository
validate_repo() {
    if [ ! -d ".git" ]; then
        log_message "$RED" "Error: Not in a git repository!"
        exit 1
    fi
}

# Cleanup untracked and ignored files
cleanup_untracked_files() {
    log_message "$YELLOW" "Cleaning untracked files..."
    
    # Dry run first to show what will be deleted
    log_message "$GREEN" "Files to be removed:"
    git clean -n -d -x
    
    read -p "Proceed with removal? (y/N) " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git clean -f -d -x
        log_message "$GREEN" "Untracked files cleaned successfully!"
    else
        log_message "$YELLOW" "File cleanup cancelled."
    fi
}

# Consolidate documentation
consolidate_docs() {
    log_message "$YELLOW" "Consolidating documentation..."
    mkdir -p docs/archive

    # Move old documentation files to archive
    mv README.md docs/archive/README.md.bak 2>/dev/null
    mv UPDATE.md docs/archive/UPDATE.md.bak 2>/dev/null
    mv REVIEW.md docs/archive/REVIEW.md.bak 2>/dev/null

    # Create comprehensive documentation
    cat > docs/README.md << EOL
# AIQLeads Project Documentation

## Project Overview
[Brief project description]

## Versions
- Current Version: [X.Y.Z]
- Last Updated: $(date '+%Y-%m-%d')

## Quick Start
[Installation and setup instructions]

## Archived Documents
Previous documentation can be found in the \`docs/archive\` directory.
EOL

    log_message "$GREEN" "Documentation consolidated!"
}

# Clean up Python cache and compiled files
clean_python_artifacts() {
    log_message "$YELLOW" "Removing Python cache files..."
    find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" \) -exec rm -rf {} +
    find . -type f -name "*.py[co]" -delete
    log_message "$GREEN" "Python artifacts cleaned!"
}

# Prune old git branches
prune_branches() {
    log_message "$YELLOW" "Pruning merged branches..."
    git branch --merged | grep -v "\*" | grep -v "main" | grep -v "develop" | xargs -n 1 git branch -d
    log_message "$GREEN" "Branches pruned successfully!"
}

# Run all cleanup tasks
main() {
    validate_repo
    
    cleanup_untracked_files
    consolidate_docs
    clean_python_artifacts
    prune_branches

    log_message "$GREEN" "Repository cleanup complete! 🧹"
}

# Execute main function
main

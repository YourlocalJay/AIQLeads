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
    log_message "$YELLOW" "Analyzing untracked files..."
    
    # Show untracked files
    log_message "$GREEN" "Untracked files:"
    git ls-files --others --exclude-standard

    # Dry run of git clean
    log_message "$GREEN" "Files that will be removed:"
    git clean -n -d -x
    
    read -p "Do you want to remove these untracked files? (y/N) " confirm
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

    # Move existing docs to archive
    for doc in README.md UPDATE.md REVIEW.md; do
        if [ -f "$doc" ]; then
            mv "$doc" "docs/archive/${doc}.bak"
            log_message "$GREEN" "Archived $doc"
        fi
    done

    # Create comprehensive README
    cat > README.md << EOL
# AIQLeads Project

## Project Overview
Comprehensive AI-driven lead management system

## Quick Start
- Clone the repository
- Install dependencies: \`pip install -r requirements.txt\`
- Run the application

## Documentation
Detailed documentation available in the \`docs/\` directory.

## Previous Versions
Previous documentation can be found in \`docs/archive/\`.
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
    git branch --merged | grep -v "\*" | grep -v "main" | grep -v "develop" | xargs -n 1 git branch -d 2>/dev/null
    log_message "$GREEN" "Branches pruned successfully!"
}

# Main cleanup function
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

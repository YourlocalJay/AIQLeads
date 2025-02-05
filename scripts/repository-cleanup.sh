#!/bin/bash

# AIQLeads Repository Cleanup and Optimization Script

# Exit on any error
set -e

# Function to log messages
log() {
    echo "[CLEANUP] $1"
}

# Cleanup Utilities
cleanup_repository() {
    log "Starting comprehensive repository cleanup..."

    # Remove unnecessary files and directories
    log "Removing unnecessary files and temporary artifacts"
    find . -type f \( \
        -name "*.log" \
        -o -name "*.tmp" \
        -o -name "*.bak" \
        -o -name ".DS_Store" \
        -o -name "Thumbs.db" \
    \) -delete

    # Clean up cached and temporary directories
    log "Cleaning up cached and temporary directories"
    rm -rf \
        .cache \
        __pycache__ \
        .pytest_cache \
        .mypy_cache \
        node_modules/.cache

    # Remove large files that might have been accidentally committed
    log "Checking for and removing large files"
    find . -type f -size +100M | xargs -I {} rm -f {}
}

# Dependency Management
manage_dependencies() {
    log "Managing project dependencies"

    # Python dependency cleanup
    if [ -f requirements.txt ]; then
        log "Cleaning Python dependencies"
        pip freeze > requirements.txt
        pip clean
    fi

    # Node.js dependency cleanup
    if [ -f package.json ]; then
        log "Cleaning Node.js dependencies"
        npm prune
        npm audit fix
    fi

    # Remove unused dependencies
    log "Removing unused dependencies"
    npm outdated
    npm update
}

# Git Repository Optimization
optimize_git() {
    log "Optimizing Git repository"
    
    # Prune unnecessary references
    git gc --prune=now
    
    # Clean up unnecessary files
    git clean -fd
    
    # Remove large files from git history
    git filter-branch --force --index-filter \
        "git rm --cached --ignore-unmatch **/large_file*" \
        --prune-empty --tag-name-filter cat -- --all
}

# Code Quality and Formatting
code_quality() {
    log "Improving code quality"
    
    # Run linters
    if [ -f .eslintrc.json ]; then
        npx eslint . --fix
    fi
    
    if [ -f .pylintrc ]; then
        pylint **/*.py
    fi
    
    # Format code
    npx prettier --write .
    black .
}

# Main execution
main() {
    cleanup_repository
    manage_dependencies
    optimize_git
    code_quality
    
    log "Repository cleanup and optimization completed successfully!"
}

# Run the main function
main
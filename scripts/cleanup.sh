#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting repository cleanup...${NC}"

# Function to confirm actions
confirm() {
    read -r -p "${1:-Are you sure? [y/N]} " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}

# Run repository analysis
echo -e "\n${YELLOW}Running repository analysis...${NC}"
python3 scripts/repo_analysis.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Error running analysis script. Please check the script and try again.${NC}"
    exit 1
fi

# Read and parse analysis results
ANALYSIS_FILE="repo_analysis.json"
if [ ! -f "$ANALYSIS_FILE" ]; then
    echo -e "${RED}Analysis file not found. Please run the analysis script first.${NC}"
    exit 1
fi

# Clean Python cache files
echo -e "\n${YELLOW}Cleaning Python cache files...${NC}"
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Clean temporary files
echo -e "\n${YELLOW}Cleaning temporary files...${NC}"
find . -type f -name "*.log" -delete
find . -type f -name "*.tmp" -delete
find . -type f -name ".DS_Store" -delete
find . -type f -name "*.swp" -delete
find . -type f -name "*.swo" -delete

# Clean old backup files
echo -e "\n${YELLOW}Cleaning backup files...${NC}"
find . -type f -name "*~" -delete
find . -type f -name "*.bak" -delete

# Clean empty directories
echo -e "\n${YELLOW}Cleaning empty directories...${NC}"
find . -type d -empty -delete

# Handle duplicate files
echo -e "\n${YELLOW}Checking duplicate files from analysis...${NC}"
if confirm "Would you like to review and remove duplicate files? [y/N] "; then
    # Python script to process duplicates
    python3 - <<EOF
import json
import os
from pathlib import Path

with open('repo_analysis.json', 'r') as f:
    data = json.load(f)

duplicates = data.get('duplicate_files', {})
for hash_value, file_list in duplicates.items():
    if len(file_list) > 1:
        print(f"\nDuplicate files found:")
        for i, file_path in enumerate(file_list, 1):
            print(f"{i}. {file_path}")
        
        keep = input("\nEnter the number of the file to keep (other copies will be removed): ")
        try:
            keep_idx = int(keep) - 1
            if 0 <= keep_idx < len(file_list):
                for i, file_path in enumerate(file_list):
                    if i != keep_idx:
                        try:
                            os.remove(file_path)
                            print(f"Removed: {file_path}")
                        except Exception as e:
                            print(f"Error removing {file_path}: {e}")
        except ValueError:
            print("Invalid input, skipping...")
EOF
fi

# Git cleanup
echo -e "\n${YELLOW}Cleaning Git repository...${NC}"
if confirm "Would you like to clean the Git repository (this will run git gc)? [y/N] "; then
    git gc --aggressive --prune=now
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "\n${YELLOW}Creating .gitignore file...${NC}"
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Logs and databases
*.log
*.sqlite3

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
*.bak
*.tmp
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/
EOL
fi

echo -e "\n${GREEN}Cleanup completed!${NC}"
echo -e "${YELLOW}Please review the changes before committing.${NC}"

# Optional: List remaining TODOs
echo -e "\n${YELLOW}Searching for TODO comments in code...${NC}"
find . -type f -name "*.py" -exec grep -l "TODO" {} \;

echo -e "\n${GREEN}All done!${NC}"

#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting repository cleanup...${NC}"

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

echo -e "\n${GREEN}Basic cleanup completed!${NC}"

# Run more complex analysis
echo -e "\n${YELLOW}Running repository analysis...${NC}"
python3 scripts/analyze.py

echo -e "\n${GREEN}All done!${NC}"

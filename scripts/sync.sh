#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Syncing changes...${NC}"

# Pull latest changes first
git pull origin main

# Add all changes
git add .

# Get the current timestamp
timestamp=$(date +"%Y-%m-%d %H:%M:%S")

# Commit with timestamp
git commit -m "Auto-sync: ${timestamp}"

# Push changes
git push origin main

echo -e "${GREEN}Sync completed!${NC}"

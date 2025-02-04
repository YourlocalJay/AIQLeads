#!/bin/bash

# Pre-deployment Check Script

# Check system requirements
echo "Checking system requirements..."

# Python version check
PYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
if [[ $(echo "${PYTHON_VERSION} >= 3.9" | bc) -eq 1 ]]; then
    echo "Python version ${PYTHON_VERSION} OK"
else
    echo "Error: Python 3.9+ required, found ${PYTHON_VERSION}"
    exit 1
fi

# Docker check
if command -v docker &> /dev/null; then
    echo "Docker installation OK"
else
    echo "Error: Docker not found"
    exit 1
fi

# Redis check
redis-cli ping &> /dev/null
if [ $? -eq 0 ]; then
    echo "Redis connection OK"
else
    echo "Error: Redis connection failed"
    exit 1
fi

# PostgreSQL check
if psql -V &> /dev/null; then
    echo "PostgreSQL client OK"
else
    echo "Error: PostgreSQL client not found"
    exit 1
fi

echo "All pre-deployment checks passed"
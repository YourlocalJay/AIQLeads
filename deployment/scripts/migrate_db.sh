#!/bin/bash

# Database Migration Script

echo "Starting database migration..."

# Load environment variables
source "../config/${ENV}.env"

# Create database backup
echo "Creating database backup..."
DATESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -F c -f "../backups/${DB_NAME}_${DATESTAMP}.backup"

# Run migrations
echo "Running database migrations..."
python3 manage.py migrate

echo "Database migration completed"
#!/bin/bash

# AIQLeads Deployment Script

# Configuration
APP_NAME="aiqleads"
ENV=${1:-"production"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment-specific configuration
source "../config/${ENV}.env"

# Deployment Steps
echo "Starting deployment for ${APP_NAME} to ${ENV} environment"

# 1. Pre-deployment checks
echo "Running pre-deployment checks..."
./pre_deploy_check.sh

# 2. Database migration
echo "Running database migrations..."
./migrate_db.sh

# 3. Deploy application
echo "Deploying application..."
./deploy_app.sh

# 4. Setup monitoring
echo "Setting up monitoring..."
./setup_monitoring.sh

# 5. Run verification
echo "Running verification..."
./verify_deployment.sh

echo "Deployment completed"
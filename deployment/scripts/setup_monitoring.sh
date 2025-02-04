#!/bin/bash

# Monitoring Setup Script

echo "Setting up monitoring..."

# Load environment variables
source "../config/${ENV}.env"

# Configure Prometheus
echo "Configuring Prometheus..."
envsubst < ../monitoring/prometheus.yml.template > prometheus.yml

# Configure alerts
echo "Setting up alerts..."
envsubst < ../monitoring/alerts.yml.template > alerts.yml

# Deploy monitoring stack
echo "Deploying monitoring stack..."
docker-compose -f ../monitoring/docker-compose.yml up -d

echo "Monitoring setup completed"
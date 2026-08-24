#!/bin/bash
# Bash Deployment Script for Google Cloud Run
set -e

PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
REGION="us-central1"
SERVICE_NAME="agentshield"

echo "??? Deploying AgentShield to Google Cloud Run..."

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Please specify GCP Project ID: ./deploy_cloudrun.sh YOUR_PROJECT_ID"
    exit 1
fi

echo "Using GCP Project: $PROJECT_ID"

gcloud run deploy $SERVICE_NAME     --source .     --region $REGION     --project $PROJECT_ID     --allow-unauthenticated     --port 8080

echo "? Deployment Complete! AgentShield is live on Google Cloud Run."

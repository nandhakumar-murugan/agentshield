# PowerShell Deployment Script for Google Cloud Run
param (
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "agentshield"
)

Write-Host "??? Deploying AgentShield to Google Cloud Run..." -ForegroundColor Cyan

if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Error "Please provide a ProjectId: .\deploy_cloudrun.ps1 -ProjectId YOUR_PROJECT_ID"
        exit 1
    }
}

Write-Host "Using Google Cloud Project: $ProjectId" -ForegroundColor Yellow

# Deploy to Cloud Run
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --project $ProjectId `
    --allow-unauthenticated `
    --port 8080

Write-Host "? Deployment Complete! Visit your Cloud Run service URL to access AgentShield." -ForegroundColor Green

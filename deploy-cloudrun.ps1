# Cloud Run Deployment Script for Manga Wellness Backend (PowerShell)
# This script deploys your app to Google Cloud Run with proper configuration

param(
    [string]$ProjectId = "hackathon-472205",
    [string]$ServiceName = "manga-wellness-backend",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host "Starting Cloud Run deployment..." -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Cyan
Write-Host "Service: $ServiceName" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Yellow

# Ensure you're authenticated
Write-Host "Checking authentication..." -ForegroundColor Yellow
$authAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $authAccount) {
    Write-Host "Not authenticated. Please run: gcloud auth login" -ForegroundColor Red
    exit 1
}

# Set the project
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build the container image
Write-Host "Building container image..." -ForegroundColor Yellow
gcloud builds submit --tag $ImageName

# Deploy to Cloud Run with Secret Manager integration
Write-Host "Deploying to Cloud Run with Secret Manager secrets..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --image $ImageName `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --port 8080 `
    --memory 2Gi `
    --cpu 2 `
    --timeout 3600 `
    --concurrency 80 `
    --max-instances 10 `
    --set-env-vars "VERTEX_AI_PROJECT_ID=$ProjectId" `
    --set-env-vars "VERTEX_AI_LOCATION=$Region" `
    --set-env-vars "GCS_BUCKET_NAME=hackathon-asset-genai" `
    --set-env-vars "IMAGEN_SEED=42" `
    --set-env-vars "JWT_ALGORITHM=HS256" `
    --set-env-vars "JWT_EXPIRES_MIN=10080" `
    --set-env-vars "CORS_ORIGINS=https://calmira-ai-1.web.app,http://localhost:8080,http://localhost:5173,http://localhost:3000" `
    --update-secrets "GEMINI_API_KEY=gemini-api-key:latest" `
    --update-secrets "JWT_SECRET_KEY=jwt-secret-key:latest" `
    --update-secrets "GOOGLE_CLIENT_ID=google-client-id:latest" `
    --update-secrets "DATABASE_URL=database-url:latest"

# Get the service URL
$ServiceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"

Write-Host "==================================" -ForegroundColor Yellow
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "API Docs: $ServiceUrl/docs" -ForegroundColor Cyan
Write-Host "Socket.IO: $ServiceUrl/socket.io" -ForegroundColor Cyan
Write-Host "Health Check: $ServiceUrl/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ SECRET MANAGER INTEGRATION ACTIVE" -ForegroundColor Green
Write-Host "Your app is now using secure Secret Manager for:" -ForegroundColor Yellow
Write-Host "   • Gemini API Key (auto-rotatable)" -ForegroundColor White
Write-Host "   • JWT Secret Key" -ForegroundColor White  
Write-Host "   • Google Client ID" -ForegroundColor White
Write-Host "   • Database URL" -ForegroundColor White
Write-Host ""
Write-Host "To update secrets, use:" -ForegroundColor Yellow
Write-Host "   gcloud secrets versions add <secret-name> --data-file=-" -ForegroundColor White
Write-Host ""
Write-Host "Frontend is configured for: https://calmira-ai-1.web.app" -ForegroundColor Yellow
Write-Host "Local testing available at: http://localhost:8080" -ForegroundColor Yellow
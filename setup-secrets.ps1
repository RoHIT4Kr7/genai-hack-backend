# Secret Manager Setup Script
# Run this BEFORE deploying to Cloud Run to set up your secrets securely

param(
    [string]$ProjectId = "hackathon-472205"
)

Write-Host "Setting up Google Secret Manager..." -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Yellow

# Set the project
gcloud config set project $ProjectId

# Enable Secret Manager API
Write-Host "Enabling Secret Manager API..." -ForegroundColor Yellow
gcloud services enable secretmanager.googleapis.com

Write-Host ""
Write-Host "Creating secrets in Secret Manager..." -ForegroundColor Yellow
Write-Host "You'll be prompted to enter each secret value." -ForegroundColor Cyan
Write-Host "IMPORTANT: Enter the actual values, not the old exposed ones!" -ForegroundColor Red
Write-Host ""

# Create secrets interactively
Write-Host "1. Creating gemini-api-key secret..." -ForegroundColor Cyan
Write-Host "   Enter your NEW Gemini API key (regenerate if compromised):"
$geminiKey = Read-Host -AsSecureString
$geminiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($geminiKey))
echo $geminiKeyPlain | gcloud secrets create gemini-api-key --data-file=-

Write-Host "2. Creating jwt-secret-key secret..." -ForegroundColor Cyan
Write-Host "   Enter a strong JWT secret (minimum 32 characters):"
$jwtSecret = Read-Host -AsSecureString
$jwtSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($jwtSecret))
echo $jwtSecretPlain | gcloud secrets create jwt-secret-key --data-file=-

Write-Host "3. Creating google-client-id secret..." -ForegroundColor Cyan
Write-Host "   Enter your Google OAuth Client ID:"
$clientId = Read-Host
echo $clientId | gcloud secrets create google-client-id --data-file=-

Write-Host "4. Creating database-url secret..." -ForegroundColor Cyan
Write-Host "   Enter your database connection URL:"
Write-Host "   (Update password if compromised!)"
$dbUrl = Read-Host -AsSecureString
$dbUrlPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbUrl))
echo $dbUrlPlain | gcloud secrets create database-url --data-file=-

Write-Host ""
Write-Host "All secrets created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Verifying secrets..." -ForegroundColor Yellow
gcloud secrets list --filter="name:gemini-api-key OR name:jwt-secret-key OR name:google-client-id OR name:database-url"

Write-Host "" 
Write-Host "Secret Manager setup complete!" -ForegroundColor Green
Write-Host "You can now run the Cloud Run deployment script." -ForegroundColor Cyan
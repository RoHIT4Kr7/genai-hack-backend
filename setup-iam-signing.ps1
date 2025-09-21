#!/usr/bin/env powershell
<#
.SYNOPSIS
    Setup IAM Service Account Credentials API for signed URL generation in Cloud Run

.DESCRIPTION
    This script enables the IAM Service Account Credentials API and grants the necessary
    permissions for Cloud Run service accounts to generate signed URLs using the 
    SignBlob operation.

.NOTES
    This is the recommended keyless approach for Cloud Run signed URL generation.
    It eliminates the need for service account private keys by using IAM Credentials API.
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "hackathon-472205"
)

Write-Host "🚀 Setting up IAM Service Account Credentials API for signed URL generation" -ForegroundColor Green

# Set the project
Write-Host "Setting project: $ProjectId" -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable IAM Service Account Credentials API
Write-Host "Enabling IAM Service Account Credentials API..." -ForegroundColor Yellow
gcloud services enable iamcredentials.googleapis.com

# Get the Cloud Run service account
Write-Host "Getting Cloud Run service account details..." -ForegroundColor Yellow
$cloudRunSA = gcloud run services describe manga-wellness-backend --region=us-central1 --format="value(spec.template.spec.serviceAccountName)" 2>$null

if ([string]::IsNullOrEmpty($cloudRunSA)) {
    # If no custom service account is set, use the default Compute Engine service account
    $projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)"
    $cloudRunSA = "$projectNumber-compute@developer.gserviceaccount.com"
    Write-Host "Using default Compute Engine service account: $cloudRunSA" -ForegroundColor Cyan
} else {
    Write-Host "Using custom Cloud Run service account: $cloudRunSA" -ForegroundColor Cyan
}

# Grant Service Account Token Creator role to the Cloud Run service account
# This allows it to call iam.serviceAccounts.signBlob for signed URL generation
Write-Host "Granting Service Account Token Creator role..." -ForegroundColor Yellow
gcloud iam service-accounts add-iam-policy-binding $cloudRunSA `
    --member="serviceAccount:$cloudRunSA" `
    --role="roles/iam.serviceAccountTokenCreator"

# Verify the permissions
Write-Host "Verifying IAM permissions..." -ForegroundColor Yellow
gcloud iam service-accounts get-iam-policy $cloudRunSA

Write-Host ""
Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The Cloud Run service can now generate signed URLs using:" -ForegroundColor Cyan
Write-Host "  • IAM Service Account Credentials API (iamcredentials.googleapis.com)" -ForegroundColor White
Write-Host "  • Service Account Token Creator role for SignBlob operations" -ForegroundColor White
Write-Host "  • V4 signed URLs with impersonated credentials" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy the updated service with the new IAM-based signing code" -ForegroundColor White
Write-Host "  2. Test meditation generation to verify signed URLs work" -ForegroundColor White
Write-Host ""
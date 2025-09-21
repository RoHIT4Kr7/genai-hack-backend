# Pre-Deployment Checklist for DhyaanService

## 🔧 Configuration Updates Made

### ✅ DhyaanService Fixes Applied:

- [x] Fixed API key handling for Secret Manager compatibility
- [x] Updated GCS bucket configuration for Cloud Run environment
- [x] Added proper service account handling for managed credentials
- [x] Improved error logging for deployment debugging
- [x] Added environment detection (Cloud Run vs Local)

### ✅ Deployment Script Updates:

- [x] Fixed port from 8000 to 8080 (matches cloudrun-service.yaml)
- [x] Secret Manager integration confirmed
- [x] Environment variables properly set

## 🚀 Ready to Deploy Commands:

### 1. Build and Deploy:

```powershell
cd D:\calmira\Clean-backend\genai-hack-backend
.\deploy-cloudrun.ps1
```

### 2. Alternative individual commands:

```powershell
# Set project
gcloud config set project hackathon-472205

# Build image
gcloud builds submit --tag gcr.io/hackathon-472205/manga-wellness-backend

# Deploy with secrets
gcloud run deploy manga-wellness-backend \
    --image gcr.io/hackathon-472205/manga-wellness-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 10 \
    --set-env-vars "VERTEX_AI_PROJECT_ID=hackathon-472205" \
    --set-env-vars "VERTEX_AI_LOCATION=us-central1" \
    --set-env-vars "GCS_BUCKET_NAME=hackathon-asset-genai" \
    --update-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

## 🧪 Post-Deployment Testing:

### Test Service Health:

```powershell
python test_dhyaan_status.py
```

### Expected Results:

1. General health endpoint: ✅ 200 OK
2. Dhyaan test endpoint: ✅ 200 OK with `"dhyaan_service_available": true`
3. Service should show improved logging with Secret Manager integration

## 🔍 Troubleshooting:

### If DhyaanService fails to initialize:

1. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Verify Secret Manager secrets exist and are accessible
3. Check service account has proper permissions

### Key Log Messages to Look For:

- "✅ Using Gemini API key from environment variable (Secret Manager mounted)"
- "🌍 Environment: GCloud Run"
- "🔐 Using GCloud Run managed service account for GCS"
- "✅ GCS connection successful, bucket: hackathon-asset-genai"

## 📋 Secret Manager Requirements:

Make sure these secrets exist in Secret Manager:

- `gemini-api-key` (your Gemini API key)
- `jwt-secret-key` (for authentication)
- `google-client-id` (for Google OAuth)
- `database-url` (database connection)

Check with: `gcloud secrets list`

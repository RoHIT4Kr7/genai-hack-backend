#!/bin/bash

# Cloud Run Deployment Script for Manga Wellness Backend
# This script deploys your app to Google Cloud Run with proper configuration

set -e  # Exit on any error

# Configuration
PROJECT_ID="hackathon-472205"
SERVICE_NAME="manga-wellness-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting Cloud Run deployment..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "=================================="

# Ensure you're authenticated
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Not authenticated. Please run: gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🛠️ Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build the container image
echo "🏗️ Building container image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 10 \
    --set-env-vars "VERTEX_AI_PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "VERTEX_AI_LOCATION=$REGION" \
    --set-env-vars "GCS_BUCKET_NAME=hackathon-asset-genai" \
    --set-env-vars "IMAGEN_SEED=42" \
    --set-env-vars "JWT_ALGORITHM=HS256" \
    --set-env-vars "JWT_EXPIRES_MIN=10080"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "=================================="
echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📖 API Docs: $SERVICE_URL/docs"
echo "🔌 Socket.IO: $SERVICE_URL/socket.io"
echo "💖 Health Check: $SERVICE_URL/health"
echo ""
echo "🔐 IMPORTANT: Remember to set up your secrets in Secret Manager:"
echo "   gcloud secrets create gemini-api-key --data-file=-"
echo "   gcloud secrets create jwt-secret-key --data-file=-"
echo "   gcloud secrets create google-client-id --data-file=-"
echo "   gcloud secrets create database-url --data-file=-"
echo ""
echo "📝 Update your frontend CORS_ORIGINS to include: $SERVICE_URL"
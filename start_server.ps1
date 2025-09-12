#!/usr/bin/env pwsh
# PowerShell script to start the Manga Mental Wellness Backend

Write-Host "🚀 Starting Manga Mental Wellness Backend" -ForegroundColor Green
Write-Host "=" * 50

# Check if virtual environment exists and activate it
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
} elseif (Test-Path ".venv\bin\activate") {
    Write-Host "🔄 Activating virtual environment (Unix)..." -ForegroundColor Yellow
    & .venv\bin\activate
} else {
    Write-Host "⚠️  No virtual environment found" -ForegroundColor Yellow
}

# Set up environment variables
$serviceKeyPath = Join-Path $PSScriptRoot "servicekey.json"
if ((Test-Path $serviceKeyPath) -and (-not $env:GOOGLE_APPLICATION_CREDENTIALS)) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = $serviceKeyPath
    Write-Host "🔐 Using service account: $serviceKeyPath" -ForegroundColor Cyan
}

Write-Host "🌟 Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "📖 API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔌 Socket.IO: http://localhost:8000/socket.io" -ForegroundColor Cyan
Write-Host "-" * 50

# Start the server using uvicorn directly
try {
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
} catch {
    Write-Host "❌ Failed to start server: $_" -ForegroundColor Red
    Write-Host "🔧 Try: pip install uvicorn fastapi" -ForegroundColor Yellow
    exit 1
}
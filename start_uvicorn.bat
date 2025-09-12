@echo off
echo 🚀 Starting with uvicorn directly
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo 🔄 Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Set up service account if exists
if exist "servicekey.json" (
    set GOOGLE_APPLICATION_CREDENTIALS=%~dp0servicekey.json
    echo 🔐 Using service account: servicekey.json
)

echo 🌟 Starting server on http://localhost:8000
echo 📖 Docs: http://localhost:8000/docs
echo.

REM Start server with uvicorn directly
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
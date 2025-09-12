@echo off
echo 🚀 Starting Manga Mental Wellness Backend (Simple Mode)
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo 🔄 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found at .venv
)

REM Start the server
echo 🌟 Starting FastAPI server...
python simple_start.py

pause
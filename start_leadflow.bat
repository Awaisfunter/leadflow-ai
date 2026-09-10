@echo off
echo Starting LeadFlow AI...
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to the day2 directory relative to script location
cd /d "%SCRIPT_DIR%day2"

REM Check if we're in the right directory
if not exist "backend\app\main.py" (
    echo ERROR: Cannot find backend\app\main.py
    echo Make sure you're running this from the LeadFlow AI root directory
    echo.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed (basic check for fastapi)
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Try running: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo LeadFlow AI Starting...
echo ========================================
echo.
echo Web interface will be available at:
echo http://localhost:8000
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

REM Start the FastAPI application
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo LeadFlow AI stopped.
pause
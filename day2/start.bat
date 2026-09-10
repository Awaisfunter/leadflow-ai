@echo off
title LeadFlow AI — Day 2 Operating System
echo ==========================================================
echo Starting LeadFlow AI (v0 Operating System)
echo ==========================================================
echo.

cd /d "%~dp0"

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.11+.
    pause
    exit /b 1
)

REM Create logs directory if missing
if not exist "logs" mkdir logs

REM Copy .env.example to .env if .env does not exist
if not exist ".env" (
    echo [NOTICE] .env not found. Copying .env.example to .env...
    copy .env.example .env >nul
)

echo [INFO] Starting FastAPI server on http://localhost:8000 ...
echo [INFO] Access the SDR Dashboard at: http://localhost:8000
echo.
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause

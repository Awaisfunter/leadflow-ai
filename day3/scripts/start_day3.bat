@echo off
REM ============================================================
REM LeadFlow AI — Day 3 Core Operating System Startup Script
REM Author: Awais Saeed | Applied AI Engineer Candidate
REM Target User: Non-developer Inbound SDR
REM ============================================================

echo [1/3] Navigating to Day 2 Application Core...
cd /d "%~dp0..\..\day2"

echo [2/3] Checking environment configuration...
if not exist .env (
    if exist .env.example (
        echo Copying .env.example to .env (Default offline deterministic fallback)...
        copy .env.example .env >nul
    )
)

echo [3/3] Starting LeadFlow AI FastAPI Server with Real Integrations...
echo.
echo ============================================================
echo   LeadFlow AI Dashboard available at: http://localhost:8000
echo   FastAPI Documentation available at: http://localhost:8000/docs
echo ============================================================
echo.

python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause

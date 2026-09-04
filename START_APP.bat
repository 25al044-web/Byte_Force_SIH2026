@echo off
setlocal enabledelayedexpansion

title SIH26188 - Screening System Launcher

echo =========================================================================
echo   SIH26188: AI-Based Fake Identity & Document Screening System
echo   Hackathon Startup Launcher
echo =========================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [*] Verifying project environment...

:: 1. Check Python virtual environment
if not exist "%ROOT_DIR%backend\.venv\Scripts\python.exe" (
    echo [!] ERROR: Backend Python virtual environment not found!
    echo     Expected location: %ROOT_DIR%backend\.venv
    echo.
    echo     Setup instructions:
    echo       1. cd backend
    echo       2. python -m venv .venv
    echo       3. .\.venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: 2. Check Frontend node_modules
if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [!] ERROR: Frontend dependencies not found!
    echo     Expected location: %ROOT_DIR%frontend\node_modules
    echo.
    echo     Setup instructions:
    echo       1. cd frontend
    echo       2. npm install
    echo.
    pause
    exit /b 1
)

echo [OK] Backend environment verified (.venv).
echo [OK] Frontend dependencies verified (node_modules).
echo.

:: 3. Check InsightFace local model cache
set "INSIGHTFACE_MODEL=%USERPROFILE%\.insightface\models\buffalo_sc"
if exist "%INSIGHTFACE_MODEL%" (
    echo [OK] InsightFace model cache verified (buffalo_sc ready).
) else (
    echo [!] NOTE: InsightFace model not yet cached locally.
    echo     First face comparison will download buffalo_sc (~100MB).
)
echo.

:: 4. Start FastAPI Backend
echo [*] Starting FastAPI screening backend on http://127.0.0.1:8000 ...
start "SIH26188-Backend" cmd /k "cd /d "%ROOT_DIR%backend" && .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 5. Start React Vite Frontend
echo [*] Starting Vite frontend server on http://localhost:5173 ...
start "SIH26188-Frontend" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

:: 6. Wait for servers to initialize
echo [*] Waiting for services to initialize...
timeout /t 4 /nobreak >nul

:: 7. Launch default web browser
echo [*] Opening screening dashboard in web browser...
start http://localhost:5173

echo.
echo =========================================================================
echo   SYSTEM READY FOR SCREENING DEMO!
echo =========================================================================
echo   Dashboard UI : http://localhost:5173
echo   API Health   : http://127.0.0.1:8000/api/health
echo   API Docs     : http://127.0.0.1:8000/docs
echo.
echo   To stop all servers, run: STOP_APP.bat
echo =========================================================================
echo.
pause

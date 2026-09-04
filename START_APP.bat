@echo off
setlocal

title SIH26188 Launcher

REM Project root = folder containing this BAT file
set "ROOT=%~dp0"

echo.
echo ==========================================
echo   SIH26188 Identity Screening System
echo ==========================================
echo.

REM -----------------------------
REM CHECK BACKEND
REM -----------------------------
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not found:
    echo %ROOT%backend\.venv
    echo.
    echo Create it first inside backend.
    pause
    exit /b 1
)

REM -----------------------------
REM CHECK FRONTEND
REM -----------------------------
if not exist "%ROOT%frontend\node_modules" (
    echo [ERROR] frontend\node_modules not found.
    echo.
    echo Run:
    echo cd frontend
    echo npm install
    echo.
    pause
    exit /b 1
)

echo [1/4] Starting FastAPI backend...

start "SIH26188 Backend" /D "%ROOT%backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload"

echo [2/4] Waiting for backend...
timeout /t 4 /nobreak >nul

echo [3/4] Starting React frontend...

start "SIH26188 Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"

echo [4/4] Opening browser...
timeout /t 4 /nobreak >nul

start "" "http://localhost:5173"

echo.
echo ==========================================
echo   SIH26188 STARTED
echo ==========================================
echo.
echo Backend : http://127.0.0.1:8000
echo Swagger : http://127.0.0.1:8000/docs
echo Frontend: http://localhost:5173
echo.
echo Keep the Backend and Frontend windows open.
echo.

timeout /t 3 /nobreak >nul
exit /b 0
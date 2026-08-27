@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo     F.R.I.D.A.Y. AI Assistant Setup (Windows)
echo ==========================================

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: 1. Setup Backend
echo [1/4] Setting up Python Backend...
cd "%PROJECT_ROOT%backend"
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Installing backend dependencies...
call .\venv\Scripts\pip.exe install -r requirements.txt

:: 2. Setup Frontend
echo [2/4] Setting up Desktop Frontend...
cd "%PROJECT_ROOT%desktop"
echo Syncing frontend dependencies...
call npm install


:: 3. Launch Backend
echo [3/4] Starting FRIDAY Backend Server...
cd "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
start "FRIDAY Backend" /min cmd /c ".\backend\venv\Scripts\python.exe backend\run_backend.py"

timeout /t 3 /nobreak >nul

:: 4. Launch Desktop Application (Tauri)
echo [4/4] Starting FRIDAY Desktop Application (Tauri)...
cd "%PROJECT_ROOT%desktop"
call npm run desktop:dev

pause

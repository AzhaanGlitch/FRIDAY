@echo off
title FRIDAY AI Assistant Launcher
echo ==========================================
echo     F.R.I.D.A.Y. AI Assistant Setup
echo ==========================================

set PROJECT_ROOT=%~dp0
cd /d %PROJECT_ROOT%

:: 1. Setup Backend
echo [1/4] Setting up Python Backend...
cd /d %PROJECT_ROOT%\backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: 2. Setup Frontend
echo [2/4] Setting up Desktop Frontend...
cd /d %PROJECT_ROOT%\desktop
if not exist "node_modules" (
    echo Installing node dependencies...
    call npm install
)

:: 3. Launch Backend in separate window
echo [3/4] Starting FRIDAY Backend Server...
cd /d %PROJECT_ROOT%
start "FRIDAY Backend Server" cmd /k "set PYTHONPATH=%PROJECT_ROOT% && call backend\venv\Scripts\activate.bat && python backend\run_backend.py"


timeout /t 3 /nobreak >nul

:: 4. Launch Desktop Frontend
echo [4/4] Starting FRIDAY Desktop UI...
cd /d %PROJECT_ROOT%\desktop
call npm run dev

pause

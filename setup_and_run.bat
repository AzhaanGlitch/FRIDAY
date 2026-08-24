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

:: 4. Launch Desktop Application (Tauri or Web Preview fallback)
echo [4/4] Starting FRIDAY Desktop Application Interface...
cd /d %PROJECT_ROOT%\desktop

where link.exe >nul 2>nul
if %errorlevel%==0 goto LINKER_READY

if exist "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
    echo [Info] Activating Visual Studio C++ Compiler environment...
    call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
)

if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
    echo [Info] Activating Visual Studio C++ Compiler environment...
    call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
)

if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" (
    echo [Info] Activating Visual Studio C++ Compiler environment...
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
)

:LINKER_READY

where link.exe >nul 2>nul
if %errorlevel%==0 (
    echo [Info] C++ Linker ready. Launching native Tauri Desktop App...
    call npm run desktop:dev
) else (
    echo.
    echo ========================================================================
    echo [NOTICE] C++ Build Tools (link.exe) not found on your Windows system.
    echo To compile & run the native Tauri Desktop window, install:
    echo "Desktop development with C++" from Visual Studio Build Tools:
    echo https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo Launching FRIDAY Web Interface on http://localhost:3000 in the meantime...
    echo ========================================================================
    echo.
    call npm run dev
)

pause

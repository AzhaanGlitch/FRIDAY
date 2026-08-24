@echo off
title FRIDAY AI Assistant Launcher
echo ==========================================
echo     F.R.I.D.A.Y. AI Assistant Setup
echo ==========================================

set PROJECT_ROOT=%~dp0
set PATH=C:\Users\Azhaan\.cargo\bin;%PATH%
cd /d %PROJECT_ROOT%

:: 1. Auto-initialize Visual Studio C++ Compiler environment if needed
where link.exe >nul 2>nul
if %errorlevel%==0 goto COMPILER_SET
if exist "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
:COMPILER_SET

:: 2. Setup Backend
echo [1/4] Setting up Python Backend...
cd /d %PROJECT_ROOT%\backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: 3. Setup Frontend
echo [2/4] Setting up Desktop Frontend...
cd /d %PROJECT_ROOT%\desktop
if not exist "node_modules" (
    echo Installing node dependencies...
    call npm install
)

:: 4. Launch Backend in separate window
echo [3/4] Starting FRIDAY Backend Server...
cd /d %PROJECT_ROOT%
start "FRIDAY Backend Server" cmd /k "set PYTHONPATH=%PROJECT_ROOT% && call backend\venv\Scripts\activate.bat && python backend\run_backend.py"

timeout /t 3 /nobreak >nul

:: 5. Launch Desktop Application Interface
echo [4/4] Starting FRIDAY Desktop Application Interface...
cd /d %PROJECT_ROOT%\desktop

where link.exe >nul 2>nul
if %errorlevel% neq 0 goto USE_WEB_DEV

echo [Info] C++ Linker ready. Launching native Tauri Desktop App...
call npm run desktop:dev
goto END

:USE_WEB_DEV
echo.
echo ========================================================================
echo [NOTICE] C++ Build Tools (link.exe) not found on your Windows system.
echo Launching FRIDAY Web Interface on http://localhost:3000 in the meantime...
echo ========================================================================
echo.
call npm run dev

:END
pause

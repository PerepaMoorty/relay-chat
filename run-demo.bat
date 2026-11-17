@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo         Relay - Real-Time Chat Application Demo
echo ========================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Setup Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

:: 3. Install Dependencies
echo [*] Installing / checking dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

:: 4. Seed Database if Missing
if not exist "instance\relay.db" (
    echo [*] Seeding demo database (alice, bob, carol, admin)...
    flask --app run seed-demo
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Seed-demo CLI not yet ready; database will initialize on server start.
    )
) else (
    echo [*] Database instance\relay.db already exists.
)

:: 5. Launch Relay Server
echo.
echo ========================================================
echo  Server starting at: http://localhost:5000
echo  Press Ctrl+C to terminate the server.
echo ========================================================
echo.

python run.py

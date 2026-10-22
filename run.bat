@echo off
title Smart Library Management System
echo ========================================================
echo   Starting Smart Library Management System...
echo ========================================================
echo.
cd /d "%~dp0"

:: Step 1: Detect Python or Py launcher
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ========================================================
        echo [ERROR] Python is not installed or not added to your PATH!
        echo.
        echo Please install Python 3.10+ from https://www.python.org/
        echo Make sure to check the box: "Add python.exe to PATH".
        echo ========================================================
        echo.
        pause
        exit /b
    ) else (
        set PYTHON_CMD=py
    )
)

:: Step 2: Auto-check and install required packages if teammate doesn't have them
%PYTHON_CMD% -c "import flask, flask_cors, dotenv, werkzeug" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] First-time setup detected! Installing required packages...
    %PYTHON_CMD% -m pip install -r requirements.txt
    echo [SETUP] Packages installed successfully!
    echo.
)

:: Step 3: Run Flask server (it will automatically open the browser once ready)
echo Starting Flask Server (Keep this window open while using the website)...
echo.
%PYTHON_CMD% app.py
pause


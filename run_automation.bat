@echo off
title Solange Project - Network Automation Suite
echo.
echo ========================================
echo   SOLANGE PROJECT AUTOMATION SUITE
echo ========================================
echo.
echo Starting Python automation suite...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing/updating dependencies...
    python -m pip install -r requirements.txt
    echo.
)

REM Run the main script
python main.py

echo.
echo Automation suite finished.
pause

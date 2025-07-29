@echo off
title Solange Network Automation - Web Interface
echo.
echo =========================================
echo   SOLANGE NETWORK AUTOMATION WEB CMD
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Installing/updating dependencies...
python main.py

echo.
echo Starting web server...
echo.
echo =========================================
echo   OPEN YOUR BROWSER TO:
echo   http://localhost:5000
echo =========================================
echo.
echo Press Ctrl+C to stop the server
echo.

@REM cd web_gui
@REM python app.py

pause

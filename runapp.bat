@echo off
title CYBER SKULLS Repinning Tool - Enhanced Processing
color 0A

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo ========================================
echo    CYBER SKULLS REPINNING TOOL
echo    Enhanced ARC-19 Processing Engine
echo ========================================
echo.
echo NEW FEATURES:
echo   * 3x faster ARC-19 processing
echo   * Smart caching system
echo   * Enhanced error recovery
echo   * IPFS gateway URL support
echo.

REM Check if Python is installed
echo [STEP 1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python first:
    echo  * Download from: https://python.org/downloads/
    echo  * Make sure to check "Add Python to PATH" during installation
    echo  * Restart this script after installation
    echo.
    start https://python.org/downloads/
    pause
    exit /b 1
)

python --version
echo Python is available

REM Check if we're in the correct directory and files exist
echo.
echo [STEP 2/3] Checking application files...
echo Current directory: %CD%

if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    echo.
    echo This script should be in the same folder as app.py
    echo Make sure both runapp.bat and app.py are in the same directory
    echo.
    echo Files in current directory:
    dir /b *.py 2>nul
    if errorlevel 1 (
        echo No Python files found in this directory
    )
    echo.
    pause
    exit /b 1
)

if not exist "utils.py" (
    echo ERROR: utils.py not found - application may be incomplete
    echo.
    echo Please reinstall the application using the installer
    echo.
    pause
    exit /b 1
)

echo Application files found

REM Check if streamlit is installed
echo.
echo [STEP 3/3] Checking dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing required packages...
    echo This may take a few minutes for first-time setup...
    echo.
    
    REM Check if requirements.txt exists
    if exist "requirements.txt" (
        echo Installing from requirements.txt...
        python -m pip install -r requirements.txt --upgrade --quiet
    ) else (
        echo Installing core packages...
        python -m pip install streamlit pandas requests base58 py-algorand-sdk py-multibase --upgrade --quiet
    )
    
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo.
        echo Possible solutions:
        echo  * Check your internet connection
        echo  * Try running as administrator
        echo  * Manually install: pip install streamlit pandas requests base58 py-algorand-sdk py-multibase
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed successfully!
    echo.
) else (
    echo All dependencies are available
)

echo.
echo STARTING CYBER SKULLS REPINNING TOOL...
echo.
echo The app will open in your default web browser automatically
echo URL: http://localhost:8501
echo.
echo IMPORTANT:
echo   * Keep this window open while using the app
echo   * To stop the app: Close this window or press Ctrl+C
echo   * For support: https://github.com/theonetwoone/CYBER_repinning
echo.
echo ================================================================
echo   Enhanced processing is now active for better performance!
echo ================================================================
echo.

REM Run the Streamlit app
streamlit run app.py --server.headless true --server.port 8501

echo.
echo App has stopped.
echo.
echo Thank you for using CYBER SKULLS Repinning Tool!
echo For updates and support, visit: https://github.com/theonetwoone/CYBER_repinning
echo.
pause 
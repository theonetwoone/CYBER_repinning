@echo off
echo ========================================
echo    CYBER Repinning - Streamlit App
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first and make sure it's in your system PATH
    echo.
    pause
    exit /b 1
)

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing requirements...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        echo Please check your internet connection and try again
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Requirements installed successfully!
    echo.
)

echo Starting Streamlit app...
echo.
echo The app will open in your default web browser.
echo To stop the app, close this window or press Ctrl+C
echo.

REM Run the Streamlit app
streamlit run app.py

echo.
echo App has stopped.
pause 
@echo off
title IPFS Gateway Risk Tester UI
color 0A

echo.
echo ========================================
echo 🚀 IPFS Gateway Risk Tester UI
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH!
    echo 💡 Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not available!
    echo 💡 Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip found
echo.

REM Check if utils.py exists
if not exist "utils.py" (
    echo ❌ utils.py not found!
    echo 💡 Make sure you're running this from the project directory
    pause
    exit /b 1
)

echo ✅ utils.py found
echo.

echo 📦 Installing essential packages...
echo.

REM Install essential packages
echo Installing streamlit...
pip install streamlit --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ❌ Failed to install streamlit
    pause
    exit /b 1
)

echo Installing pandas...
pip install pandas --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ❌ Failed to install pandas
    pause
    exit /b 1
)

echo Installing requests...
pip install requests --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ❌ Failed to install requests
    pause
    exit /b 1
)

echo Installing algorand-python-sdk...
pip install algorand-python-sdk --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ❌ Failed to install algorand-python-sdk
    pause
    exit /b 1
)

echo Installing base58...
pip install base58 --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ❌ Failed to install base58
    pause
    exit /b 1
)

echo Installing py-multibase...
pip install py-multibase --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ❌ Failed to install py-multibase
    pause
    exit /b 1
)

echo.
echo 🎨 Installing optional packages for enhanced charts...
pip install plotly --quiet --disable-pip-version-check >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ plotly installed - you'll get fancy charts!
) else (
    echo ⚠️ plotly failed to install - using simple charts instead
)

echo.
echo ✅ All essential packages installed successfully!
echo.

echo 🌐 Starting Gateway Risk Tester UI...
echo 💡 The app will open in your default web browser
echo 🔧 Close this window or press Ctrl+C to stop the server
echo.

REM Start the Streamlit app with cyber theme
streamlit run gateway_tester_ui.py ^
    --theme.base dark ^
    --theme.primaryColor "#00FF41" ^
    --theme.backgroundColor "#0E1117" ^
    --theme.secondaryBackgroundColor "#1E1E1E" ^
    --theme.textColor "#FFFFFF" ^
    --server.headless false ^
    --browser.gatherUsageStats false

echo.
echo 👋 Gateway Risk Tester UI has been closed.
pause 
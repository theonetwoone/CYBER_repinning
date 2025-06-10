@echo off
echo ===============================================
echo   CYBER SKULLS REPINNING TOOL INSTALLER
echo   Windows One-Click Installer
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please download and install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in PATH
    echo Please download and install Git from https://git-scm.com
    pause
    exit /b 1
)

echo [OK] Git found:
git --version

:: Create installation directory
set INSTALL_DIR=%USERPROFILE%\Desktop\CYBER_repinning
echo.
echo [INFO] Installing to: %INSTALL_DIR%

:: Remove existing directory if it exists
if exist "%INSTALL_DIR%" (
    echo [INFO] Removing existing installation...
    rmdir /s /q "%INSTALL_DIR%"
)

:: Clone the repository
echo [INFO] Cloning repository from GitHub...
git clone https://github.com/theonetwo-dev/cyber_repinning.git "%INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to clone repository
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

:: Change to project directory
cd /d "%INSTALL_DIR%"

:: Install Python requirements
echo [INFO] Installing Python dependencies...
pip install streamlit pandas requests base58 py-algorand-sdk multibase
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

:: Create desktop shortcut
echo [INFO] Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\CYBER_SKULLS_REPINNING.bat
echo @echo off > "%SHORTCUT_PATH%"
echo cd /d "%INSTALL_DIR%" >> "%SHORTCUT_PATH%"
echo streamlit run app.py >> "%SHORTCUT_PATH%"

echo.
echo ===============================================
echo   INSTALLATION COMPLETE!
echo ===============================================
echo.
echo The CYBER SKULLS Repinning Tool has been installed to:
echo %INSTALL_DIR%
echo.
echo To run the application:
echo 1. Double-click "CYBER_SKULLS_REPINNING.bat" on your desktop
echo 2. Or run this command in Command Prompt:
echo    streamlit run "%INSTALL_DIR%\app.py"
echo.
echo The app will open in your web browser at http://localhost:8501
echo.
pause 
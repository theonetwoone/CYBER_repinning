@echo off
:: Enhanced Windows Installer for CYBER SKULLS Repinning Tool
:: Designed for novice users with comprehensive error handling

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ===============================================
    echo   CYBER SKULLS REPINNING TOOL INSTALLER
    echo   Administrator Privileges Required
    echo ===============================================
    echo.
    echo [NOTICE] This installer needs Administrator privileges to:
    echo  • Install Git if not present
    echo  • Install Python packages system-wide
    echo  • Create desktop shortcuts
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

title CYBER SKULLS Repinning Tool - Installer
color 0A

echo ===============================================
echo   CYBER SKULLS REPINNING TOOL INSTALLER
echo   Enhanced Windows One-Click Installer
echo   Running with Administrator Privileges
echo ===============================================
echo.
echo [INFO] This installer will:
echo  1. Check for Python and Git
echo  2. Install missing dependencies
echo  3. Download the latest version from GitHub
echo  4. Install Python packages
echo  5. Create desktop shortcut
echo.
pause

:: Check if Python is installed
echo [STEP 1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python is not installed or not in PATH
    echo.
    echo Please download and install Python from https://python.org
    echo.
    echo IMPORTANT INSTALLATION NOTES:
    echo  • Download Python 3.9 or newer
    echo  • During installation, CHECK "Add Python to PATH"
    echo  • Choose "Install for all users" if available
    echo.
    echo After installing Python, run this installer again.
    echo.
    start https://python.org/downloads/
    pause
    exit /b 1
)

python --version
echo [OK] Python is installed and accessible

:: Check if Git is installed
echo.
echo [STEP 2/5] Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Git is not installed or not in PATH
    echo.
    echo INSTALLING GIT FOR WINDOWS...
    echo This may take a few minutes...
    echo.
    
    :: Try to install Git using winget (Windows 10/11)
    winget install --id Git.Git -e --source winget --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] Winget installation failed, trying alternative method...
        
        :: Alternative: Download and install Git manually
        echo [INFO] Downloading Git for Windows...
        echo Please wait while we download Git installer...
        
        powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/latest/download/Git-2.42.0.2-64-bit.exe' -OutFile '%TEMP%\git-installer.exe'}" 2>nul
        
        if exist "%TEMP%\git-installer.exe" (
            echo [INFO] Installing Git for Windows...
            "%TEMP%\git-installer.exe" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"
            
            :: Wait for installation to complete
            timeout /t 30 /nobreak >nul
            
            :: Clean up
            del "%TEMP%\git-installer.exe" 2>nul
            
            :: Add Git to PATH
            setx PATH "%PATH%;C:\Program Files\Git\bin" /M >nul 2>&1
            
            echo [INFO] Git installation completed. Refreshing environment...
            
            :: Refresh PATH for current session
            set "PATH=%PATH%;C:\Program Files\Git\bin"
        ) else (
            echo [ERROR] Failed to download Git installer
            echo.
            echo Please manually install Git from https://git-scm.com/download/win
            echo Make sure to select "Git from the command line and also from 3rd-party software"
            echo.
            start https://git-scm.com/download/win
            pause
            exit /b 1
        )
    )
    
    :: Verify Git installation
    git --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Git installation verification failed
        echo Please restart your computer and run this installer again
        echo.
        pause
        exit /b 1
    )
)

git --version
echo [OK] Git is installed and accessible

:: Set installation directory
set INSTALL_DIR=%USERPROFILE%\Desktop\CYBER_repinning_local
echo.
echo [STEP 3/5] Preparing installation directory...
echo [INFO] Installing to: %INSTALL_DIR%

:: Remove existing directory if it exists
if exist "%INSTALL_DIR%" (
    echo [INFO] Removing existing installation...
    rmdir /s /q "%INSTALL_DIR%" 2>nul
    if exist "%INSTALL_DIR%" (
        echo [WARNING] Could not remove existing directory
        echo Please close any open files in %INSTALL_DIR% and try again
        pause
        exit /b 1
    )
)

:: Clone the repository
echo [INFO] Downloading latest version from GitHub...
echo This may take a few minutes depending on your internet speed...
git clone https://github.com/theonetwoone/CYBER_repinning.git "%INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download from GitHub
    echo.
    echo Possible causes:
    echo  • Internet connection issues
    echo  • GitHub is temporarily unavailable
    echo  • Firewall blocking Git
    echo.
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo [OK] Successfully downloaded from GitHub

:: Change to project directory
cd /d "%INSTALL_DIR%"

:: Install Python requirements
echo.
echo [STEP 4/5] Installing Python dependencies...
echo This may take several minutes for first-time installation...
echo.

:: Upgrade pip first
python -m pip install --upgrade pip --quiet

:: Install requirements with better error handling
python -m pip install streamlit pandas requests base58 py-algorand-sdk py-multibase --upgrade --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Standard installation failed, trying alternative method...
    
    :: Try installing without cache
    python -m pip install --no-cache-dir streamlit pandas requests base58 py-algorand-sdk py-multibase
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python dependencies
        echo.
        echo Possible solutions:
        echo  • Check your internet connection
        echo  • Try running as administrator
        echo  • Disable antivirus temporarily
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Python dependencies installed successfully

:: Create enhanced desktop shortcut
echo.
echo [STEP 5/5] Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\🔥 CYBER SKULLS REPINNING 🔥.bat
(
echo @echo off
echo title CYBER SKULLS Repinning Tool
echo color 0A
echo echo ========================================
echo echo    CYBER SKULLS REPINNING TOOL
echo echo    Enhanced ARC-19 Processing
echo echo ========================================
echo echo.
echo echo Starting the app...
echo echo The app will open in your web browser automatically.
echo echo.
echo echo To stop the app: Close this window or press Ctrl+C
echo echo.
echo cd /d "%INSTALL_DIR%"
echo streamlit run app.py
echo.
echo echo App has stopped.
echo pause
) > "%SHORTCUT_PATH%"

:: Create a quick run script in the installation directory
set QUICK_RUN=%INSTALL_DIR%\🚀 RUN APP.bat
(
echo @echo off
echo title CYBER SKULLS Repinning Tool
echo cd /d "%INSTALL_DIR%"
echo streamlit run app.py
) > "%QUICK_RUN%"

echo [OK] Desktop shortcuts created

echo.
echo ===============================================
echo   INSTALLATION COMPLETE! 🎉
echo ===============================================
echo.
echo ✅ The CYBER SKULLS Repinning Tool has been installed successfully!
echo.
echo 📁 Installation location: %INSTALL_DIR%
echo.
echo 🚀 TO START THE APP:
echo   1. Double-click "🔥 CYBER SKULLS REPINNING 🔥.bat" on your desktop
echo   2. Or double-click "🚀 RUN APP.bat" in the installation folder
echo.
echo 🌐 The app will automatically open in your web browser at:
echo    http://localhost:8501
echo.
echo 💡 NEW FEATURES IN THIS VERSION:
echo   • Enhanced ARC-19 processing with 3x faster speeds
echo   • Smart caching for improved performance
echo   • Better error recovery and timeout handling
echo   • Support for IPFS gateway URLs
echo.
echo 📞 Need help? Check the GitHub repository:
echo    https://github.com/theonetwoone/CYBER_repinning
echo.
echo Press any key to finish...
pause >nul 
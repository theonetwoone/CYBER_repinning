@echo off
REM IPFS Gateway Risk Tester - Quick Test Scripts
REM =============================================

echo.
echo 🌐 IPFS Gateway Risk Tester
echo ===========================

:menu
echo.
echo Choose a test option:
echo 1. Test 3 random well-known CIDs (quick test)
echo 2. Test 10 random well-known CIDs (comprehensive)
echo 3. Test custom CIDs (enter manually)
echo 4. Test CIDs from file
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Testing 3 random CIDs with 5 gateways...
    python gateway_risk_tester.py --random-test 3 --gateways 5
    goto menu
)

if "%choice%"=="2" (
    echo.
    echo 🚀 Testing 10 random CIDs with 8 gateways...
    python gateway_risk_tester.py --random-test 10 --gateways 8
    goto menu
)

if "%choice%"=="3" (
    echo.
    set /p custom_cids="Enter CIDs (comma-separated): "
    echo 🚀 Testing custom CIDs...
    python gateway_risk_tester.py --cids "%custom_cids%" --gateways 6
    goto menu
)

if "%choice%"=="4" (
    echo.
    set /p filename="Enter filename containing CIDs: "
    echo 🚀 Testing CIDs from file...
    python gateway_risk_tester.py --file "%filename%" --gateways 6
    goto menu
)

if "%choice%"=="5" (
    echo.
    echo 👋 Goodbye!
    exit /b 0
)

echo Invalid choice. Please try again.
goto menu 
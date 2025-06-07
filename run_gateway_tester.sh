#!/bin/bash

# IPFS Gateway Risk Tester UI Launcher with Auto-Install
# =====================================================

set -e  # Exit on any error

echo ""
echo "🚀 IPFS Gateway Risk Tester UI Launcher"
echo "========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "💡 Please install Python 3 from your package manager"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not available!"
    echo "💡 Please install pip3"
    exit 1
fi

echo "✅ pip3 found"

# Check if utils.py exists
if [ ! -f "utils.py" ]; then
    echo "❌ utils.py not found!"
    echo "💡 Make sure you're running this from the project directory"
    exit 1
fi

echo "✅ utils.py found"

echo ""
echo "📦 Installing required packages..."

# Function to install package
install_package() {
    local package_name=$1
    local pip_name=${2:-$1}
    
    echo "📦 Installing $package_name..."
    if pip3 install "$pip_name" --quiet --disable-pip-version-check; then
        echo "✅ $package_name installed successfully"
    else
        echo "❌ Failed to install $package_name"
        exit 1
    fi
}

# Install required packages
install_package "streamlit" "streamlit"
install_package "plotly" "plotly"
install_package "pandas" "pandas" 
install_package "requests" "requests"
install_package "algosdk" "algorand-python-sdk"
install_package "base58" "base58"
install_package "multibase" "py-multibase"

echo ""
echo "✅ All packages installed successfully!"
echo ""

echo "🌐 Starting Gateway Risk Tester UI..."
echo "💡 The app will open in your default web browser"
echo "🔧 Close this terminal or press Ctrl+C to stop the server"
echo "========================================="

# Start the Streamlit app with cyber theme
python3 -m streamlit run gateway_tester_ui.py \
    --theme.base dark \
    --theme.primaryColor "#00FF41" \
    --theme.backgroundColor "#0E1117" \
    --theme.secondaryBackgroundColor "#1E1E1E" \
    --theme.textColor "#FFFFFF" \
    --server.headless false \
    --browser.gatherUsageStats false

echo ""
echo "👋 Gateway Risk Tester UI has been closed." 
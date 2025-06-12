#!/bin/bash

# Enhanced macOS Installer for CYBER SKULLS Repinning Tool
# Designed for novice users with comprehensive error handling

echo "==============================================="
echo "  🔥 CYBER SKULLS REPINNING TOOL INSTALLER"
echo "  Enhanced macOS One-Click Installer"
echo "==============================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}[INFO]${NC} This installer will:"
echo "  1. Check for required dependencies (Python, Git)"
echo "  2. Install missing dependencies using Homebrew"
echo "  3. Download the latest version from GitHub"
echo "  4. Install Python packages"
echo "  5. Create desktop launcher"
echo
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Function to install Homebrew
install_homebrew() {
    echo -e "${YELLOW}[INFO]${NC} Installing Homebrew (package manager for macOS)..."
    echo "This is required to install Git and Python easily."
    echo
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        # Apple Silicon Macs
        export PATH="/opt/homebrew/bin:$PATH"
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
    elif [[ -f "/usr/local/bin/brew" ]]; then
        # Intel Macs
        export PATH="/usr/local/bin:$PATH"
        echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
    fi
    
    # Reload shell configuration
    source ~/.zshrc 2>/dev/null || true
}

# Check if Homebrew is installed
echo -e "${BLUE}[STEP 1/5]${NC} Checking package manager..."
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Homebrew is not installed"
    echo "Homebrew is the easiest way to install dependencies on macOS."
    echo
    echo "Would you like to install Homebrew? (recommended) [y/N]"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        install_homebrew
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}[ERROR]${NC} Homebrew installation failed"
            exit 1
        fi
    else
        echo -e "${YELLOW}[INFO]${NC} Continuing without Homebrew..."
        echo "You may need to install dependencies manually."
    fi
else
    echo -e "${GREEN}[OK]${NC} Homebrew found: $(brew --version | head -n1)"
fi

# Check if Python is installed
echo
echo -e "${BLUE}[STEP 2/5]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Python 3 is not installed"
    
    if command -v brew &> /dev/null; then
        echo "Installing Python 3 using Homebrew..."
        brew install python
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}[ERROR]${NC} Python installation failed"
            exit 1
        fi
    else
        echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
        echo
        echo "Please install Python 3:"
        echo "  • Download from: https://python.org/downloads/macos/"
        echo "  • Or install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "  • Then run: brew install python"
        open "https://python.org/downloads/macos/"
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} pip3 is not installed"
    echo "Installing pip3..."
    python3 -m ensurepip --upgrade
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} pip3 installation failed"
        echo "Please reinstall Python with pip included"
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} pip3 found"

# Check if Git is installed
echo
echo -e "${BLUE}[STEP 3/5]${NC} Checking Git installation..."
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Git is not installed"
    
    if command -v brew &> /dev/null; then
        echo "Installing Git using Homebrew..."
        brew install git
        if ! command -v git &> /dev/null; then
            echo -e "${RED}[ERROR]${NC} Git installation failed"
            exit 1
        fi
    else
        echo -e "${RED}[ERROR]${NC} Git is not installed"
        echo
        echo "Please install Git:"
        echo "  • Install Xcode Command Line Tools: xcode-select --install"
        echo "  • Or install via Homebrew: brew install git"
        echo "  • Or download from: https://git-scm.com/download/mac"
        echo
        echo "Installing Xcode Command Line Tools now..."
        xcode-select --install
        echo "After installation completes, run this installer again."
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} Git found: $(git --version)"

# Set installation directory
INSTALL_DIR="$HOME/Desktop/CYBER_repinning"
echo
echo -e "${BLUE}[STEP 4/5]${NC} Preparing installation directory..."
echo -e "${YELLOW}[INFO]${NC} Installing to: $INSTALL_DIR"

# Create Desktop directory if it doesn't exist
mkdir -p "$HOME/Desktop"

# Remove existing directory if it exists
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} Removing existing installation..."
    rm -rf "$INSTALL_DIR"
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${RED}[ERROR]${NC} Could not remove existing directory"
        echo "Please close any open files in $INSTALL_DIR and try again"
        exit 1
    fi
fi

# Clone the repository
echo -e "${YELLOW}[INFO]${NC} Downloading latest version from GitHub..."
echo "This may take a few minutes depending on your internet speed..."
if ! git clone https://github.com/theonetwoone/CYBER_repinning.git "$INSTALL_DIR"; then
    echo -e "${RED}[ERROR]${NC} Failed to download from GitHub"
    echo
    echo "Possible causes:"
    echo "  • Internet connection issues"
    echo "  • GitHub is temporarily unavailable"
    echo "  • Firewall blocking Git"
    echo
    echo "Please check your internet connection and try again"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Successfully downloaded from GitHub"

# Change to project directory
cd "$INSTALL_DIR"

# Install Python requirements
echo
echo -e "${BLUE}[STEP 5/5]${NC} Installing Python dependencies..."
echo "This may take several minutes for first-time installation..."
echo

# Upgrade pip first
python3 -m pip install --upgrade pip --quiet

# Install requirements with error handling
if ! pip3 install streamlit pandas requests base58 py-algorand-sdk py-multibase --upgrade --quiet; then
    echo -e "${YELLOW}[WARNING]${NC} Standard installation failed, trying alternative method..."
    
    # Try user installation
    if ! pip3 install --user streamlit pandas requests base58 py-algorand-sdk py-multibase; then
        echo -e "${RED}[ERROR]${NC} Failed to install Python dependencies"
        echo
        echo "Possible solutions:"
        echo "  • Check your internet connection"
        echo "  • Try running with sudo (not recommended)"
        echo "  • Create a virtual environment"
        echo
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} Python dependencies installed successfully"

# Create enhanced launcher script
echo -e "${YELLOW}[INFO]${NC} Creating desktop launcher..."
LAUNCHER_PATH="$HOME/Desktop/🔥 CYBER SKULLS REPINNING 🔥.command"
cat > "$LAUNCHER_PATH" << 'EOF'
#!/bin/bash

# Set terminal colors
export TERM=xterm-256color

# Function to show colored output
show_header() {
    clear
    echo "========================================"
    echo "   🔥 CYBER SKULLS REPINNING TOOL 🔥"
    echo "    Enhanced ARC-19 Processing"
    echo "========================================"
    echo
    echo "🚀 Starting the app..."
    echo "📱 The app will open in your web browser automatically."
    echo
    echo "⚠️  To stop the app: Close this terminal or press Ctrl+C"
    echo
}

show_header

# Change to the correct directory
cd "$HOME/Desktop/CYBER_repinning"

# Check if directory exists
if [ ! -d "$HOME/Desktop/CYBER_repinning" ]; then
    echo "❌ Installation directory not found!"
    echo "Please run the installer again."
    echo
    read -p "Press Enter to close..."
    exit 1
fi

# Run the Streamlit app
python3 -m streamlit run app.py

echo
echo "App has stopped."
read -p "Press Enter to close..."
EOF

# Make launcher executable
chmod +x "$LAUNCHER_PATH"

# Also create a simple terminal launcher
TERMINAL_LAUNCHER="$HOME/Desktop/🚀 RUN APP (Terminal).command"
cat > "$TERMINAL_LAUNCHER" << 'EOF'
#!/bin/bash
cd "$HOME/Desktop/CYBER_repinning"
python3 -m streamlit run app.py
EOF
chmod +x "$TERMINAL_LAUNCHER"

# Create a quick run script in the installation directory
QUICK_RUN="$INSTALL_DIR/🚀 RUN APP.command"
cat > "$QUICK_RUN" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 -m streamlit run app.py
EOF
chmod +x "$QUICK_RUN"

echo -e "${GREEN}[OK]${NC} Desktop launchers created"

echo
echo "==============================================="
echo "  ✅ INSTALLATION COMPLETE! 🎉"
echo "==============================================="
echo
echo -e "${GREEN}✅ The CYBER SKULLS Repinning Tool has been installed successfully!${NC}"
echo
echo -e "${BLUE}📁 Installation location:${NC} $INSTALL_DIR"
echo
echo -e "${PURPLE}🚀 TO START THE APP:${NC}"
echo "  1. Double-click '🔥 CYBER SKULLS REPINNING 🔥.command' on your desktop"
echo "  2. Or double-click '🚀 RUN APP (Terminal).command' on your desktop"
echo "  3. Or double-click '🚀 RUN APP.command' in the installation folder"
echo "  4. Or run in Terminal: cd '$INSTALL_DIR' && python3 -m streamlit run app.py"
echo
echo -e "${BLUE}🌐 The app will automatically open in your web browser at:${NC}"
echo "   http://localhost:8501"
echo
echo -e "${YELLOW}💡 NEW FEATURES IN THIS VERSION:${NC}"
echo "  • Enhanced ARC-19 processing with 3x faster speeds"
echo "  • Smart caching for improved performance"
echo "  • Better error recovery and timeout handling"
echo "  • Support for IPFS gateway URLs"
echo
echo -e "${BLUE}📞 Need help?${NC} Check the GitHub repository:"
echo "   https://github.com/theonetwoone/CYBER_repinning"
echo
echo "Press Enter to finish..."
read 
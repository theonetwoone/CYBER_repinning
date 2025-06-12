#!/bin/bash

# Enhanced Linux Installer for CYBER SKULLS Repinning Tool
# Designed for novice users with comprehensive error handling

echo "==============================================="
echo "  🔥 CYBER SKULLS REPINNING TOOL INSTALLER"
echo "  Enhanced Linux One-Click Installer"
echo "==============================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Enhanced distribution detection
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_NAME=$NAME
        VERSION=$VERSION_ID
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        DISTRO=$(echo $DISTRIB_ID | tr '[:upper:]' '[:lower:]')
        DISTRO_NAME=$DISTRIB_DESCRIPTION
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
        DISTRO_NAME="Debian"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
        DISTRO_NAME="Red Hat Enterprise Linux"
    else
        DISTRO="unknown"
        DISTRO_NAME="Unknown Linux"
    fi
}

detect_distro

echo -e "${BLUE}[INFO]${NC} Detected Linux distribution: $DISTRO_NAME"
echo -e "${BLUE}[INFO]${NC} This installer will:"
echo "  1. Check for required dependencies (Python, Git)"
echo "  2. Install missing dependencies using system package manager"
echo "  3. Download the latest version from GitHub"
echo "  4. Install Python packages"
echo "  5. Create desktop launchers"
echo
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Function to install packages based on distribution
install_package() {
    local package=$1
    echo -e "${YELLOW}[INFO]${NC} Installing $package..."
    
    case $DISTRO in
        ubuntu|debian|mint|pop|elementary)
            sudo apt update && sudo apt install -y $package
            ;;
        centos|rhel|rocky|alma)
            if command -v dnf &> /dev/null; then
                sudo dnf install -y $package
            else
                sudo yum install -y $package
            fi
            ;;
        fedora)
            sudo dnf install -y $package
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -Sy --noconfirm $package
            ;;
        opensuse|suse)
            sudo zypper install -y $package
            ;;
        alpine)
            sudo apk add --no-cache $package
            ;;
        void)
            sudo xbps-install -Sy $package
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unsupported distribution: $DISTRO"
            echo "Please install $package manually using your distribution's package manager"
            return 1
            ;;
    esac
}

# Check for sudo privileges
echo -e "${BLUE}[STEP 1/5]${NC} Checking sudo privileges..."
if ! sudo -n true 2>/dev/null; then
    echo -e "${YELLOW}[INFO]${NC} This installer needs sudo privileges to install packages."
    echo "You may be prompted for your password."
    if ! sudo true; then
        echo -e "${RED}[ERROR]${NC} Sudo privileges required"
        exit 1
    fi
fi
echo -e "${GREEN}[OK]${NC} Sudo privileges confirmed"

# Check if Python is installed
echo
echo -e "${BLUE}[STEP 2/5]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Python 3 is not installed"
    echo "Installing Python 3..."
    
    case $DISTRO in
        ubuntu|debian|mint|pop|elementary)
            install_package "python3 python3-pip python3-venv"
            ;;
        centos|rhel|rocky|alma|fedora)
            install_package "python3 python3-pip"
            ;;
        arch|manjaro|endeavouros)
            install_package "python python-pip"
            ;;
        opensuse|suse)
            install_package "python3 python3-pip"
            ;;
        alpine)
            install_package "python3 py3-pip"
            ;;
        void)
            install_package "python3 python3-pip"
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Please install Python 3 manually"
            exit 1
            ;;
    esac
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Python 3 installation failed"
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} pip3 is not installed"
    echo "Installing pip3..."
    
    case $DISTRO in
        ubuntu|debian|mint|pop|elementary)
            install_package "python3-pip"
            ;;
        centos|rhel|rocky|alma|fedora)
            install_package "python3-pip"
            ;;
        arch|manjaro|endeavouros)
            install_package "python-pip"
            ;;
        opensuse|suse)
            install_package "python3-pip"
            ;;
        alpine)
            install_package "py3-pip"
            ;;
        void)
            install_package "python3-pip"
            ;;
        *)
            # Try to install pip using get-pip.py
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py --user
            rm get-pip.py
            ;;
    esac
    
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} pip3 installation failed"
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} pip3 found"

# Check if Git is installed
echo
echo -e "${BLUE}[STEP 3/5]${NC} Checking Git installation..."
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Git is not installed"
    echo "Installing Git..."
    
    case $DISTRO in
        ubuntu|debian|mint|pop|elementary)
            install_package "git"
            ;;
        centos|rhel|rocky|alma|fedora)
            install_package "git"
            ;;
        arch|manjaro|endeavouros)
            install_package "git"
            ;;
        opensuse|suse)
            install_package "git"
            ;;
        alpine)
            install_package "git"
            ;;
        void)
            install_package "git"
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Please install Git manually"
            exit 1
            ;;
    esac
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Git installation failed"
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
python3 -m pip install --upgrade pip --user --quiet

# Install requirements (try user installation first)
echo -e "${YELLOW}[INFO]${NC} Installing Python packages..."
if ! python3 -m pip install --user streamlit pandas requests base58 py-algorand-sdk py-multibase --upgrade --quiet; then
    echo -e "${YELLOW}[WARNING]${NC} User installation failed, trying system installation..."
    if ! python3 -m pip install streamlit pandas requests base58 py-algorand-sdk py-multibase --upgrade; then
        echo -e "${RED}[ERROR]${NC} Failed to install Python dependencies"
        echo
        echo "Possible solutions:"
        echo "  • Check your internet connection"
        echo "  • Try running with sudo (not recommended for pip)"
        echo "  • Create a virtual environment"
        echo "  • Install packages manually: pip3 install streamlit pandas requests base58 py-algorand-sdk py-multibase"
        echo
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} Python dependencies installed successfully"

# Create enhanced desktop launchers
echo -e "${YELLOW}[INFO]${NC} Creating desktop launchers..."

# Create XDG desktop launcher
DESKTOP_LAUNCHER="$HOME/Desktop/🔥 CYBER SKULLS REPINNING 🔥.desktop"
cat > "$DESKTOP_LAUNCHER" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=🔥 CYBER SKULLS REPINNING 🔥
Comment=Algorand NFT Collection Repinning Tool - Enhanced ARC-19 Processing
Exec=bash -c "cd '$INSTALL_DIR' && python3 -m streamlit run app.py"
Icon=$INSTALL_DIR/assets/icon.png
Terminal=true
Categories=Development;Utility;
StartupWMClass=streamlit
Keywords=algorand;nft;ipfs;repinning;blockchain;
MimeType=text/csv;
EOF

# Make desktop launcher executable
chmod +x "$DESKTOP_LAUNCHER"

# Also create a simple shell script launcher for easier execution
SCRIPT_LAUNCHER="$HOME/Desktop/🚀 RUN CYBER SKULLS.sh"
cat > "$SCRIPT_LAUNCHER" << 'EOF'
#!/bin/bash

# Set colors for better terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

clear
echo -e "${PURPLE}========================================"
echo -e "   🔥 CYBER SKULLS REPINNING TOOL 🔥"
echo -e "    Enhanced ARC-19 Processing"
echo -e "========================================${NC}"
echo
echo -e "${GREEN}🚀 Starting the app...${NC}"
echo -e "${BLUE}📱 The app will open in your web browser automatically.${NC}"
echo
echo -e "${YELLOW}⚠️  To stop the app: Close this terminal or press Ctrl+C${NC}"
echo

# Change to installation directory
cd "$HOME/Desktop/CYBER_repinning"

# Check if directory exists
if [ ! -d "$HOME/Desktop/CYBER_repinning" ]; then
    echo -e "${RED}❌ Installation directory not found!${NC}"
    echo "Please run the installer again."
    echo
    read -p "Press Enter to close..."
    exit 1
fi

# Run the app
python3 -m streamlit run app.py

echo
echo -e "${YELLOW}App has stopped.${NC}"
read -p "Press Enter to close..."
EOF

chmod +x "$SCRIPT_LAUNCHER"

# Create a quick run script in the installation directory
QUICK_RUN="$INSTALL_DIR/🚀 RUN APP.sh"
cat > "$QUICK_RUN" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 -m streamlit run app.py
EOF
chmod +x "$QUICK_RUN"

# Create a simple launcher for terminal users
TERMINAL_LAUNCHER="$INSTALL_DIR/run_app_terminal.sh"
cat > "$TERMINAL_LAUNCHER" << 'EOF'
#!/bin/bash
# Simple terminal launcher without graphics
cd "$(dirname "$0")"
echo "Starting CYBER SKULLS Repinning Tool..."
echo "Open your browser to: http://localhost:8501"
python3 -m streamlit run app.py
EOF
chmod +x "$TERMINAL_LAUNCHER"

echo -e "${GREEN}[OK]${NC} Desktop launchers created"

# Try to make the desktop launcher trusted (for some desktop environments)
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_LAUNCHER" "metadata::trusted" true 2>/dev/null || true
fi

echo
echo "==============================================="
echo "  ✅ INSTALLATION COMPLETE! 🎉"
echo "==============================================="
echo
echo -e "${GREEN}✅ The CYBER SKULLS Repinning Tool has been installed successfully!${NC}"
echo
echo -e "${BLUE}📁 Installation location:${NC} $INSTALL_DIR"
echo -e "${BLUE}🐧 Detected system:${NC} $DISTRO_NAME"
echo
echo -e "${PURPLE}🚀 TO START THE APP:${NC}"
echo "  1. Double-click '🔥 CYBER SKULLS REPINNING 🔥.desktop' on your desktop"
echo "  2. Or double-click '🚀 RUN CYBER SKULLS.sh' on your desktop"
echo "  3. Or double-click '🚀 RUN APP.sh' in the installation folder"
echo "  4. Or run in terminal: cd '$INSTALL_DIR' && python3 -m streamlit run app.py"
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
echo -e "${YELLOW}🔧 TROUBLESHOOTING TIPS:${NC}"
echo "  • If desktop launchers don't work, use the terminal command"
echo "  • For permission issues, try: chmod +x '$DESKTOP_LAUNCHER'"
echo "  • For Python path issues, try: python3 -m streamlit run app.py"
echo
echo -e "${BLUE}📞 Need help?${NC} Check the GitHub repository:"
echo "   https://github.com/theonetwoone/CYBER_repinning"
echo
echo "Press Enter to finish..."
read 
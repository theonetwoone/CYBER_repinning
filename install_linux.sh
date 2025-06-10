#!/bin/bash

echo "==============================================="
echo "  CYBER SKULLS REPINNING TOOL INSTALLER"
echo "  Linux One-Click Installer"
echo "==============================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

echo -e "${BLUE}[INFO]${NC} Detected Linux distribution: $DISTRO"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3:"
    case $DISTRO in
        ubuntu|debian)
            echo "  sudo apt update && sudo apt install python3 python3-pip"
            ;;
        centos|rhel|fedora)
            echo "  sudo yum install python3 python3-pip"
            ;;
        arch)
            echo "  sudo pacman -S python python-pip"
            ;;
        *)
            echo "  Use your distribution's package manager to install python3 and python3-pip"
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} pip3 is not installed"
    echo "Please install pip3:"
    case $DISTRO in
        ubuntu|debian)
            echo "  sudo apt install python3-pip"
            ;;
        centos|rhel|fedora)
            echo "  sudo yum install python3-pip"
            ;;
        arch)
            echo "  sudo pacman -S python-pip"
            ;;
        *)
            echo "  Use your distribution's package manager to install python3-pip"
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}[OK]${NC} pip3 found"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Git is not installed"
    echo "Please install Git:"
    case $DISTRO in
        ubuntu|debian)
            echo "  sudo apt install git"
            ;;
        centos|rhel|fedora)
            echo "  sudo yum install git"
            ;;
        arch)
            echo "  sudo pacman -S git"
            ;;
        *)
            echo "  Use your distribution's package manager to install git"
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Git found: $(git --version)"

# Set installation directory
INSTALL_DIR="$HOME/Desktop/CYBER_repinning"
echo
echo -e "${YELLOW}[INFO]${NC} Installing to: $INSTALL_DIR"

# Create Desktop directory if it doesn't exist
mkdir -p "$HOME/Desktop"

# Remove existing directory if it exists
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} Removing existing installation..."
    rm -rf "$INSTALL_DIR"
fi

# Clone the repository
echo -e "${YELLOW}[INFO]${NC} Cloning repository from GitHub..."
if ! git clone https://github.com/theonetwo-dev/cyber_repinning.git "$INSTALL_DIR"; then
    echo -e "${RED}[ERROR]${NC} Failed to clone repository"
    echo "Please check your internet connection and try again"
    exit 1
fi

# Change to project directory
cd "$INSTALL_DIR"

# Install Python requirements (try user installation first)
echo -e "${YELLOW}[INFO]${NC} Installing Python dependencies..."
if ! pip3 install --user streamlit pandas requests base58 py-algorand-sdk multibase; then
    echo -e "${YELLOW}[WARNING]${NC} User installation failed, trying system installation..."
    if ! pip3 install streamlit pandas requests base58 py-algorand-sdk multibase; then
        echo -e "${RED}[ERROR]${NC} Failed to install Python dependencies"
        echo "You may need to use 'sudo pip3 install' or create a virtual environment"
        exit 1
    fi
fi

# Create a desktop launcher
echo -e "${YELLOW}[INFO]${NC} Creating desktop launcher..."
LAUNCHER_PATH="$HOME/Desktop/CYBER_SKULLS_REPINNING.desktop"
cat > "$LAUNCHER_PATH" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=CYBER SKULLS Repinning Tool
Comment=Algorand NFT Collection Repinning Tool
Exec=bash -c "cd '$INSTALL_DIR' && python3 -m streamlit run app.py"
Icon=$INSTALL_DIR/icon.png
Terminal=true
Categories=Development;
EOF

# Make launcher executable
chmod +x "$LAUNCHER_PATH"

# Also create a simple shell script launcher
SCRIPT_LAUNCHER="$HOME/Desktop/run_cyber_skulls.sh"
cat > "$SCRIPT_LAUNCHER" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 -m streamlit run app.py
EOF
chmod +x "$SCRIPT_LAUNCHER"

echo
echo "==============================================="
echo "  INSTALLATION COMPLETE!"
echo "==============================================="
echo
echo "The CYBER SKULLS Repinning Tool has been installed to:"
echo "$INSTALL_DIR"
echo
echo "To run the application:"
echo "1. Double-click 'CYBER_SKULLS_REPINNING.desktop' on your desktop"
echo "2. Or double-click 'run_cyber_skulls.sh' on your desktop"
echo "3. Or run this command in Terminal:"
echo "   cd '$INSTALL_DIR' && python3 -m streamlit run app.py"
echo
echo "The app will open in your web browser at http://localhost:8501"
echo
echo "Press Enter to continue..."
read 
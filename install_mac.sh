#!/bin/bash

echo "==============================================="
echo "  CYBER SKULLS REPINNING TOOL INSTALLER"
echo "  macOS One-Click Installer"
echo "==============================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3 from https://python.org or using Homebrew:"
    echo "  brew install python"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} pip3 is not installed"
    echo "Please install pip3 or reinstall Python with pip included"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} pip3 found"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Git is not installed"
    echo "Please install Git:"
    echo "  - Install Xcode Command Line Tools: xcode-select --install"
    echo "  - Or install via Homebrew: brew install git"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Git found: $(git --version)"

# Set installation directory
INSTALL_DIR="$HOME/Desktop/CYBER_repinning"
echo
echo -e "${YELLOW}[INFO]${NC} Installing to: $INSTALL_DIR"

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

# Install Python requirements
echo -e "${YELLOW}[INFO]${NC} Installing Python dependencies..."
if ! pip3 install streamlit pandas requests base58 py-algorand-sdk multibase; then
    echo -e "${RED}[ERROR]${NC} Failed to install Python dependencies"
    echo "You may need to use 'sudo pip3 install' or create a virtual environment"
    exit 1
fi

# Create a launcher script
echo -e "${YELLOW}[INFO]${NC} Creating launcher script..."
LAUNCHER_PATH="$HOME/Desktop/CYBER_SKULLS_REPINNING.command"
cat > "$LAUNCHER_PATH" << 'EOF'
#!/bin/bash
cd "$HOME/Desktop/CYBER_repinning"
python3 -m streamlit run app.py
EOF

# Make launcher executable
chmod +x "$LAUNCHER_PATH"

echo
echo "==============================================="
echo "  INSTALLATION COMPLETE!"
echo "==============================================="
echo
echo "The CYBER SKULLS Repinning Tool has been installed to:"
echo "$INSTALL_DIR"
echo
echo "To run the application:"
echo "1. Double-click 'CYBER_SKULLS_REPINNING.command' on your desktop"
echo "2. Or run this command in Terminal:"
echo "   cd '$INSTALL_DIR' && python3 -m streamlit run app.py"
echo
echo "The app will open in your web browser at http://localhost:8501"
echo
echo "Press any key to continue..."
read -n 1 -s 
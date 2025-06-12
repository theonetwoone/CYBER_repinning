# 🚀 CYBER SKULLS Repinning Tool - One-Click Installation

This repository includes **one-click installers** for Windows, Mac, and Linux that automatically:
- ✅ Check for required dependencies (Python, Git)
- ✅ Clone the repository from GitHub
- ✅ Install all Python dependencies
- ✅ Create desktop shortcuts for easy access

---

## 🪟 **Windows Installation**

### **Requirements:**
- Windows 10/11
- Internet connection

### **Steps:**
1. **Download** `install_windows.bat` from this repository
2. **Right-click** → "Run as Administrator" (recommended)
3. **Follow** the prompts in the command window
4. **Launch** using the desktop shortcut: `CYBER_SKULLS_REPINNING.bat`

### **Manual Prerequisites (if needed):**
- [Python 3.8+](https://python.org) - Check "Add Python to PATH"
- [Git for Windows](https://git-scm.com/download/win)

---

## 🍎 **Mac Installation**

### **Requirements:**
- macOS 10.15+
- Internet connection

### **Steps:**
1. **Download** `install_mac.sh` from this repository
2. **Open Terminal** and navigate to the download folder
3. **Run:** `chmod +x install_mac.sh && ./install_mac.sh`
4. **Launch** using the desktop shortcut: `CYBER_SKULLS_REPINNING.command`

### **Manual Prerequisites (if needed):**
- [Python 3.8+](https://python.org)
- Git (install with: `xcode-select --install`)

---

## 🐧 **Linux Installation**

### **Requirements:**
- Linux distribution (Ubuntu, Debian, CentOS, Fedora, Arch)
- Internet connection

### **Steps:**
1. **Download** `install_linux.sh` from this repository
2. **Open Terminal** and navigate to the download folder
3. **Run:** `chmod +x install_linux.sh && ./install_linux.sh`
4. **Launch** using desktop shortcuts or: `./run_cyber_skulls.sh`

### **Manual Prerequisites (if needed):**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip git

# CentOS/RHEL/Fedora
sudo yum install python3 python3-pip git

# Arch Linux
sudo pacman -S python python-pip git
```

---

## 🔧 **Manual Installation (All Platforms)**

If the automatic installers don't work, you can install manually:

```bash
# 1. Clone the repository
git clone https://github.com/theonetwoone/CYBER_repinning.git
cd cyber_repinning

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run app.py
```

---

## 🌐 **Access the Application**

After installation, the app will be available at:
**http://localhost:8501**

The browser should open automatically, or you can manually navigate to this URL.

---

## 🆘 **Troubleshooting**

### **Common Issues:**

**Python not found:**
- Make sure Python is installed and added to your system PATH
- Try using `python3` instead of `python`

**Permission denied:**
- On Windows: Run as Administrator
- On Mac/Linux: Use `sudo` or install to user directory

**Git clone fails:**
- Check your internet connection
- Ensure Git is installed and accessible

**Dependencies fail to install:**
- Update pip: `python -m pip install --upgrade pip`
- Try user installation: `pip install --user -r requirements.txt`

### **Getting Help:**
- Check the GitHub Issues page
- Ensure you have the latest version of the installers
- Verify all prerequisites are met

---

## 📦 **What Gets Installed**

The installer will create:
- **Main folder:** `~/Desktop/CYBER_repinning/`
- **Desktop shortcuts** for easy launching
- **All Python dependencies** required to run the tool

---

## 🔄 **Updating**

To update to the latest version, simply run the installer again. It will:
1. Remove the old installation
2. Download the latest code
3. Update all dependencies
4. Recreate shortcuts

---

**Enjoy using the CYBER SKULLS Repinning Tool! 🚀** 
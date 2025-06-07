#!/usr/bin/env python3
"""
Gateway Tester UI Launcher with Auto-Install
============================================
"""

import subprocess
import sys
import os
import importlib.util

def install_package(package_name, pip_name=None):
    """Install a package using pip."""
    if pip_name is None:
        pip_name = package_name
    
    print(f"📦 Installing {package_name}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", pip_name, 
            "--quiet", "--disable-pip-version-check"
        ])
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def check_and_install_requirements():
    """Check if required packages are installed and install if missing."""
    # Essential packages (required)
    essential_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'),
        ('requests', 'requests'),
        ('algosdk', 'algorand-python-sdk'),
        ('base58', 'base58'),
        ('multibase', 'py-multibase')
    ]
    
    # Optional packages (nice to have)
    optional_packages = [
        ('plotly', 'plotly')
    ]
    
    print("🔍 Checking essential packages...")
    
    # Install essential packages
    for package_name, pip_name in essential_packages:
        try:
            importlib.util.find_spec(package_name)
            print(f"✅ {package_name} - already installed")
        except ImportError:
            if not install_package(package_name, pip_name):
                return False
    
    # Try to install optional packages
    print("\n🎨 Checking optional packages (for enhanced charts)...")
    for package_name, pip_name in optional_packages:
        try:
            importlib.util.find_spec(package_name)
            print(f"✅ {package_name} - already installed")
        except ImportError:
            print(f"📦 Installing optional package: {package_name}...")
            if install_package(package_name, pip_name):
                print(f"✅ {package_name} installed - you'll get fancy charts!")
            else:
                print(f"⚠️ {package_name} failed to install - using simple charts instead")
    
    print("\n✅ All essential packages are ready!")
    return True

def check_utils_file():
    """Check if utils.py exists."""
    if not os.path.exists('utils.py'):
        print("❌ utils.py not found!")
        print("💡 Make sure you're running this from the project directory.")
        print("💡 The utils.py file should contain the Algorand asset fetching functions.")
        return False
    
    print("✅ utils.py found")
    return True

def main():
    print("🚀 IPFS Gateway Risk Tester UI Launcher")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        print(f"💡 Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check if utils.py exists
    if not check_utils_file():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Check and install requirements
    if not check_and_install_requirements():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("\n🌐 Starting Gateway Risk Tester UI...")
    print("💡 The app will open in your default web browser")
    print("🔧 Close this window or press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Launch Streamlit app with cyber theme
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "gateway_tester_ui.py",
            "--theme.base", "dark",
            "--theme.primaryColor", "#00FF41",
            "--theme.backgroundColor", "#0E1117", 
            "--theme.secondaryBackgroundColor", "#1E1E1E",
            "--theme.textColor", "#FFFFFF",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Gateway Risk Tester UI has been closed.")
    except FileNotFoundError:
        print("❌ Streamlit not found. Installation may have failed.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 
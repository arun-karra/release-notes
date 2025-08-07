#!/usr/bin/env python3
"""
Setup script for Linear Release Notes Generator
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and create template if not"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env template...")
    env_template = """# Linear API Configuration
# Get your API key from: https://linear.app/settings/api
LINEAR_API_KEY=your_linear_api_key_here

# Your Linear workspace URL (optional)
LINEAR_WORKSPACE_URL=https://linear.app/your-workspace
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ .env template created")
        print("⚠️  Please edit .env file with your actual Linear API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['releases', '.streamlit']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory already exists: {directory}")

def main():
    """Main setup function"""
    print("🚀 Setting up Linear Release Notes Generator...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check/create .env file
    check_env_file()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Linear API key")
    print("2. Run 'streamlit run app.py' to start the web application")
    print("3. Open http://localhost:8501 in your browser")
    print("\n🤖 For automated updates:")
    print("1. Push this repository to GitHub")
    print("2. Add secrets in GitHub repository settings")
    print("3. Enable GitHub Actions")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
LeanAI Model MVP Startup Script
Run this script to start the LeanAI Model application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import streamlit
        import supabase
        import openai
        import numpy
        import PyPDF2
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  .env file not found")
        print("Please copy env_example.txt to .env and fill in your credentials")
        return False
    print("✅ .env file found")
    return True

def main():
    """Main startup function"""
    print("🤖 Starting LeanAI Model MVP...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        print("You can continue without .env, but you'll need to set environment variables manually")
    
    # Start the Streamlit app
    print("\n🚀 Launching Streamlit application...")
    print("The app will open in your default browser")
    print("Press Ctrl+C to stop the application")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "leanai_model.py",
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 LeanAI Model MVP stopped")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

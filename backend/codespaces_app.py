#!/usr/bin/env python3
"""
Codespaces-specific version of the Option Chain Analyzer
Optimized for cloud deployment
"""
import os
import sys
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_codespaces_environment():
    """Setup specific to GitHub Codespaces"""
    print("🚀 Setting up GitHub Codespaces environment...")
    
    # Get Codespaces environment variables
    codespace_name = os.getenv('CODESPACE_NAME', 'local')
    codespace_domain = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'localhost')
    
    print(f"📦 Codespace: {codespace_name}")
    print(f"🌐 Domain: {codespace_domain}")
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    return codespace_name, codespace_domain

def main():
    """Main function for Codespaces"""
    codespace_name, codespace_domain = setup_codespaces_environment()
    
    # Install dependencies
    print("📦 Checking dependencies...")
    try:
        import flask
        import pandas
        import requests
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return
    
    # Import after dependency check
    try:
        from app import app, fetch_and_process_data
        from config import Config
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # Initial data fetch
    print("📊 Fetching initial market data...")
    try:
        fetch_and_process_data()
        print("✅ Initial data fetched successfully")
    except Exception as e:
        print(f"⚠️ Initial data fetch failed: {e}")
        print("💡 This might be a network issue. Continuing...")
    
    # Calculate URLs
    local_url = f"http://localhost:5000"
    external_url = f"https://{codespace_name}-5000.{codespace_domain}"
    
    print("\n" + "="*60)
    print("🎉 Option Chain Analyzer is ready!")
    print("="*60)
    print(f"📊 Local URL: {local_url}")
    print(f"🌐 External URL: {external_url}")
    print(f"📱 Mobile Access: {external_url}")
    print("🔄 Auto-refresh: 30 seconds")
    print("⏹️  Stop: Ctrl+C")
    print("="*60)
    print("\n💡 The browser should open automatically. If not, use the URLs above.")
    
    try:
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Option Chain Analyzer...")
    except Exception as e:
        print(f"❌ Application error: {e}")

if __name__ == '__main__':
    main()

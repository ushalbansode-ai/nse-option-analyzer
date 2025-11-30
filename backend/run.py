#!/usr/bin/env python3
"""
Main entry point for Option Chain Analyzer
Run this file to start the application
"""
import os
import sys
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, fetch_and_process_data
from config import Config

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'logs/option_chain_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )

def create_directories():
    """Create necessary directories"""
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data/historical', exist_ok=True)
    os.makedirs('frontend', exist_ok=True)

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import flask
        import pandas
        import requests
        import plotly
        logging.info("All dependencies are available")
        return True
    except ImportError as e:
        logging.error(f"Missing dependency: {e}")
        logging.info("Please install requirements: pip install -r requirements.txt")
        return False

def main():
    """Main function to start the application"""
    print("🚀 Starting NSE Option Chain Analyzer...")
    
    # Setup
    create_directories()
    setup_logging()
    
    if not check_dependencies():
        sys.exit(1)
    
    # Initial data fetch
    print("📊 Fetching initial market data...")
    try:
        fetch_and_process_data()
        print("✅ Initial data fetched successfully")
    except Exception as e:
        print(f"❌ Initial data fetch failed: {e}")
        logging.error(f"Initial data fetch failed: {e}")
    
    # Start Flask application
    print(f"🌐 Starting web server on http://localhost:5000")
    print("📈 Dashboard available at: http://localhost:5000")
    print("🔄 Auto-refresh interval: 30 seconds")
    print("⏹️  Press Ctrl+C to stop the application")
    
    try:
        app.run(
            debug=False,  # Set to False in production
            host='0.0.0.0', 
            port=5000, 
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Option Chain Analyzer...")
    except Exception as e:
        print(f"❌ Application error: {e}")
        logging.error(f"Application error: {e}")

if __name__ == '__main__':
    main()

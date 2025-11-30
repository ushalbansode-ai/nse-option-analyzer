#!/bin/bash

# setup_codespaces.sh
# Run this script to set up Option Chain Analyzer in GitHub Codespaces

echo "==========================================="
echo "🚀 Option Chain Analyzer - Codespaces Setup"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in Codespaces
if [ -z "$CODESPACE_NAME" ]; then
    print_warning "Not running in GitHub Codespaces!"
    print_warning "This script is optimized for Codespaces environment."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_status "Checking system information..."
echo "➤ Python version: $(python3 --version 2>/dev/null || echo 'Not installed')"
echo "➤ Pip version: $(pip3 --version 2>/dev/null || echo 'Not installed')"
echo "➤ Codespace: $CODESPACE_NAME"

print_status "Updating package list..."
sudo apt-get update > /dev/null 2>&1

print_status "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv > /dev/null 2>&1

print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

print_status "Installing Python dependencies..."
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
    if [ $? -eq 0 ]; then
        print_success "All Python dependencies installed successfully"
    else
        print_error "Failed to install some dependencies"
        exit 1
    fi
else
    print_error "requirements.txt not found in backend directory"
    exit 1
fi

print_status "Setting up project structure..."
# Create necessary directories
mkdir -p logs
mkdir -p data/historical

print_status "Checking frontend files..."
if [ ! -f "frontend/index.html" ]; then
    print_warning "Frontend files not found. Creating basic structure..."
    mkdir -p frontend
    cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Option Chain Analyzer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <h1>Option Chain Analyzer</h1>
    <p>Frontend files will be generated automatically.</p>
</body>
</html>
EOF
fi

print_status "Testing NSE data access..."
python3 -c "
import requests
try:
    response = requests.get('https://www.nseindia.com', timeout=10)
    print('✅ NSE website is accessible')
except:
    print('⚠️  Cannot reach NSE website - check network connection')
"

print_status "Setting file permissions..."
chmod +x backend/run.py
chmod +x backend/codespaces_app.py

print_status "Setup complete!"

# Display access information
echo ""
echo "==========================================="
echo "🎉 Setup Completed Successfully!"
echo "==========================================="
echo ""
echo "📊 Your Option Chain Analyzer is ready!"
echo ""
if [ -n "$CODESPACE_NAME" ]; then
    EXTERNAL_URL="https://${CODESPACE_NAME}-5000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
    echo "🌐 Access your dashboard at:"
    echo "   ${EXTERNAL_URL}"
    echo ""
    echo "📱 Mobile/Tablet access:"
    echo "   Same URL on any device: ${EXTERNAL_URL}"
else
    echo "🌐 Access your dashboard at:"
    echo "   http://localhost:5000"
fi
echo ""
echo "🚀 Starting the application..."
echo "   To start manually: cd backend && python codespaces_app.py"
echo ""
echo "⏹️  To stop: Press Ctrl+C in the terminal"
echo "==========================================="

# Start the application
print_status "Starting Option Chain Analyzer..."
cd backend
python codespaces_app.py

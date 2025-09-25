#!/bin/bash

# Local setup script for Grocery Price Scraper
# Creates virtual environment, installs dependencies, and sets up Playwright browsers

set -e  # Exit on any error

echo "🛒 Setting up Grocery Price Scraper..."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is compatible (>= 3.11)"
else
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    echo "📁 Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create data directories
echo "📂 Creating data directories..."
mkdir -p data/reports
mkdir -p data/logs

# Set up logging directory
mkdir -p logs

# Create sample .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating sample .env file..."
    cat > .env << EOF
# Environment configuration for Grocery Price Scraper

# Database
DATABASE_PATH=data/grocery_prices.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log

# Scraping settings
MAX_CONCURRENT_REQUESTS=3
DEFAULT_RATE_LIMIT=1.0

# Report settings  
REPORT_DIR=data/reports
EXCEL_AUTHOR=Farm2bag

# Optional: Proxy settings (uncomment if needed)
# USE_PROXY=false
# PROXY_URL=http://proxy.example.com:8080

# Optional: Notification settings (uncomment if needed)
# SLACK_WEBHOOK_URL=
# EMAIL_SMTP_SERVER=
# EMAIL_FROM=
# EMAIL_TO=
EOF
    echo "✅ Sample .env file created. Edit it with your settings."
else
    echo "📝 .env file already exists"
fi

# Run a quick test
echo "🧪 Running quick test..."
if python -c "import requests, playwright, beautifulsoup4, pandas, openpyxl, yaml, rapidfuzz, pytest; print('✅ All imports successful')"; then
    echo "✅ All dependencies installed correctly"
else
    echo "❌ Some dependencies failed to import"
    exit 1
fi

# Test database creation
echo "🗄️  Testing database setup..."
python -c "
from db import Database
db = Database('data/test.db')
stats = db.get_statistics()
print('✅ Database setup successful')
import os
os.remove('data/test.db')
"

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x tooling/*.sh

# Print completion message
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Edit config files in config/ directory if needed"
echo "   3. Run the scraper: python runner.py"
echo ""
echo "📚 Usage examples:"
echo "   python runner.py --categories vegetables fruits"
echo "   python runner.py --sites bigbasket jiomart"
echo "   python runner.py --stats  # Show database statistics"
echo "   python runner.py --cleanup 30  # Clean data older than 30 days"
echo ""
echo "📁 Important directories:"
echo "   • config/          - Configuration files"
echo "   • data/reports/    - Generated Excel reports"
echo "   • data/            - Database and data files"
echo "   • logs/            - Log files"
echo ""
echo "⚠️  Don't forget to:"
echo "   • Edit config/sites.yml for scraper settings"
echo "   • Edit config/compare_rules.yml for normalization rules"
echo "   • Check .env file for environment settings"
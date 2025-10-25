#!/bin/bash
# ABOUTME: Setup script for funding data scraper
# ABOUTME: Installs Playwright dependencies and prepares environment

set -e

echo "🚀 Setting up Funding Data Scraper"
echo "=================================="

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -q playwright psycopg2-binary

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright browsers (this may take a few minutes)..."
python -m playwright install chromium

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the scraper:"
echo "  1. Set credentials (optional but recommended):"
echo "     export CRYPTORANK_EMAIL='your_email@example.com'"
echo "     export CRYPTORANK_PASSWORD='your_password'"
echo ""
echo "  2. Run one-time sync:"
echo "     python scripts/market_intelligence/continuous_funding_sync.py --pages 5"
echo ""
echo "  3. Or scrape specific company:"
echo "     python scripts/market_intelligence/continuous_funding_sync.py --company echodotxyz"
echo ""
echo "  4. For continuous mode (runs daily):"
echo "     python scripts/market_intelligence/continuous_funding_sync.py --continuous --pages 10"
echo ""


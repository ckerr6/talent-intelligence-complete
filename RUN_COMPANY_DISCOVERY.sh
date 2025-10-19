#!/bin/bash
# Quick setup and run company discovery prep

cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"

# Make executable
chmod +x prep_company_discovery.py
chmod +x batch_discover_companies.sh

echo "🏢 Company Discovery - Quick Start"
echo "======================================"
echo ""
echo "Step 1: Analyze companies and create discovery queue"
echo "  python3 prep_company_discovery.py"
echo ""
echo "Step 2: Run batch discovery"
echo "  chmod +x batch_discover_companies.sh"
echo "  ./batch_discover_companies.sh"
echo ""
echo "======================================"
echo ""
echo "Ready to run Step 1?"
read -p "Press ENTER to analyze companies now..."

python3 prep_company_discovery.py

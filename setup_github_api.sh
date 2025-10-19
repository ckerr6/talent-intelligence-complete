#!/bin/bash
# ABOUTME: Quick setup script for GitHub API enrichment
# ABOUTME: Gets you ready to enrich GitHub data in 2 minutes

set -e

echo "🚀 GitHub API Enrichment - Quick Setup"
echo "======================================"
echo ""

# Check if database exists
if [ ! -f "talent_intelligence.db" ]; then
    echo "❌ Database not found: talent_intelligence.db"
    echo "   Make sure you're in the FINAL_DATABASE directory"
    exit 1
fi

echo "✅ Database found"
echo ""

# Check if Python script exists
if [ ! -f "github_api_enrichment.py" ]; then
    echo "❌ Script not found: github_api_enrichment.py"
    exit 1
fi

chmod +x github_api_enrichment.py
echo "✅ Script permissions set"
echo ""

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set"
    echo ""
    echo "To get maximum rate limits (5000/hour instead of 60/hour):"
    echo ""
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scopes:"
    echo "   - public_repo"
    echo "   - read:user"
    echo "   - read:org"
    echo "4. Copy the token"
    echo "5. Run: export GITHUB_TOKEN='your_token_here'"
    echo ""
    read -p "Press ENTER to continue without token (60 requests/hour limit)..."
    echo ""
else
    echo "✅ GitHub token found"
    echo ""
fi

# Check Python requests library
echo "Checking dependencies..."
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing requests library..."
    pip3 install requests
fi
echo "✅ Dependencies ready"
echo ""

echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "What do you want to do?"
echo ""
echo "1. Enrich existing 12,815 GitHub profiles"
echo "   └─ Updates follower counts, repos, company info"
echo "   └─ Time: ~3-4 hours with token, much longer without"
echo ""
echo "2. Discover a company's GitHub repos + contributors"
echo "   └─ Example: Uniswap, Coinbase, etc."
echo "   └─ Gets all repos and all contributors"
echo "   └─ Time: 10-30 minutes per company"
echo ""
echo "3. Enrich a specific user"
echo "   └─ Get complete profile for one person"
echo "   └─ Time: ~1 second"
echo ""
echo "Commands:"
echo ""
echo "# Option 1: Enrich all existing profiles"
echo "python3 github_api_enrichment.py enrich-existing talent_intelligence.db"
echo ""
echo "# Option 2: Discover company"
echo "python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs \"Uniswap\""
echo ""
echo "# Option 3: Enrich specific user"
echo "python3 github_api_enrichment.py enrich-user talent_intelligence.db haydenadams"
echo ""
echo "======================================"
echo ""
echo "Recommended: Start with Option 1 (enrich existing profiles)"
echo "This will update all 12,815 profiles with current data from GitHub API"
echo ""

read -p "Start Option 1 now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting enrichment of existing profiles..."
    echo ""
    python3 github_api_enrichment.py enrich-existing talent_intelligence.db
fi

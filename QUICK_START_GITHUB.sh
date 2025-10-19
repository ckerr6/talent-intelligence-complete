#!/bin/bash
# Quick command reference for GitHub enrichment

cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"

# Make scripts executable
chmod +x github_api_enrichment.py
chmod +x setup_github_api.sh

echo "🚀 GitHub API Enrichment - Quick Start"
echo ""
echo "Step 1: Get your GitHub token"
echo "  Go to: https://github.com/settings/tokens"
echo "  Create token with: public_repo, read:user, read:org"
echo ""
echo "Step 2: Set your token"
echo "  export GITHUB_TOKEN='your_token_here'"
echo ""
echo "Step 3: Choose what to do:"
echo ""
echo "Option A: Enrich existing 12,815 profiles (~3-4 hours)"
echo "  ./github_api_enrichment.py enrich-existing talent_intelligence.db"
echo ""
echo "Option B: Discover a company (~10-30 min per company)"
echo "  ./github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs 'Uniswap'"
echo ""
echo "Option C: Enrich one specific user (~1 second)"
echo "  ./github_api_enrichment.py enrich-user talent_intelligence.db haydenadams"
echo ""
echo "---"
echo ""
echo "Recommended: Start with Option A overnight, then do Option B for key companies"

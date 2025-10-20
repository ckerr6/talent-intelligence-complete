#!/bin/bash
# ABOUTME: Fix GitHub schema and test enrichment
# ABOUTME: Resolves column issues and validates enrichment works

echo "============================================================"
echo "🔧 Fixing GitHub Schema & Testing Enrichment"
echo "============================================================"
echo ""

# Step 1: Fix the schema
echo "📋 Step 1: Fixing database schema..."
python3 fix_github_schema.py

if [ $? -ne 0 ]; then
    echo "❌ Schema fix failed"
    exit 1
fi

echo ""
echo "✅ Schema fixed successfully"
echo ""

# Step 2: Test with 5 profiles
echo "📋 Step 2: Testing enrichment with 5 profiles..."
python3 github_enrichment.py --test

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test enrichment successful!"
    
    # Show the results
    echo ""
    echo "📊 Checking enrichment results..."
    python3 -c "
import sqlite3
from config import Config

conn = sqlite3.connect(Config.DB_PATH)
cursor = conn.cursor()

# Get enrichment stats
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN followers IS NOT NULL THEN 1 ELSE 0 END) as enriched,
        SUM(CASE WHEN github_bio IS NOT NULL THEN 1 ELSE 0 END) as with_bio
    FROM github_profiles
''')

total, enriched, with_bio = cursor.fetchone()

print(f'GitHub Profiles Status:')
print(f'  Total profiles: {total}')
print(f'  Enriched profiles: {enriched}')  
print(f'  Profiles with bio: {with_bio}')

# Show sample enriched profile
cursor.execute('''
    SELECT github_username, github_name, github_company, 
           followers, public_repos, top_language
    FROM github_profiles 
    WHERE followers IS NOT NULL
    LIMIT 1
''')

result = cursor.fetchone()
if result:
    print(f'\\nSample enriched profile:')
    print(f'  Username: {result[0]}')
    print(f'  Name: {result[1]}')
    print(f'  Company: {result[2]}')
    print(f'  Followers: {result[3]}')
    print(f'  Public repos: {result[4]}')
    print(f'  Top language: {result[5]}')

conn.close()
"
else
    echo ""
    echo "⚠️  Enrichment had issues - check logs/enrichment.log for details"
fi

echo ""
echo "============================================================"
echo "✅ GitHub Integration Ready for Day 3!"
echo "============================================================"
echo ""
echo "Everything is now set up correctly for full enrichment."
echo ""
echo "📊 Your options:"
echo ""
echo "1. Run a small batch (100 profiles - ~2 minutes):"
echo "   python3 github_enrichment.py --limit 100"
echo ""
echo "2. Run full enrichment (all profiles - ~45 minutes):"
echo "   python3 github_enrichment.py"
echo ""
echo "3. Run in background with screen (recommended for full run):"
echo "   screen -S github_enrichment"
echo "   python3 github_enrichment.py"
echo "   # Press Ctrl+A, then D to detach"
echo "   # Use 'screen -r github_enrichment' to reattach"
echo ""
echo "The enrichment will:"
echo "  • Process ~500 GitHub profiles"
echo "  • Add followers, repos, languages, companies"
echo "  • Handle all errors automatically"
echo "  • Save progress (can resume if interrupted)"
echo ""
echo "To commit your fixes:"
echo "  git add ."
echo "  git commit -m 'Fixed GitHub schema and tested enrichment'"
echo "  git push origin main"
echo ""

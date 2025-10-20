#!/bin/bash
# ABOUTME: Complete GitHub enrichment and matching workflow
# ABOUTME: Enriches all profiles, then matches them to people

echo "============================================================"
echo "🚀 GitHub Complete Enrichment & Matching Workflow"
echo "============================================================"
echo ""

# Step 1: Check current status
echo "📊 Step 1: Analyzing GitHub profiles..."
python3 github_queue_manager.py

echo ""
echo "============================================================"
echo ""

# Ask if user wants to run enrichment
echo "Do you want to run enrichment now? (y/n)"
read -r run_enrichment

if [ "$run_enrichment" = "y" ] || [ "$run_enrichment" = "Y" ]; then
    echo ""
    echo "How many profiles to enrich?"
    echo "  1. Test batch (100 profiles)"
    echo "  2. Medium batch (1000 profiles)"  
    echo "  3. All profiles"
    echo ""
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            echo "Running test batch of 100..."
            python3 github_enrichment.py --limit 100
            ;;
        2)
            echo "Running medium batch of 1000..."
            python3 github_enrichment.py --limit 1000
            ;;
        3)
            echo "Running all profiles..."
            echo "This may take several hours. Consider using screen:"
            echo "  screen -S github_enrichment"
            echo "  python3 github_enrichment.py"
            echo ""
            echo "Continue without screen? (y/n)"
            read -r continue_all
            if [ "$continue_all" = "y" ]; then
                python3 github_enrichment.py
            fi
            ;;
        *)
            echo "Invalid choice"
            ;;
    esac
    
    echo ""
    echo "============================================================"
    echo ""
    echo "✅ Enrichment complete. Running matching..."
    echo ""
    
    # Re-run matching after enrichment
    python3 github_queue_manager.py
fi

echo ""
echo "============================================================"
echo "📊 FINAL STATUS"
echo "============================================================"
echo ""

# Show final stats
python3 -c "
import sqlite3
from config import Config

conn = sqlite3.connect(Config.DB_PATH)
cursor = conn.cursor()

# Overall stats
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN person_id IS NOT NULL THEN 1 ELSE 0 END) as linked,
        SUM(CASE WHEN followers IS NOT NULL THEN 1 ELSE 0 END) as enriched,
        SUM(CASE WHEN github_email IS NOT NULL THEN 1 ELSE 0 END) as with_email,
        SUM(CASE WHEN github_company IS NOT NULL THEN 1 ELSE 0 END) as with_company
    FROM github_profiles
''')

total, linked, enriched, with_email, with_company = cursor.fetchone()

print(f'GitHub Profile Statistics:')
print(f'  Total profiles:       {total:,}')
print(f'  Enriched:            {enriched:,} ({enriched/total*100:.1f}%)')
print(f'  Linked to people:    {linked:,} ({linked/total*100:.1f}%)')
print(f'  Has email:           {with_email:,} ({with_email/total*100:.1f}%)')
print(f'  Has company:         {with_company:,} ({with_company/total*100:.1f}%)')

# Top unmatched profiles
print(f'\\nTop unmatched profiles by followers:')
cursor.execute('''
    SELECT github_username, github_name, followers, github_company
    FROM github_profiles
    WHERE person_id IS NULL
    AND followers IS NOT NULL
    ORDER BY followers DESC
    LIMIT 5
''')

for username, name, followers, company in cursor.fetchall():
    print(f'  @{username}: {name} ({followers:,} followers) - {company or \"No company\"}')

conn.close()
"

echo ""
echo "============================================================"
echo "✅ Workflow Complete!"
echo "============================================================"
echo ""
echo "📝 Notes:"
echo "  • Enriched profiles now have emails, names, companies for matching"
echo "  • Matched profiles are linked to people in database"
echo "  • Unmatched profiles saved for future matching"
echo "  • Re-run after importing new people to match more"
echo ""

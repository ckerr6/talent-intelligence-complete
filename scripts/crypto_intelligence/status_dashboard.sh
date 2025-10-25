#!/bin/bash
# ABOUTME: Real-time status dashboard for Ethereum ecosystem intelligence gathering

echo "================================================================================"
echo "🌍 ETHEREUM ECOSYSTEM INTELLIGENCE - REAL-TIME STATUS"
echo "================================================================================"
echo ""

# Running processes
echo "📊 ACTIVE PROCESSES:"
echo "--------------------------------------------------------------------------------"
ps aux | grep -E "(discover_all_contributors|enrich_crypto_developers)" | grep -v grep | awk '{printf "   ✅ PID %-7s CPU: %3s%%  Mem: %6s  %s\n", $2, $3, $6/1024"MB", $NF}'
echo ""

# Database stats
echo "💾 DATABASE STATISTICS:"
echo "--------------------------------------------------------------------------------"
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Crypto developers
psql -d talent -t -c "SELECT '   Total Crypto Developers: ' || COUNT(*)::text FROM crypto_developers;" 2>/dev/null

# Enriched
psql -d talent -t -c "SELECT '   Enriched: ' || COUNT(DISTINCT cd.github_profile_id)::text FROM crypto_developers cd JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id;" 2>/dev/null

# Pending
psql -d talent -t -c "SELECT '   Pending Enrichment: ' || (COUNT(*) - COUNT(CASE WHEN gi.github_profile_id IS NOT NULL THEN 1 END))::text FROM crypto_developers cd LEFT JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id;" 2>/dev/null

# Total repos
psql -d talent -t -c "SELECT '   Ethereum Repos: ' || COUNT(*)::text || ' repos' FROM crypto_ecosystem_repos WHERE ecosystem_id IN (SELECT ecosystem_id FROM crypto_ecosystems WHERE ecosystem_name = 'Ethereum');" 2>/dev/null

echo ""

# Discovery progress (from latest backup)
echo "🔍 DISCOVERY PROGRESS:"
echo "--------------------------------------------------------------------------------"
LATEST_BACKUP=$(ls -t /tmp/ethereum_contributors_backup_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    python3 << EOF
import json
try:
    with open('$LATEST_BACKUP') as f:
        data = json.load(f)
        print(f"   Contributors Discovered: {len(data['contributors']):,}")
        print(f"   Repos Processed: {data['processed']:,} / 166,881")
        print(f"   Progress: {data['processed']/166881*100:.2f}%")
        print(f"   Repos Skipped: {data['skipped']:,}")
except:
    print("   No backup data available")
EOF
else
    echo "   No backup files found yet"
fi

echo ""

# Enrichment stats
echo "⚡ ENRICHMENT STATISTICS:"
echo "--------------------------------------------------------------------------------"
psql -d talent -t -c "SELECT '   Total Enriched (All): ' || COUNT(*)::text FROM github_intelligence;" 2>/dev/null

psql -d talent -t -c "
SELECT '   ' || inferred_seniority || ': ' || COUNT(*)::text 
FROM github_intelligence 
WHERE inferred_seniority IS NOT NULL 
GROUP BY inferred_seniority 
ORDER BY COUNT(*) DESC 
LIMIT 5;" 2>/dev/null

echo ""

# Top contributors
echo "🏆 TOP 10 ETHEREUM CONTRIBUTORS (BY CONTRIBUTIONS):"
echo "--------------------------------------------------------------------------------"
psql -d talent -t -c "
SELECT '   ' || ROW_NUMBER() OVER (ORDER BY cd.contribution_count DESC) || '. @' || 
       gp.github_username || ' - ' || cd.contribution_count::text || ' contributions' ||
       CASE WHEN gi.github_profile_id IS NOT NULL THEN ' ✅ ENRICHED' ELSE '' END
FROM crypto_developers cd
JOIN github_profile gp ON cd.github_profile_id = gp.github_profile_id
LEFT JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id
WHERE cd.ecosystem_id IN (SELECT ecosystem_id FROM crypto_ecosystems WHERE ecosystem_name = 'Ethereum')
ORDER BY cd.contribution_count DESC
LIMIT 10;" 2>/dev/null

echo ""
echo "================================================================================"
echo "🔄 Refreshing in real-time... Press Ctrl+C to stop"
echo "================================================================================"


#!/bin/bash
# Morning Summary: Check Overnight Discovery Results

echo "=========================================="
echo "🌅 OVERNIGHT DISCOVERY RESULTS"
echo "=========================================="
echo ""

# Check if process is still running
if [ -f logs/discovery_pid.txt ]; then
    PID=$(cat logs/discovery_pid.txt)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⏳ Discovery still running (PID: $PID)"
        echo ""
    else
        echo "✅ Discovery completed!"
        echo ""
    fi
fi

# Show latest log file
echo "📋 Latest Log Output:"
echo "=========================================="
LATEST_LOG=$(ls -t logs/overnight_discovery_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    tail -30 "$LATEST_LOG"
    echo ""
    echo "Full log: $LATEST_LOG"
else
    echo "No log files found"
fi
echo ""
echo ""

# Database statistics
echo "📊 DATABASE STATISTICS:"
echo "=========================================="

psql -d talent << 'SQL'
-- Discovery Stats
SELECT 
    '🎯 Total Discovery Events' as metric,
    COUNT(*)::text as value
FROM entity_discovery
UNION ALL
SELECT 
    '👥 New Developers Discovered',
    COUNT(DISTINCT entity_id)::text
FROM entity_discovery
WHERE entity_type = 'person'
  AND discovered_at >= NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
    '📦 Repos Processed',
    COUNT(DISTINCT repo_id)::text
FROM github_repository
WHERE last_contributor_sync IS NOT NULL
UNION ALL
SELECT
    '✨ Total Enriched Profiles',
    COUNT(*)::text
FROM github_profile
WHERE last_enriched IS NOT NULL;

-- Ecosystem Breakdown
\echo ''
\echo '🌍 DEVELOPERS BY ECOSYSTEM:'
SELECT 
    UNNEST(ecosystem_tags) as ecosystem,
    COUNT(*) as developer_count
FROM github_profile
WHERE array_length(ecosystem_tags, 1) > 0
GROUP BY ecosystem
ORDER BY developer_count DESC
LIMIT 10;

-- Top New Discoveries
\echo ''
\echo '⭐ TOP NEW DEVELOPERS (Last 24h):'
SELECT 
    gp.github_username,
    gp.github_name,
    gp.ecosystem_tags,
    gp.followers,
    gp.total_merged_prs,
    ed.discovered_at::date as discovered
FROM github_profile gp
JOIN entity_discovery ed ON gp.github_profile_id = ed.entity_id
WHERE ed.entity_type = 'person'
  AND ed.discovered_at >= NOW() - INTERVAL '24 hours'
ORDER BY gp.importance_score DESC NULLS LAST
LIMIT 20;

-- Repos synced
\echo ''
\echo '📦 REPOS WITH CONTRIBUTORS SYNCED:'
SELECT 
    r.full_name,
    r.contributor_count,
    r.stars,
    r.last_contributor_sync::date as last_sync
FROM github_repository r
WHERE r.last_contributor_sync IS NOT NULL
ORDER BY r.last_contributor_sync DESC
LIMIT 10;
SQL

echo ""
echo "=========================================="
echo "✅ Summary Complete!"
echo "=========================================="
echo ""
echo "To see more details, run:"
echo "  psql -d talent -c 'SELECT * FROM v_discovery_stats;'"
echo "  psql -d talent -c 'SELECT * FROM v_top_developers LIMIT 50;'"
echo ""


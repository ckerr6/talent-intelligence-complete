#!/bin/bash
# Quick script to check GitHub PR enrichment progress

echo "=========================================="
echo "📊 GitHub PR Enrichment Progress"
echo "=========================================="
echo ""

# Check if process is running
if ps aux | grep "07_github_pr_enrichment.py" | grep -v grep > /dev/null; then
    echo "✅ Status: RUNNING"
else
    echo "⏹️  Status: STOPPED/COMPLETED"
fi

echo ""

# Get database stats
psql -d talent << 'EOF'
SELECT 
    COUNT(*) as total_profiles,
    COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END) as enriched,
    COUNT(CASE WHEN enriched_at IS NULL THEN 1 END) as remaining,
    ROUND(100.0 * COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END) / COUNT(*), 2) as pct_complete
FROM github_profile;

-- Top 10 contributors by merged PRs
SELECT 
    '--- Top 10 by Merged PRs ---' as header;

SELECT 
    p.full_name,
    gp.github_username,
    gp.total_merged_prs,
    gp.total_lines_contributed,
    gp.enriched_at::date as enriched_date
FROM github_profile gp
JOIN person p ON gp.person_id = p.person_id
WHERE gp.total_merged_prs > 0
ORDER BY gp.total_merged_prs DESC
LIMIT 10;
EOF

echo ""
echo "=========================================="
echo "📋 Recent Log Entries (last 15 lines):"
echo "=========================================="
tail -15 logs/pr_enrichment_*.log 2>/dev/null || echo "No log file found"

echo ""
echo "=========================================="
echo "To monitor in real-time:"
echo "  tail -f logs/pr_enrichment_*.log"
echo "=========================================="


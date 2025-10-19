#!/bin/bash
# ABOUTME: One-command script to build GitHub enrichment (Phase 3)
# ABOUTME: Run this AFTER Phase 1 and 2 are complete

echo "============================================================"
echo "🐙 Phase 3: GitHub Enrichment Builder"
echo "============================================================"
echo ""

DB_PATH="./talent_intelligence.db"
GITHUB_CSV="./GitHub_Contributors-Default-view-export-1760735472022.csv"

# Check if Phase 1 & 2 database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Phase 1 & 2 database not found!"
    echo "Run ./RUN_ME.sh and ./RUN_PHASE2.sh first"
    exit 1
fi

echo "✓ Phase 1 & 2 database found"

# Check if GitHub CSV exists
if [ ! -f "$GITHUB_CSV" ]; then
    echo "❌ GitHub CSV not found at: $GITHUB_CSV"
    echo "Please check the file location"
    exit 1
fi

echo "✓ GitHub CSV found ($(wc -l < "$GITHUB_CSV" | tr -d ' ') rows)"
echo ""
echo "📦 Processing GitHub enrichment data..."
echo "   This will take 2-5 minutes for ~48k profiles"
echo ""

python3 build_github_enrichment.py "$DB_PATH" "$GITHUB_CSV"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ SUCCESS! GitHub enrichment complete"
    echo "============================================================"
    echo ""
    echo "View enrichment report:"
    echo "  cat github_enrichment_report.txt"
    echo ""
    echo "Review matches needing manual verification:"
    echo "  ./review_github_matches.sh"
    echo ""
    echo "Query GitHub data:"
    echo "  sqlite3 talent_intelligence.db"
    echo "  SELECT COUNT(*) FROM github_profiles;"
    echo "  SELECT * FROM people WHERE status='github_sourced' LIMIT 10;"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "❌ Build failed - check github_enrichment_log.txt for details"
    echo "============================================================"
    echo ""
    exit 1
fi

#!/bin/bash
# ABOUTME: One-command script to build the company database (Phase 2)
# ABOUTME: Run this AFTER Phase 1 is complete

echo "============================================================"
echo "🏢 Phase 2: Company Database Builder"
echo "============================================================"
echo ""

DB_PATH="./talent_intelligence.db"
SOURCE_DIR="/Users/charlie.kerr/Documents/CK Docs"

# Check if Phase 1 database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Phase 1 database not found!"
    echo "Run ./RUN_ME.sh first to build the candidate database"
    exit 1
fi

echo "✓ Phase 1 database found"
echo ""
echo "📦 Building company database..."
echo ""

python3 build_company_database.py "$DB_PATH" "$SOURCE_DIR"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ SUCCESS! Company database built successfully"
    echo "============================================================"
    echo ""
    echo "View company report:"
    echo "  cat company_quality_report.txt"
    echo ""
    echo "Query companies:"
    echo "  sqlite3 talent_intelligence.db"
    echo "  SELECT COUNT(*) FROM companies;"
    echo "  SELECT * FROM companies LIMIT 10;"
    echo ""
    echo "Query companies with candidates:"
    echo "  ./query_database.sh"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "❌ Build failed - check company_import_log.txt for details"
    echo "============================================================"
    echo ""
    exit 1
fi

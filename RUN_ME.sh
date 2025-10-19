#!/bin/bash
# ABOUTME: One-command script to build the candidate database
# ABOUTME: Handles all setup, execution, and validation automatically

echo "============================================================"
echo "🚀 Talent Intelligence Database Builder"
echo "============================================================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    echo "Install it with: brew install python3"
    exit 1
fi

echo "✓ Python 3 found"

# Check/install required packages
echo ""
echo "📦 Checking dependencies..."

python3 -c "import pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing pandas..."
    pip3 install pandas
fi

python3 -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing numpy..."
    pip3 install numpy
fi

echo "✓ All dependencies installed"

# Run the database builder
echo ""
echo "============================================================"
echo "🔨 Building Database..."
echo "============================================================"
echo ""

python3 build_candidate_database.py "/Users/charlie.kerr/Documents/CK Docs"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ SUCCESS! Database built successfully"
    echo "============================================================"
    echo ""
    echo "Your database is ready at:"
    echo "  ./talent_intelligence.db"
    echo ""
    echo "View reports:"
    echo "  cat data_quality_report.txt"
    echo "  cat deduplication_report.txt"
    echo ""
    echo "Query the database:"
    echo "  sqlite3 talent_intelligence.db"
    echo "  .schema"
    echo "  SELECT COUNT(*) FROM people;"
    echo ""
    echo "Or view sample queries:"
    echo "  cat sample_queries.sql"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "❌ Build failed - check import_log.txt for details"
    echo "============================================================"
    echo ""
    exit 1
fi

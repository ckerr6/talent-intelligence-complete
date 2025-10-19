#!/bin/bash
# ABOUTME: Batch discover multiple companies
# ABOUTME: Reads from companies_to_discover.csv and processes them

set -e

DB_PATH="talent_intelligence.db"
CSV_PATH="companies_to_discover.csv"
LOG_PATH="batch_discovery_log.txt"

echo "🚀 Batch Company Discovery"
echo "======================================"
echo ""

# Check if CSV exists
if [ ! -f "$CSV_PATH" ]; then
    echo "❌ Discovery queue not found: $CSV_PATH"
    echo "Run this first: python3 prep_company_discovery.py"
    exit 1
fi

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    exit 1
fi

# Check if token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  Warning: GITHUB_TOKEN not set"
    echo "Set it with: export GITHUB_TOKEN='your_token'"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Ask how many companies to process
echo "How many companies do you want to discover?"
echo "(Estimate: 10-30 minutes per company)"
echo ""
read -p "Number of companies: " NUM_COMPANIES

if [ -z "$NUM_COMPANIES" ] || [ "$NUM_COMPANIES" -lt 1 ]; then
    echo "Invalid number"
    exit 1
fi

echo ""
echo "📋 Processing $NUM_COMPANIES companies..."
echo "Starting at: $(date)"
echo ""

# Initialize log
echo "=====================================" > "$LOG_PATH"
echo "Batch Discovery Started: $(date)" >> "$LOG_PATH"
echo "=====================================" >> "$LOG_PATH"
echo "" >> "$LOG_PATH"

# Read CSV and process companies
# Skip header, take first NUM_COMPANIES rows
PROCESSED=0
SUCCESSFUL=0
FAILED=0

tail -n +2 "$CSV_PATH" | head -n "$NUM_COMPANIES" | while IFS=',' read -r company_id name github_org employees priority website; do
    PROCESSED=$((PROCESSED + 1))
    
    # Remove quotes from name
    name=$(echo "$name" | sed 's/"//g')
    
    echo "[$PROCESSED/$NUM_COMPANIES] Discovering: $name ($github_org)"
    echo "  Employees in DB: $employees"
    echo ""
    
    # Log to file
    echo "[$PROCESSED/$NUM_COMPANIES] $name ($github_org)" >> "$LOG_PATH"
    echo "Started: $(date)" >> "$LOG_PATH"
    
    # Run discovery
    if python3 github_api_enrichment.py discover-company "$DB_PATH" "$github_org" "$name" >> "$LOG_PATH" 2>&1; then
        echo "  ✅ Success!"
        SUCCESSFUL=$((SUCCESSFUL + 1))
        echo "Status: SUCCESS" >> "$LOG_PATH"
    else
        echo "  ❌ Failed - check log for details"
        FAILED=$((FAILED + 1))
        echo "Status: FAILED" >> "$LOG_PATH"
    fi
    
    echo "Finished: $(date)" >> "$LOG_PATH"
    echo "-------------------------------------" >> "$LOG_PATH"
    echo ""
done

echo ""
echo "======================================"
echo "✅ BATCH DISCOVERY COMPLETE"
echo "======================================"
echo "Finished at: $(date)"
echo ""
echo "Summary:"
echo "  Processed:  $PROCESSED companies"
echo "  Successful: $SUCCESSFUL"
echo "  Failed:     $FAILED"
echo ""
echo "Detailed log: $LOG_PATH"
echo ""
echo "Next steps:"
echo "1. Query database to see new data"
echo "2. Run prep_company_discovery.py again for next batch"
echo "3. Check failed companies in log"

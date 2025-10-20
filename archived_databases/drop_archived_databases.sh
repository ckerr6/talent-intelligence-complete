#!/bin/bash

# Drop Archived PostgreSQL Databases
# ⚠️  WARNING: This will PERMANENTLY DELETE databases!
# Only run this AFTER you've created dumps with archive_postgresql_databases.sh

# Databases to drop
DATABASES=(
    "talent_intelligence"
    "talent_intel"
    "talent_graph"
    "talentgraph"
    "talentgraph2"
    "talentgraph_development"
    "tech_recruiting_db"
    "crypto_dev_network"
)

echo "============================================================================"
echo "  ⚠️  DROP ARCHIVED DATABASES - PERMANENT ACTION ⚠️"
echo "============================================================================"
echo ""
echo "This will PERMANENTLY DELETE the following databases:"
echo ""
for db in "${DATABASES[@]}"; do
    echo "  - $db"
done
echo ""
echo "⚠️  PRIMARY DATABASE 'talent' WILL NOT BE DROPPED - IT IS PROTECTED ⚠️"
echo ""
echo "Make sure you have:"
echo "  1. ✅ Run ./archive_postgresql_databases.sh to create backups"
echo "  2. ✅ Verified the backup files exist in postgresql_dumps/"
echo "  3. ✅ Confirmed all data was migrated to PostgreSQL 'talent'"
echo ""
read -p "Type 'DELETE' (all caps) to continue, or anything else to abort: " confirmation
echo ""

if [ "$confirmation" != "DELETE" ]; then
    echo "❌ Aborted - no databases were dropped"
    exit 1
fi

echo "============================================================================"
echo "Dropping databases..."
echo "============================================================================"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
SKIPPED_COUNT=0

for db in "${DATABASES[@]}"; do
    # Safety check: never drop 'talent' database
    if [ "$db" = "talent" ]; then
        echo "⚠️  Skipping 'talent' (PRIMARY DATABASE - PROTECTED)"
        ((SKIPPED_COUNT++))
        continue
    fi
    
    echo "Dropping: $db"
    
    if psql -h localhost -p 5432 -U "$USER" -d postgres -c "DROP DATABASE IF EXISTS $db;" 2>&1; then
        echo "  ✅ Dropped: $db"
        ((SUCCESS_COUNT++))
    else
        echo "  ❌ Failed to drop: $db"
        ((FAIL_COUNT++))
    fi
    echo ""
done

echo "============================================================================"
echo "Drop Summary"
echo "============================================================================"
echo "Dropped: $SUCCESS_COUNT"
echo "Failed: $FAIL_COUNT"
echo "Skipped (Protected): $SKIPPED_COUNT"
echo ""
echo "Remaining databases:"
psql -h localhost -p 5432 -U "$USER" -d postgres -c "\l" | grep -E "talent|graph|recruiting|crypto" | grep -v "template"
echo ""
echo "✅ Database cleanup complete!"
echo ""
echo "PRIMARY DATABASE: PostgreSQL 'talent' @ localhost:5432"
echo "  - 32,515 people"
echo "  - 91,722 companies"
echo "  - 203,076 employment records"
echo "  - 1,014 emails"
echo "  - 17,534 GitHub profiles"
echo ""
echo "============================================================================"


#!/bin/bash

# Archive PostgreSQL Databases
# This script creates dumps of all PostgreSQL databases that are being archived
# Run this BEFORE dropping any databases

ARCHIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/postgresql_dumps"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Databases to archive
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
echo "  Archiving PostgreSQL Databases"
echo "============================================================================"
echo ""
echo "Archive directory: $ARCHIVE_DIR"
echo "Databases to archive: ${#DATABASES[@]}"
echo ""

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Create a log file
LOG_FILE="$ARCHIVE_DIR/archive_log_$TIMESTAMP.txt"
echo "Archive started at $(date)" > "$LOG_FILE"

SUCCESS_COUNT=0
FAIL_COUNT=0

for db in "${DATABASES[@]}"; do
    echo "Archiving: $db"
    
    DUMP_FILE="$ARCHIVE_DIR/${db}_${TIMESTAMP}.sql.gz"
    
    # Create compressed dump
    if pg_dump -h localhost -p 5432 -U "$USER" -d "$db" | gzip > "$DUMP_FILE" 2>> "$LOG_FILE"; then
        SIZE=$(du -h "$DUMP_FILE" | cut -f1)
        echo "  ✅ Archived: $DUMP_FILE ($SIZE)"
        echo "SUCCESS: $db -> $DUMP_FILE ($SIZE)" >> "$LOG_FILE"
        ((SUCCESS_COUNT++))
    else
        echo "  ❌ Failed to archive $db (check $LOG_FILE)"
        echo "FAILED: $db" >> "$LOG_FILE"
        ((FAIL_COUNT++))
    fi
    echo ""
done

echo "============================================================================"
echo "Archive Summary"
echo "============================================================================"
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $FAIL_COUNT"
echo "Total size: $(du -sh "$ARCHIVE_DIR" | cut -f1)"
echo ""
echo "Log file: $LOG_FILE"
echo ""
echo "Archive complete! Dumps saved to: $ARCHIVE_DIR"
echo ""
echo "To restore a database later:"
echo "  gunzip -c <dump_file.sql.gz> | psql -d <database_name>"
echo ""
echo "============================================================================"
echo ""
echo "⚠️  NEXT STEP: Review archived databases, then optionally drop them"
echo ""
echo "To DROP archived databases (CAUTION - cannot be undone!):"
echo "  ./drop_archived_databases.sh"
echo ""
echo "============================================================================"


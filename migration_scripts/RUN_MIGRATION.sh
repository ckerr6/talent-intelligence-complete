#!/bin/bash
# ============================================================================
# Master Migration Execution Script
# Runs all migration phases in the correct order with validation checkpoints
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SQLITE_DB="${SQLITE_DB:-../talent_intelligence.db}"
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
PG_DB="${PG_DB:-talent}"
PG_USER="${PG_USER:-$USER}"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}        DATABASE MIGRATION: SQLite → PostgreSQL talent${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "Configuration:"
echo "  SQLite DB: $SQLITE_DB"
echo "  PostgreSQL: $PG_USER@$PG_HOST:$PG_PORT/$PG_DB"
echo ""

# Function to pause and ask for confirmation
confirm() {
    read -p "$(echo -e ${YELLOW}Continue with $1? [y/N]:${NC} )" response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted by user${NC}"
        exit 1
    fi
}

# Function to print section header
print_section() {
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}============================================================================${NC}"
}

# Phase 0: Pre-flight checks
print_section "Phase 0: Pre-flight Checks"

echo "Checking SQLite database..."
if [ ! -f "$SQLITE_DB" ]; then
    echo -e "${RED}Error: SQLite database not found at $SQLITE_DB${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SQLite database found${NC}"

echo "Checking PostgreSQL connection..."
if ! psql -h "$PG_HOST" -p "$PG_PORT" -d "$PG_DB" -U "$PG_USER" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to PostgreSQL${NC}"
    echo "Please check your connection parameters and credentials"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL connection successful${NC}"

echo "Checking Python dependencies..."
python3 -c "import psycopg2" 2>/dev/null || {
    echo -e "${RED}Error: psycopg2 not installed${NC}"
    echo "Install with: pip3 install psycopg2-binary"
    exit 1
}
echo -e "${GREEN}✓ Python dependencies OK${NC}"

confirm "pre-flight checks passed"

# Phase 1: Schema Enhancement
print_section "Phase 1: Schema Enhancement"

echo "This will add new tables to PostgreSQL talent database:"
echo "  - person_email (for multiple emails per person)"
echo "  - github_profile (GitHub profile data)"
echo "  - github_repository (repository information)"
echo "  - github_contribution (profile-repo links)"
echo "  - migration_log (tracking migration progress)"
echo ""

confirm "schema enhancement"

echo "Running schema enhancement SQL..."
psql -h "$PG_HOST" -p "$PG_PORT" -d "$PG_DB" -U "$PG_USER" -f 01_schema_enhancement.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Schema enhancement complete${NC}"
else
    echo -e "${RED}✗ Schema enhancement failed${NC}"
    exit 1
fi

# Phase 2: Email Migration
print_section "Phase 2: Email Migration"

echo "This will migrate ~7,000 email addresses from SQLite to PostgreSQL"
echo "Emails will be matched to people via LinkedIn URLs"
echo ""

confirm "email migration"

echo "Running email migration..."
python3 02_migrate_emails.py \
    --sqlite-db "$SQLITE_DB" \
    --pg-host "$PG_HOST" \
    --pg-port "$PG_PORT" \
    --pg-db "$PG_DB" \
    --pg-user "$PG_USER"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Email migration complete${NC}"
else
    echo -e "${RED}✗ Email migration failed${NC}"
    exit 1
fi

# Phase 3: GitHub Migration
print_section "Phase 3: GitHub Migration"

echo "This will migrate ~18,000 GitHub profiles, repositories, and contributions"
echo "Profiles will be linked to people where possible"
echo ""

confirm "GitHub migration"

echo "Running GitHub migration..."
python3 03_migrate_github.py \
    --sqlite-db "$SQLITE_DB" \
    --pg-host "$PG_HOST" \
    --pg-port "$PG_PORT" \
    --pg-db "$PG_DB" \
    --pg-user "$PG_USER"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ GitHub migration complete${NC}"
else
    echo -e "${RED}✗ GitHub migration failed${NC}"
    exit 1
fi

# Phase 4: Deduplication
print_section "Phase 4: Deduplication"

echo "This will identify and merge duplicate people in the database"
echo "Strategy: Moderate (merge on LinkedIn URL OR email match)"
echo "Expected: ~2,500 duplicates to be merged"
echo ""

confirm "deduplication"

echo "Running deduplication (dry run first)..."
python3 04_deduplicate_people.py \
    --pg-host "$PG_HOST" \
    --pg-port "$PG_PORT" \
    --pg-db "$PG_DB" \
    --pg-user "$PG_USER" \
    --dry-run

echo ""
echo -e "${YELLOW}Dry run complete. Review the results above.${NC}"
confirm "actual deduplication"

echo "Running actual deduplication..."
python3 04_deduplicate_people.py \
    --pg-host "$PG_HOST" \
    --pg-port "$PG_PORT" \
    --pg-db "$PG_DB" \
    --pg-user "$PG_USER"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deduplication complete${NC}"
else
    echo -e "${RED}✗ Deduplication failed${NC}"
    exit 1
fi

# Phase 5: Validation
print_section "Phase 5: Validation"

echo "Running comprehensive validation tests..."
python3 05_validate_migration.py \
    --sqlite-db "$SQLITE_DB" \
    --pg-host "$PG_HOST" \
    --pg-port "$PG_PORT" \
    --pg-db "$PG_DB" \
    --pg-user "$PG_USER"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Validation complete${NC}"
else
    echo -e "${YELLOW}⚠ Validation completed with warnings${NC}"
fi

# Final Summary
print_section "Migration Complete!"

echo "All phases completed successfully:"
echo "  ✓ Schema enhancement"
echo "  ✓ Email migration"
echo "  ✓ GitHub migration"
echo "  ✓ Deduplication"
echo "  ✓ Validation"
echo ""
echo "Next steps:"
echo "  1. Review validation results above"
echo "  2. Spot-check some profiles in the database"
echo "  3. Run your application tests"
echo "  4. Archive old databases (see CLEANUP_GUIDE.md)"
echo ""
echo -e "${GREEN}Database consolidation complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"


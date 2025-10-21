# Archived Implementations

This directory contains legacy scripts and implementations that are no longer actively used but are kept for historical reference.

## Contents

### Legacy Database Builders (SQLite-era, Pre-Migration)
- `build_candidate_database.py` - Built SQLite people table (historical)
- `build_company_database.py` - Built SQLite company table (historical)

**Status**: These built the original SQLite database that was migrated to PostgreSQL. Historical reference only.

### One-Time Fix Scripts
- `fix_employment_duplicates.py` - Employment deduplication fix
- `fix_github_schema.py` - GitHub schema fix

**Status**: One-time fixes that may have already been run. Archived for reference.

### Historical Setup Scripts
- `day1_setup.sh` - Phase 1 setup (completed)
- `day2_setup.sh` - Phase 2 setup (completed)
- `RUN_ME.sh` - Original SQLite builder (legacy)
- `RUN_PHASE2.sh` - Company phase (legacy)
- `RUN_PHASE3.sh` - GitHub phase (legacy)

**Status**: Historical setup scripts from SQLite era. All phases completed.

## Current Active Scripts

For current active scripts, see:
- `config.py` - Core configuration
- `migration_scripts/` - Completed migration scripts
- `enrichment_scripts/` - Ready-to-run enrichment scripts
- `github_automation/` - Production-ready GitHub automation
- `api/` - FastAPI application
- `dashboard/` - Web interface

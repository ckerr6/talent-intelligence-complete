# SQLite Era Scripts Archive

This directory contains scripts and documentation from the original SQLite-based implementation of the Talent Intelligence system. These scripts were used to build and populate the initial SQLite database before the migration to PostgreSQL.

## Archived Scripts

### Database Building Scripts
- `build_candidate_database.py` - Original script to build the candidate database from raw data
- `build_company_database.py` - Original script to build the company database from raw data

### Setup and Execution Scripts
- `RUN_ME.sh` - Main execution script for the SQLite implementation
- `RUN_PHASE2.sh` - Phase 2 execution script
- `RUN_PHASE3.sh` - Phase 3 execution script
- `day1_setup.sh` - Day 1 setup script
- `day2_setup.sh` - Day 2 setup script

### Documentation
- `DAY1_COMPLETE.md` - Documentation for Day 1 completion
- `DAY2_COMPLETE.md` - Documentation for Day 2 completion

## Historical Context

These scripts represent the initial implementation phase where:
1. Raw talent data was processed and structured
2. SQLite databases were created and populated
3. Basic data relationships were established
4. Initial GitHub integration was implemented

## Migration Status

All functionality from these scripts has been migrated to:
- PostgreSQL database with improved schema
- Modern Python API (`api/` directory)
- GitHub automation package (`github_automation/`)
- Continuous enrichment system (`enrich_github_continuous.py`)

## Note

These scripts are preserved for historical reference and should not be executed against the current PostgreSQL-based system. The current system uses the scripts in the root directory and specialized packages for all operations.

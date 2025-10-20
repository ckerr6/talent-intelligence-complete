# Archived Databases

This directory contains archived databases from the pre-migration consolidation.

## Contents

- **sqlite/**: SQLite databases (moved from project root)
- **postgresql_dumps/**: PostgreSQL database dumps for archival

## Archived Databases

### Active (Consolidated)
- PostgreSQL `talent` - **PRIMARY DATABASE** (32,515 people, 91,722 companies, enhanced with emails & GitHub)

### Archived (October 20, 2025)
- SQLite `talent_intelligence.db` - Original data source (15,350 people, data migrated to PostgreSQL)
- PostgreSQL `talent_intelligence` - Duplicate of SQLite import
- PostgreSQL `talent_intel` - Partial/abandoned database
- PostgreSQL `talentgraph*` - Experimental graph databases
- PostgreSQL `tech_recruiting_db` - Empty/abandoned
- PostgreSQL `crypto_dev_network` - Empty/abandoned

All unique data from these databases has been consolidated into PostgreSQL `talent`.


# Scripts Directory

User-facing scripts for database operations, imports, and maintenance.

## Structure

- `database/` - Database operations (backup, query, quality checks)
- `diagnostics/` - Diagnostic and monitoring tools
- `imports/` - Data import scripts (Clay, CSV, etc.)
- `github/` - GitHub profile matching and discovery
- `maintenance/` - System maintenance (deduplication, graph population)

## Usage

All scripts can be run directly from this directory:

```bash
# Database operations
python database/backup_database.py
python database/check_data_quality.py

# Diagnostics
python diagnostics/diagnostic_check.py
python diagnostics/monitor_hung_queries.py

# Imports
python imports/import_clay_people.py

# GitHub
python github/match_github_profiles.py

# Maintenance
python maintenance/deduplicate_companies.py
```

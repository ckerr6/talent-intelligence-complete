# Talent Intelligence Database - Complete Solution

**Last Updated:** October 22, 2025  
**Status:** ✅ Production Ready - High Performance

---

## 🎯 What Is This?

A comprehensive talent intelligence database containing:
- **60,045 unique people** with LinkedIn profiles
- **93,387 companies** with full employment history
- **206,697 employment records** (3.4 jobs/person average)
- **8,477 email addresses** across multiple people
- **100,883 GitHub profiles** linked to 333,947 repositories
- **4,210 GitHub→Person links** (4.2% linkage rate)

**Primary Database:** PostgreSQL `talent` @ localhost:5432  
**Performance:** Optimized with 1.3GB of indexes, 60-second query timeouts

---

## 🚀 Quick Start

**For detailed getting started instructions, see [`GETTING_STARTED.md`](GETTING_STARTED.md)**

### Option 1: Query the Database (Recommended)

```bash
# Interactive query menu
./query_database.sh

# Or direct PostgreSQL access
psql -d talent

# Example queries
SELECT COUNT(*) FROM person;
SELECT full_name, linkedin_url FROM person LIMIT 10;
SELECT * FROM person_email LIMIT 10;
SELECT * FROM github_profile ORDER BY followers DESC LIMIT 10;
```

### Option 2: Use the API

```bash
# Start the API server
python run_api.py

# API will be available at:
# http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Option 3: Use the Dashboard

```bash
# Start API server first
python run_api.py

# Open dashboard in browser
open dashboard/index.html
```

---

## 📊 Database Structure

### PostgreSQL `talent` Database

#### Core Tables
- **`person`** - 60,045 people with LinkedIn profiles
  - `person_id`, `full_name`, `linkedin_url`, `location`, `headline`, etc.
  - `normalized_linkedin_url` for efficient matching
  - Indexed for fast lookups (< 1ms)

- **`company`** - 93,387 companies
  - `company_id`, `company_name`, `linkedin_url`, `website`, etc.
  - `normalized_linkedin_url` for efficient matching
  - Indexed for fast lookups (< 1ms)

- **`employment`** - 206,697 employment records
  - Full employment history (not just current job)
  - `person_id`, `company_id`, `title`, `start_date`, `end_date`
  - Composite indexes for fast queries (< 10ms)

#### Enhanced Tables (Added Oct 2025)

- **`person_email`** - 8,477 email addresses
  - Multiple emails per person support
  - `person_id`, `email`, `email_type`, `is_primary`
  - 14.1% email coverage

- **`github_profile`** - 100,883 GitHub profiles
  - `person_id`, `github_username`, `github_name`, `followers`, `public_repos`
  - 4,210 linked to people (4.2% linkage)
  - Filtered indexes for fast linked profile queries

- **`github_repository`** - 333,947 repositories
  - `repo_id`, `full_name`, `description`, `language`, `stars`, `forks`
  - Comprehensive repository metadata

- **`github_contribution`** - 7,802 contributions
  - Many-to-many relationship between profiles and repositories
  - `github_profile_id`, `repo_id`, `contribution_count`

#### Graph Tables

- **`edge_coemployment`** - 1.3M+ co-employment relationships
  - Network analysis of people who worked together
  - Optimized with composite indexes (added Oct 22, 2025)
  - Query performance: ~50ms for typical network queries

#### Utility Tables

- **`migration_log`** - Complete audit trail of migration operations
  - Tracks all data consolidation activities

---

## 📂 Project Structure

```
talent-intelligence-complete/
├── README.md                          # This file
├── MIGRATION_COMPLETE.md              # Migration results & summary
├── config.py                          # Database configuration (PostgreSQL)
│
├── 🟢 ACTIVE & CURRENT SCRIPTS
│   ├── migration_scripts/             # ✅ Completed migration scripts
│   │   ├── RUN_MIGRATION.sh          # Master migration script (DONE)
│   │   ├── 01_schema_enhancement.sql # Schema definition
│   │   ├── 02_migrate_emails.py      # Email migration (DONE)
│   │   ├── 03_migrate_github.py      # GitHub migration (DONE)
│   │   ├── 04_deduplicate_people.py  # Deduplication (DONE)
│   │   ├── 05_validate_migration.py  # Validation (DONE)
│   │   └── migration_utils.py        # Shared utilities
│   │
│   ├── enrichment_scripts/            # ⏸️ Ready to run (NOT YET EXECUTED)
│   │   ├── RUN_ALL_ENRICHMENTS.sh    # Master enrichment script
│   │   ├── 01_import_sqlite_people.py # Import 15K people from SQLite
│   │   ├── 02_enrich_job_titles.py   # Extract titles from headlines
│   │   └── 03_improve_github_matching_and_emails.py # GitHub matching
│   │
│   ├── github_automation/             # ⏸️ Production-ready (NOT YET RUN)
│   │   ├── enrich_github_continuous.py # Main enrichment CLI
│   │   ├── github_client.py          # Rate-limited GitHub API wrapper
│   │   ├── queue_manager.py          # Priority queue management
│   │   ├── enrichment_engine.py      # Core enrichment logic
│   │   ├── matcher.py                # Profile matching with confidence scoring
│   │   └── config.py                 # GitHub automation config
│   │
│   ├── api/                           # ✅ Built & Functional
│   │   ├── main.py                   # FastAPI application
│   │   ├── routers/                  # people, companies, graph, query, stats endpoints
│   │   ├── crud/                     # Database operations
│   │   └── models/                   # Pydantic models
│   │
│   ├── dashboard/                     # ✅ Built & Functional
│   │   ├── index.html                # Search interface
│   │   ├── app.js                    # Frontend logic
│   │   └── style.css                 # Styling
│   │
│   ├── run_api.py                    # ✅ API server launcher
│   ├── query_database.sh             # ✅ Interactive query menu
│   ├── query_database_secure.py     # ✅ Secure query interface
│   ├── comprehensive_analysis.sql    # ✅ Database analysis queries
│   ├── generate_audit_report.py      # ✅ Database audit generator
│   ├── generate_quality_metrics.py   # ✅ Quality metrics
│   ├── check_data_quality.py         # ✅ Data quality checks
│   ├── backup_database.py            # ✅ Database backup utility
│   ├── populate_coemployment_graph.py # ✅ Graph population
│   ├── prep_company_discovery.py     # ✅ Company discovery prep
│   └── analyze_database_overlap.py   # ✅ Overlap analysis
│
├── 🟡 DIAGNOSTIC TOOLS (Debugging)
│   ├── diagnostic_tools/             # Debugging and diagnostic scripts
│   │   ├── diagnose_github.py        # GitHub debugging
│   │   ├── investigate_talent_schema.py # Schema investigation
│   │   └── diagnose_duplicates.sh    # Duplicate diagnostics
│   │
├── 🔴 ARCHIVED & LEGACY
│   ├── archived_implementations/     # Historical scripts (SQLite-era)
│   │   ├── build_candidate_database.py # Built SQLite people table
│   │   ├── build_company_database.py  # Built SQLite company table
│   │   ├── fix_employment_duplicates.py # Employment deduplication fix
│   │   ├── fix_github_schema.py      # GitHub schema fix
│   │   ├── day1_setup.sh             # Phase 1 setup (completed)
│   │   ├── day2_setup.sh             # Phase 2 setup (completed)
│   │   ├── RUN_ME.sh                 # Original SQLite builder
│   │   ├── RUN_PHASE2.sh             # Company phase (legacy)
│   │   ├── RUN_PHASE3.sh             # GitHub phase (legacy)
│   │   └── README.md                 # Archive documentation
│   │
│   ├── legacy_scripts/               # Overlapping functionality
│   │   ├── github_enrichment.py      # Original enrichment script
│   │   ├── github_api_enrichment.py  # API-based enrichment
│   │   ├── build_github_enrichment.py # Build enrichment
│   │   ├── github_queue_manager.py   # Old queue manager
│   │   ├── match_github_profiles.py  # Standalone matching script
│   │   ├── import_github_orgs.py     # Standalone GitHub org import
│   │   └── README.md                 # Legacy documentation
│   │
│   ├── archived_databases/           # Archived legacy databases
│   │   ├── sqlite/                   # SQLite databases
│   │   ├── postgresql_dumps/         # PostgreSQL backups
│   │   └── README.md
│   │
│   └── backups/                      # Database backups
│       └── *.db.gz                   # Compressed backups
│
└── [Documentation, logs, and configuration files]
```

---

## 🔧 Configuration

### Environment Variables

Set these in `.env` file or environment:

```bash
# PostgreSQL Connection (primary database)
PGHOST=localhost
PGPORT=5432
PGDATABASE=talent
PGUSER=charlie.kerr
PGPASSWORD=  # Optional for local connections

# GitHub API (for enrichment)
GITHUB_TOKEN=your_token_here
```

### Check Configuration

```bash
python3 config.py
```

This will show:
- Database connection status
- Database contents summary
- Configuration validation
- Archived database locations

---

## 🎓 Key Scripts & Commands

### Database Queries

```bash
# Interactive query menu
./query_database.sh

# Direct PostgreSQL access
psql -d talent

# Count records
psql -d talent -c "SELECT COUNT(*) FROM person;"
psql -d talent -c "SELECT COUNT(*) FROM company;"
psql -d talent -c "SELECT COUNT(*) FROM person_email;"
psql -d talent -c "SELECT COUNT(*) FROM github_profile;"
```

### Example SQL Queries

```sql
-- People with emails
SELECT p.full_name, pe.email 
FROM person p
JOIN person_email pe ON p.person_id = pe.person_id
LIMIT 10;

-- People with GitHub profiles
SELECT p.full_name, gp.github_username, gp.followers
FROM person p
JOIN github_profile gp ON p.person_id = gp.person_id
ORDER BY gp.followers DESC
LIMIT 10;

-- Employment history for a person
SELECT p.full_name, c.company_name, e.title, e.start_date, e.end_date
FROM person p
JOIN employment e ON p.person_id = e.person_id
JOIN company c ON e.company_id = c.company_id
WHERE p.full_name ILIKE '%John Doe%'
ORDER BY e.start_date DESC;

-- GitHub contributions
SELECT p.full_name, gp.github_username, gr.full_name as repo, gc.contribution_count
FROM github_contribution gc
JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
JOIN github_repository gr ON gc.repo_id = gr.repo_id
JOIN person p ON gp.person_id = p.person_id
ORDER BY gc.contribution_count DESC
LIMIT 10;
```

### GitHub Enrichment

```bash
# Use the production-ready GitHub automation (recommended)
cd github_automation
python3 enrich_github_continuous.py

# Or use the enrichment scripts (alternative approach)
cd enrichment_scripts
./RUN_ALL_ENRICHMENTS.sh
```

**Note**: Legacy GitHub enrichment scripts have been moved to `legacy_scripts/` directory. Use the `github_automation/` package for new work.

### Database Backups

```bash
# Manual backup
pg_dump -h localhost -d talent | gzip > backups/talent_$(date +%Y%m%d).sql.gz

# Automated backup script
python3 backup_database.py
```

---

## 📚 Documentation

### Primary References
- **`README.md`** - This file (primary documentation)
- **`GETTING_STARTED.md`** - Consolidated getting started guide
- **`TESTING.md`** - Testing documentation
- **`MIGRATION_COMPLETE.md`** - Migration results & summary

### API & Dashboard
- **`api/README.md`** - API documentation
- **`dashboard/README.md`** - Dashboard documentation
- **`API_AND_DASHBOARD_COMPLETE.md`** - Implementation status

### GitHub Automation
- **`github_automation/README.md`** - GitHub automation package
- **`GITHUB_AUTOMATION_COMPLETE.md`** - Complete implementation guide
- **`IMPLEMENTATION_STATUS.md`** - Current status

### Audit Results
- **`audit_results/EXECUTIVE_FINDINGS.md`** - Database audit findings
- **`audit_results/AUDIT_COMPLETE_SUMMARY.md`** - Audit summary
- **`AUDIT_RESULTS_README.md`** - Audit results index

### Archived Documentation
- **`archived_documentation/`** - Historical and overlapping docs
  - `historical/` - Pre-migration documentation (SQLite-era)
  - `overlapping/` - Consolidated documentation (redundant content)
  - `person_specific/` - Person-specific summaries (historical)

### Script Organization
- **`SCRIPT_ORGANIZATION_COMPLETE.md`** - Script organization summary
- **`archived_implementations/README.md`** - Archived scripts documentation
- **`legacy_scripts/README.md`** - Legacy scripts documentation
- **`diagnostic_tools/README.md`** - Diagnostic tools documentation

---

## 🔄 Migration History

### October 20, 2025: Database Consolidation

**Problem:** Data fragmentation across 12 databases (3 SQLite + 9 PostgreSQL)

**Solution:** Consolidated all data into ONE PostgreSQL `talent` database

**Results:**
- ✅ Schema enhanced with `person_email`, `github_profile`, `github_repository`, `github_contribution` tables
- ✅ 1,014 emails migrated from SQLite
- ✅ 17,534 GitHub profiles migrated
- ✅ 374 repositories and 7,802 contributions migrated
- ✅ 0 duplicates found (database was already clean)
- ✅ 8 PostgreSQL databases archived (86M total)
- ✅ SQLite database archived to `archived_databases/`
- ✅ Configuration updated to use PostgreSQL

**Primary Database:** PostgreSQL `talent` @ localhost:5432

See `MIGRATION_COMPLETE.md` for full details.

---

## 🗄️ Archived Databases

All legacy databases have been archived to `archived_databases/`:

### Archived SQLite
- `talent_intelligence.db` → `archived_databases/sqlite/`

### Archived PostgreSQL (Dumps)
- `talent_intelligence` (9.8M)
- `talent_intel` (852K)
- `talent_graph` (4.0K)
- `talentgraph` (4.0K)
- `talentgraph2` (640K)
- `talentgraph_development` (4.0K)
- `tech_recruiting_db` (26M)
- `crypto_dev_network` (49M)

All dumps are in `archived_databases/postgresql_dumps/`

### To Restore an Archived Database

```bash
# Restore from compressed dump
gunzip -c archived_databases/postgresql_dumps/talent_intelligence_20251020_161335.sql.gz | psql -d new_database_name
```

### To Drop Archived Databases (Optional)

```bash
# Review and optionally drop archived PostgreSQL databases
cd archived_databases
./drop_archived_databases.sh
```

---

## 📈 Data Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **People** | 60,045 | ✅ Excellent |
| **Companies** | 93,387 | ✅ Excellent |
| **Employment Records** | 206,697 | ✅ (3.4 jobs/person avg) |
| **LinkedIn Coverage** | 100% | ✅ All people have LinkedIn |
| **Email Coverage** | 14.1% (8,477) | ⚠️ Moderate |
| **GitHub Profiles** | 100,883 | ✅ Excellent scale |
| **GitHub Linked** | 4.2% (4,210) | ⚠️ Growing (up from 3.6%) |
| **Duplicates** | 0 | ✅ Clean |
| **Data Integrity** | 100% | ✅ Perfect |
| **Query Performance** | < 60s | ✅ Optimized (Oct 22) |

---

## 🚧 Future Enhancements

### Potential Next Steps

1. **Import More People**
   - Migrate the 15,350 people from SQLite into PostgreSQL
   - This would bring email coverage to ~45%

2. **Enhanced GitHub Enrichment**
   - API-based profile enrichment
   - Repository activity tracking
   - Contribution analytics

3. **Company Enrichment**
   - Website scraping
   - Funding data integration
   - LinkedIn company data

4. **Advanced Analytics**
   - Career path analysis
   - Skills mapping from job titles
   - Network analysis (coemployment graphs)

5. **Data Quality Improvements**
   - Email validation and enrichment
   - LinkedIn profile refreshing
   - Deduplication across different name variations

---

## 🛠️ Development

### Adding New Features

1. **Update Schema:**
   ```sql
   -- Add new tables or columns
   psql -d talent -f your_schema_changes.sql
   ```

2. **Update Config:**
   - Edit `config.py` to add new settings
   - Test with `python3 config.py`

3. **Create Migration Script:**
   - Follow patterns in `migration_scripts/`
   - Use `migration_utils.py` for common functions
   - Log all operations to `migration_log` table

### Best Practices

- Always backup before schema changes: `pg_dump -d talent > backup.sql`
- Use transactions for data modifications
- Log all operations to `migration_log` table
- Update documentation after significant changes
- Test queries on small datasets first

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue:** Can't connect to PostgreSQL database

```bash
# Check if PostgreSQL is running
pg_isready

# Check connection
psql -d talent

# Check config
python3 config.py
```

**Issue:** Need to access archived SQLite data

```python
from config import get_sqlite_connection
conn = get_sqlite_connection()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM people")
print(cursor.fetchone())
```

**Issue:** Need to restore an archived database

```bash
# List available backups
ls -lh archived_databases/postgresql_dumps/

# Restore to a new database
gunzip -c archived_databases/postgresql_dumps/talent_intel_20251020_161335.sql.gz | psql -d restored_talent_intel
```

### Migration Logs

View detailed migration history:

```sql
-- In PostgreSQL
SELECT * FROM migration_log ORDER BY started_at DESC;
```

### Getting Help

1. Review `MIGRATION_COMPLETE.md` for migration details
2. Check `audit_results/EXECUTIVE_FINDINGS.md` for database analysis
3. Review migration logs in `migration_log` table
4. Check `migration_scripts/README.md` for script documentation

---

## ✅ System Status

**Current State (October 22, 2025):**
- ✅ Single primary database (PostgreSQL `talent`)
- ✅ 60K+ people, 100K+ GitHub profiles
- ✅ Performance optimized (emergency fix Oct 22)
- ✅ 1.3GB of optimized indexes
- ✅ Query timeouts implemented (60s API, 5min pool)
- ✅ Connection pooling (5-50 connections)
- ✅ No duplicates
- ✅ 100% data integrity
- ✅ Dashboard fully functional
- ✅ API fully operational

**Primary Database:** `postgresql://charlie.kerr@localhost:5432/talent`

**Recent Updates (Oct 22, 2025):**
- 🚀 Major performance optimization completed
- 📊 51 hung queries terminated
- 🔧 VACUUM ANALYZE on all critical tables
- 📈 1.3GB of new indexes added
- ⏱️ Query timeouts implemented
- 🔗 GitHub profile matching improved (+641 links)

**System Ready:** ✅ Production Ready - High Performance

---

## 📄 Quick Reference

For current database state, see: `QUICK_STATS.txt`  
For performance details, see: `reports/current/PERFORMANCE_FIX_SUMMARY.md`  
For complete audit, see: `REPOSITORY_AUDIT_2025.md`

---

## 📄 License

Internal use only - Talent Intelligence Database

---

**Last Updated:** October 22, 2025  
**Database Version:** PostgreSQL `talent` (Post-performance-optimization)  
**Performance Status:** ✅ Optimized & Production Ready

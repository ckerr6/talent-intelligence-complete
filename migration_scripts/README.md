# Database Migration Scripts

This directory contains all scripts needed to migrate data from SQLite to PostgreSQL `talent` database and perform deduplication.

## Overview

**Goal**: Consolidate data from multiple databases into one PostgreSQL `talent` database

**What gets migrated:**
- 7,036 email addresses from SQLite
- 18,029 GitHub profiles from SQLite
- Repositories and contribution data
- Deduplication of ~2,500 duplicate people

**Expected outcome:**
- ~30,000 unique people (after deduplication)
- 25-30% email coverage
- 60% GitHub coverage
- 100% LinkedIn coverage maintained

---

## Quick Start

### Prerequisites

1. **Python dependencies:**
   ```bash
   pip3 install psycopg2-binary
   ```

2. **PostgreSQL access:**
   - You need connection access to the `talent` database
   - User must have CREATE/ALTER/INSERT/UPDATE/DELETE permissions

3. **SQLite database:**
   - Located at `../talent_intelligence.db` (or specify path)

### Run Everything at Once

```bash
cd migration_scripts
chmod +x RUN_MIGRATION.sh
./RUN_MIGRATION.sh
```

This master script will:
1. Run pre-flight checks
2. Execute all migration phases in order
3. Ask for confirmation at each step
4. Validate results at the end

**Time:** 15-30 minutes total

---

## Manual Execution (Step by Step)

If you prefer to run each phase manually:

### Phase 1: Schema Enhancement

Adds new tables to PostgreSQL:

```bash
psql -d talent -f 01_schema_enhancement.sql
```

**What it creates:**
- `person_email` table
- `github_profile` table
- `github_repository` table
- `github_contribution` table
- `migration_log` table
- `normalized_linkedin_url` column on `person`

### Phase 2: Email Migration

```bash
python3 02_migrate_emails.py \
    --sqlite-db ../talent_intelligence.db \
    --pg-db talent
```

**Options:**
- `--sqlite-db`: Path to SQLite database (default: `../talent_intelligence.db`)
- `--pg-host`: PostgreSQL host (default: `localhost`)
- `--pg-port`: PostgreSQL port (default: `5432`)
- `--pg-db`: PostgreSQL database name (default: `talent`)
- `--pg-user`: PostgreSQL user (default: current user)
- `--dry-run`: Test without inserting data

**What it does:**
- Extracts emails from SQLite `people` and `emails` tables
- Matches people by normalized LinkedIn URLs
- Inserts emails into `person_email` table
- Deduplicates emails per person

### Phase 3: GitHub Migration

```bash
python3 03_migrate_github.py \
    --sqlite-db ../talent_intelligence.db \
    --pg-db talent
```

**What it does:**
- Migrates GitHub profiles
- Migrates repositories
- Migrates contribution links
- Matches profiles to people via LinkedIn URL and email

### Phase 4: Deduplication

**Dry run first (recommended):**

```bash
python3 04_deduplicate_people.py \
    --pg-db talent \
    --dry-run
```

**Then run actual deduplication:**

```bash
python3 04_deduplicate_people.py --pg-db talent
```

**What it does:**
- Finds duplicates by LinkedIn URL
- Finds duplicates by email address
- Consolidates overlapping duplicate groups
- Chooses primary record (most complete data)
- Merges employment, education, emails, GitHub profiles
- Removes duplicate person records

**Strategy:** Moderate
- Merges on LinkedIn URL match OR email match
- Conservative enough to avoid false merges
- Aggressive enough to catch real duplicates

### Phase 5: Validation

```bash
python3 05_validate_migration.py \
    --sqlite-db ../talent_intelligence.db \
    --pg-db talent
```

**What it tests:**
- Schema exists correctly
- Email migration completeness
- GitHub migration completeness
- Person linkage rates
- No data loss
- Data quality metrics
- Foreign key integrity
- Migration logs
- Spot-check random profiles

---

## Files in This Directory

### SQL Scripts

- **`01_schema_enhancement.sql`**
  - Adds new tables and columns
  - Creates indexes
  - Adds migration tracking

### Python Scripts

- **`migration_utils.py`**
  - Common utility functions
  - URL/email normalization
  - Matching algorithms
  - Progress tracking

- **`02_migrate_emails.py`**
  - Email migration logic
  - Person matching
  - Deduplication

- **`03_migrate_github.py`**
  - GitHub profile migration
  - Repository migration
  - Contribution links

- **`04_deduplicate_people.py`**
  - Duplicate detection
  - Record merging
  - Data consolidation

- **`05_validate_migration.py`**
  - Comprehensive validation
  - Data quality checks
  - Integrity tests

### Shell Scripts

- **`RUN_MIGRATION.sh`**
  - Master execution script
  - Runs all phases in order
  - Interactive confirmations

---

## Configuration

### Environment Variables

Set these before running scripts:

```bash
export SQLITE_DB="/path/to/talent_intelligence.db"
export PG_HOST="localhost"
export PG_PORT="5432"
export PG_DB="talent"
export PG_USER="your_username"
```

### Command Line Arguments

All Python scripts accept these arguments:

```
--sqlite-db PATH    Path to SQLite database
--pg-host HOST      PostgreSQL host
--pg-port PORT      PostgreSQL port
--pg-db DBNAME      PostgreSQL database name
--pg-user USER      PostgreSQL user
--dry-run           Test mode (no changes)
```

---

## Migration Strategy

### Matching Logic

**People are matched between databases using:**

1. **LinkedIn URL** (highest confidence)
   - URLs are normalized (decoded, protocol removed)
   - Example: `linkedin.com/in/john-smith`

2. **Email address** (high confidence)
   - Emails are normalized (lowercased, trimmed)
   - Example: `john.smith@company.com`

3. **Unmatched profiles** (stored but not linked)
   - GitHub profiles without matching person

### Deduplication Logic

**Duplicates are identified by:**

1. Same normalized LinkedIn URL
2. Same email address
3. Groups are consolidated (if A=B and B=C, then A=B=C)

**Primary record is chosen by:**

1. Most recent `refreshed_at` timestamp
2. Most complete data (non-null fields)
3. Highest follower count

**Data is preserved:**
- All emails transferred to primary
- All GitHub profiles transferred
- All employment records transferred
- All education records transferred
- Duplicate records deleted

---

## Safety Features

### Pre-flight Checks

- Database connectivity
- File existence
- Python dependencies
- Permissions

### Transaction Safety

- All operations use transactions
- Rollback on error
- Can be rerun safely (idempotent)

### Logging

All operations logged to `migration_log` table:

```sql
SELECT * FROM migration_log ORDER BY started_at DESC;
```

### Dry Run Mode

Test migrations without changes:

```bash
python3 02_migrate_emails.py --dry-run
python3 04_deduplicate_people.py --dry-run
```

---

## Troubleshooting

### "Connection refused"

Check PostgreSQL is running and credentials are correct:

```bash
psql -h localhost -d talent -U $USER -c "SELECT 1"
```

### "Permission denied"

Your user needs these permissions:

```sql
GRANT ALL PRIVILEGES ON DATABASE talent TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

### "SQLite database not found"

Specify the correct path:

```bash
python3 02_migrate_emails.py --sqlite-db /full/path/to/talent_intelligence.db
```

### "No people matched"

Check that LinkedIn URLs are properly normalized:

```sql
SELECT COUNT(*) FROM person WHERE normalized_linkedin_url IS NULL;
```

If many are null, run the normalization update:

```sql
UPDATE person 
SET normalized_linkedin_url = normalize_linkedin_url(linkedin_url)
WHERE linkedin_url IS NOT NULL;
```

### Migration stuck or slow

- Check database locks: `SELECT * FROM pg_locks;`
- Reduce batch size in scripts
- Run during low-traffic hours

---

## Post-Migration

### Verify Results

```sql
-- Check counts
SELECT COUNT(*) FROM person;           -- Should be ~30,000
SELECT COUNT(*) FROM person_email;     -- Should be ~7,000
SELECT COUNT(*) FROM github_profile;   -- Should be ~18,000

-- Check coverage
SELECT 
    COUNT(*) as total_people,
    COUNT(DISTINCT pe.person_id) as people_with_email,
    COUNT(DISTINCT gp.person_id) as people_with_github
FROM person p
LEFT JOIN person_email pe ON p.person_id = pe.person_id
LEFT JOIN github_profile gp ON p.person_id = gp.person_id;

-- Check migration logs
SELECT * FROM migration_log ORDER BY started_at DESC;
```

### Update Application Config

Update `config.py` to point to PostgreSQL:

```python
DATABASE = {
    'type': 'postgresql',
    'host': 'localhost',
    'port': 5432,
    'database': 'talent',
    'user': 'your_user'
}
```

### Archive Old Databases

See `CLEANUP_GUIDE.md` for instructions on archiving:
- SQLite databases
- Duplicate PostgreSQL databases

---

## Support

### Check Migration Logs

```sql
SELECT 
    migration_name,
    migration_phase,
    status,
    records_processed,
    records_created,
    error_message
FROM migration_log
ORDER BY started_at DESC;
```

### Review Validation Results

```bash
python3 05_validate_migration.py
```

### Common Issues

All scripts have error handling and will:
- Print detailed error messages
- Log to `migration_log` table
- Rollback on failure
- Can be rerun safely

---

## Timeline

**Estimated time for complete migration:**

| Phase | Time | Can Skip |
|-------|------|----------|
| Schema Enhancement | 1 min | No |
| Email Migration | 5-10 min | No |
| GitHub Migration | 10-15 min | No |
| Deduplication (dry run) | 2-3 min | Yes |
| Deduplication (actual) | 2-3 min | No |
| Validation | 2-3 min | Yes |
| **Total** | **15-30 min** | |

Can be paused and resumed at any phase.

---

## Success Criteria

Migration is successful when:

✅ All scripts complete without errors  
✅ Validation passes (or only warnings)  
✅ Person count ~30,000 (±2,000)  
✅ Email coverage 20-30%  
✅ GitHub coverage 40-60%  
✅ No orphaned foreign keys  
✅ Spot-checks show complete profiles  

---

**Ready to start? Run `./RUN_MIGRATION.sh`**


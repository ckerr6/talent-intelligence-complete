# Clay CSV Import Guide

**Script:** `import_clay_people.py`  
**Purpose:** Import people data from Clay CSV exports into PostgreSQL talent database  
**Status:** ✅ Ready to use

---

## Quick Start

```bash
# Run the import
python3 import_clay_people.py

# The script will:
# 1. Show pre-flight statistics
# 2. Ask for confirmation
# 3. Process all rows
# 4. Generate detailed report
```

---

## What It Does

### Data Import Strategy
- **Deduplication:** Matches people by LinkedIn URL (normalized)
- **Existing Profiles:** Enriches with new data (preserves existing)
- **New Profiles:** Creates new person records
- **Companies:** Matches by name or creates new
- **Employment:** Links people to companies via employment records

### Safety Features
✅ **ALWAYS preserves existing data** (uses COALESCE)  
✅ **Prevents duplicates** (ON CONFLICT DO NOTHING)  
✅ **Requires confirmation** before starting  
✅ **Progress updates** every 100 rows  
✅ **Detailed error tracking**  
✅ **Full audit trail** in migration_log table  

---

## CSV Format

The script expects Clay export format with these columns:

| Column Name | Required | Maps To | Notes |
|------------|----------|---------|-------|
| Find people | No | (ignored) | Empty column |
| Current Company | No | company.company_name | Used for employment |
| First Name | No | person.first_name | |
| Last Name | No | person.last_name | |
| Full Name | **Yes** | person.full_name | Required if creating new |
| Job Title | No | person.headline | Also used in employment |
| Location | No | person.location | |
| Company Domain | No | company.company_domain | Often empty |
| LinkedIn Profile | **Yes** | person.linkedin_url | Primary deduplication key |

**Minimum Requirements:**
- LinkedIn Profile URL (for matching/creating)
- Full Name (for new profiles)

---

## Current Import Details

**CSV File:** `/Users/charlie.kerr/Desktop/Imports for TI Final/clay_find_people_crypto.csv`

**Statistics:**
- Total Rows: 10,221
- Current Database: 51,087 people
- Expected New Profiles: ~9,000-10,000
- Expected Enrichments: ~200-1,000
- Expected Runtime: 10-15 minutes

---

## What Happens During Import

### 1. Pre-Flight Check
- Validates CSV exists and is readable
- Shows current database state
- Displays what will be imported
- Requires user confirmation

### 2. Processing
```
Processed 100 rows... (95 created, 5 enriched)
Processed 200 rows... (190 created, 10 enriched)
...
```

### 3. Final Report
Shows:
- Total rows processed
- Profiles created vs enriched
- Companies matched vs created
- Employment records added
- Any errors encountered
- Final database totals

### 4. Report File
Saves detailed report to:
```
clay_import_report_YYYYMMDD_HHMMSS.txt
```

---

## Examples

### Successful Import
```bash
$ python3 import_clay_people.py

================================================================================
CLAY CSV IMPORT - PRE-FLIGHT CHECK
================================================================================

📄 CSV file found: 10,221 rows
⚠️  This will import/enrich up to 10,221 people into your database

Database: talent@localhost

Current Database State:
   People: 51,087

Proceed with import? (yes/no): yes

📦 Loading existing data into cache...
   ✅ Loaded 51,087 people, 91,882 companies

================================================================================
CLAY CSV IMPORT - PEOPLE DATA
================================================================================

   Processed 100 rows... (95 created, 5 enriched)
   Processed 200 rows... (195 created, 5 enriched)
   ...
   
✅ Processing complete!

================================================================================
IMPORT COMPLETE - FINAL REPORT
================================================================================

📊 PROCESSING STATISTICS:
   Total Rows Processed: 10,221

👥 PEOPLE:
   ✅ Profiles Created: 9,980
   🔄 Profiles Enriched: 241
   ⏭️  Skipped (Duplicate): 0

🏢 COMPANIES:
   ✅ Companies Created: 187
   🔄 Companies Matched: 9,793

💼 EMPLOYMENT:
   ✅ Employment Records Added: 10,221

📈 DATABASE TOTALS (After Import):
   Total People: 61,067
   Total Companies: 92,069
   Total Employment Records: 213,297
```

---

## Deduplication Logic

### How It Works
1. **Normalize LinkedIn URL**
   - Convert to lowercase
   - Remove protocol (https://)
   - Remove www.
   - Extract just: `linkedin.com/in/username`

2. **Check Cache**
   - Fast in-memory lookup
   - Loaded at startup

3. **Decision**
   - **Found:** Enrich existing profile (COALESCE preserves data)
   - **Not Found:** Create new profile

### Example
```
Input:  "https://www.linkedin.com/in/john-smith/"
Normalized: "linkedin.com/in/john-smith"
Match: Yes → Enrich existing
       No  → Create new
```

---

## Data Preservation

### Enriching Existing Profiles
```sql
UPDATE person
SET 
  first_name = COALESCE(first_name, 'John'),    -- Only if NULL
  location = COALESCE(location, 'San Francisco'), -- Only if NULL
  headline = COALESCE(headline, 'CEO'),          -- Only if NULL
  refreshed_at = NOW()                           -- Always update
WHERE person_id = '...'
```

**Result:** New data fills gaps, existing data is NEVER overwritten

---

## Company Matching

### Strategy
1. **Normalize company name** (lowercase, trim)
2. **Check cache** for exact match
3. **Found:** Use existing company_id
4. **Not Found:** Create new company

### Domain Handling
- If Company Domain provided: Use it
- If empty: Generate placeholder (e.g., "0x.placeholder")
- Prevents duplicates via UNIQUE constraint

---

## Employment Records

### Logic
- Only creates if person+company relationship doesn't exist
- Prevents duplicate employment records
- Links to matched/created company

```sql
-- Check first
SELECT employment_id 
FROM employment 
WHERE person_id = X AND company_id = Y

-- If not found, insert
INSERT INTO employment (person_id, company_id, title)
VALUES (...)
```

---

## Troubleshooting

### "CSV file not found"
Check the CSV_PATH variable in the script matches your file location:
```python
CSV_PATH = "/Users/charlie.kerr/Desktop/Imports for TI Final/clay_find_people_crypto.csv"
```

### "Could not query database"
Ensure PostgreSQL is running:
```bash
psql -d talent -c "SELECT COUNT(*) FROM person"
```

### High "Skipped (Duplicate)" count
This is normal if you've already imported this CSV. The script detects duplicates by LinkedIn URL.

### Errors in report
Check the generated report file for details:
```bash
cat clay_import_report_*.txt
```

---

## Modifying for Different CSVs

To use with different Clay exports:

1. **Update CSV_PATH**
   ```python
   CSV_PATH = "/path/to/your/new/file.csv"
   ```

2. **Verify column names** match Clay format:
   - First Name, Last Name, Full Name
   - Job Title, Location
   - Current Company, Company Domain
   - LinkedIn Profile

3. **Run as usual**

---

## Best Practices

1. **Always review pre-flight check** before confirming
2. **Run during low-traffic periods** for large imports
3. **Keep CSV files** for audit trail
4. **Review import reports** for errors
5. **Check migration_log table** for audit history

```sql
-- View recent imports
SELECT * FROM migration_log 
WHERE migration_name = 'clay_csv_import' 
ORDER BY started_at DESC;
```

---

## Related Scripts

- `import_csv_datablend.py` - DataBlend format imports
- `import_company_portfolio.py` - Company-only imports
- `enrichment_scripts/` - Data enrichment tools
- `migration_scripts/` - Schema migrations

---

## Support

If you encounter issues:
1. Check this README
2. Review the generated import report
3. Check migration_log table
4. Verify CSV format matches expected columns


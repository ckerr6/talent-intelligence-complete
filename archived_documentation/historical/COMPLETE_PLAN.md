# Complete Solution Plan: Talent Intelligence Database

## Overview

This is a **pragmatic, production-ready** solution to compile all your candidate and company data into a clean, queryable database.

### Technology Choices
- **SQLite** for Phase 1 (simple, portable, zero setup)
- **Batch processing** (5k records at a time) for memory efficiency on M1 Pro 16GB RAM
- **Smart deduplication** based on email, LinkedIn, and name+company
- **Extensible design** - easy to migrate to PostgreSQL later

---

## Three-Phase Approach

### ✅ PHASE 1: High-Quality Candidates (DO THIS NOW)
**Goal**: Create clean database of ~16,400 candidates with names, emails, LinkedIn, company info

**What It Does**:
1. Scans all CSVs in your CK Docs folder
2. Identifies high-quality candidate records (name + contact info + company)
3. Deduplicates intelligently:
   - Email match = same person (100% confidence)
   - LinkedIn URL match = same person (100% confidence)
   - Same name + same company = same person (merge with better data)
4. Creates SQLite database with proper relationships
5. Generates quality reports

**Expected Output**:
- ~15,000-16,000 unique candidates (after deduplication)
- Quality score: 0.6-0.8 average (60-80% completeness)
- Processing time: 2-5 minutes

**Files Created**:
- `talent_intelligence.db` - Your database
- `data_quality_report.txt` - Quality metrics
- `deduplication_report.txt` - What was merged
- `sample_queries.sql` - How to query the data
- `import_log.txt` - Detailed processing log

### 🔄 PHASE 2: Company Data (NEXT)
**Goal**: Extract and normalize company information

**What It Does**:
1. Processes company CSV files you listed
2. Extracts unique companies with:
   - Name, website, LinkedIn, GitHub org
   - Industry, funding rounds, investors
3. Links candidates to companies via company_id
4. Tracks funding history

**Expected Output**:
- ~1,000-2,000 unique companies
- Funding data for VC-backed companies
- Employee → company relationships

### 🚀 PHASE 3: GitHub Enrichment (LATER)
**Goal**: Process 400k GitHub contributors, match to existing candidates

**What It Does**:
1. Enriches GitHub data with emails, Twitter, websites
2. Attempts to match GitHub accounts to existing candidates
3. Creates separate table for unmatched developers (sourcing pool)

**Expected Output**:
- ~30-50% of GitHub accounts matched to candidates
- ~200-300k unique developer profiles for sourcing
- Skills extraction from repos

---

## Database Schema (Phase 1)

```
people
├── person_id (PK)           # Unique identifier
├── first_name
├── last_name
├── full_name
├── primary_email
├── location
├── status                   # active, archived, etc.
├── data_quality_score       # 0.0 - 1.0
├── created_at
├── updated_at
└── notes

social_profiles              # One person → many platforms
├── profile_id (PK)
├── person_id (FK)
├── platform                 # linkedin, github, twitter
├── profile_url
└── username

emails                       # One person → many emails
├── email_id (PK)
├── person_id (FK)
├── email
├── email_type               # work, personal
└── is_primary               # 1 or 0

employment                   # Current & historical jobs
├── employment_id (PK)
├── person_id (FK)
├── company_name
├── title
├── start_date
├── end_date
└── is_current               # 1 or 0

data_sources                 # Track where data came from
├── source_id (PK)
├── person_id (FK)
├── source_file
├── source_type              # manual, gem, linkedin, etc.
└── ingestion_date
```

---

## Deduplication Strategy

### Matching Rules (in priority order)

1. **Email Match** → 100% confidence
   - Exact match on normalized email
   - Automatically merge records

2. **LinkedIn URL Match** → 100% confidence  
   - Normalized LinkedIn URLs (linkedin.com/in/username)
   - Automatically merge records

3. **Name + Company Match** → 95% confidence
   - Same first name + last name + company
   - Merge if data quality improves
   - Keep record with higher completeness

### Merging Logic

When duplicates are found:
- **Keep most complete data** from both records
- **Prefer non-null values**
- **Use longer/more complete values** when both have data
- **Update quality score** based on merged record
- **Track in deduplication log**

### Example

```
Record 1:
  name: John Smith
  email: john@company.com
  linkedin: linkedin.com/in/johnsmith
  company: Acme Inc
  title: (empty)
  
Record 2:
  name: John Smith
  email: (empty)
  linkedin: linkedin.com/in/johnsmith
  company: Acme Inc
  title: Senior Engineer

Merged Result:
  name: John Smith
  email: john@company.com
  linkedin: linkedin.com/in/johnsmith
  company: Acme Inc
  title: Senior Engineer        ← Filled from Record 2
  quality_score: 0.85            ← Updated
```

---

## Data Quality Scoring

Each person gets a quality score (0.0 - 1.0) based on:

| Field | Weight |
|-------|--------|
| First Name | 15% |
| Last Name | 15% |
| Primary Email | 25% |
| LinkedIn URL | 20% |
| Current Company | 10% |
| Current Title | 10% |
| GitHub URL | 5% |

**Example Scores**:
- 1.0 = Perfect (all fields filled)
- 0.75 = High quality (name, email, LinkedIn, company, title)
- 0.50 = Medium quality (name, email, company)
- 0.30 = Low quality (name, email only)

Records below 0.30 are considered low-quality and skipped.

---

## Memory Efficiency

**M1 Pro with 16GB RAM can comfortably handle**:
- 5,000-10,000 records in memory at once
- Batch processing prevents memory overflow
- Indexes kept in memory for fast deduplication
- Database commits every 5,000 records

**Processing Strategy**:
1. Read CSV in 5,000-row chunks
2. Process each chunk completely
3. Commit to database
4. Clear memory
5. Move to next chunk

**Estimated Memory Usage**:
- ~2GB peak during processing
- ~500MB for indexes
- ~100MB for database file

---

## Sample Queries

Once your database is built, here are useful queries:

### Find candidates from specific company
```sql
SELECT p.first_name, p.last_name, p.primary_email, e.title
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE LOWER(e.company_name) LIKE '%uniswap%'
AND e.is_current = 1;
```

### Get complete profile
```sql
SELECT 
    p.*,
    GROUP_CONCAT(DISTINCT sp.platform || ': ' || sp.profile_url) as social,
    GROUP_CONCAT(DISTINCT em.email) as all_emails
FROM people p
LEFT JOIN social_profiles sp ON p.person_id = sp.person_id
LEFT JOIN emails em ON p.person_id = em.person_id
WHERE p.primary_email = 'example@email.com'
GROUP BY p.person_id;
```

### High-quality candidates
```sql
SELECT first_name, last_name, primary_email, data_quality_score
FROM people
WHERE data_quality_score > 0.7
ORDER BY data_quality_score DESC;
```

---

## Migration Path to PostgreSQL

When ready to scale, migrating from SQLite to PostgreSQL is straightforward:

### Option 1: Export/Import
```bash
# Export from SQLite
sqlite3 talent_intelligence.db .dump > database.sql

# Import to PostgreSQL
psql -d talent_db -f database.sql
```

### Option 2: Use pgloader (recommended)
```bash
brew install pgloader
pgloader talent_intelligence.db postgresql://user:pass@localhost/talent_db
```

### Option 3: Rerun with PostgreSQL
Just change the database connection in the script from:
```python
conn = sqlite3.connect(db_path)
```
To:
```python
import psycopg2
conn = psycopg2.connect(host, database, user, password)
```

---

## Future Enhancements

### Phase 2 Additions
- Company funding rounds table
- Investor relationships
- Company GitHub organizations
- Employee → company historical relationships

### Phase 3 Additions
- GitHub skills extraction from repos
- Automated profile enrichment
- Network analysis (who worked with whom)
- Email verification

### Phase 4 Additions
- Web interface (Flask/FastAPI)
- REST API for programmatic access
- Automated CSV ingestion
- LinkedIn/GitHub API integrations
- Scheduled refresh jobs

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"
```bash
pip3 install pandas numpy
```

### "sqlite3.OperationalError: database is locked"
- Another program has the database open
- Close DB Browser, DBeaver, or other DB tools
- The script handles this automatically with retries

### "MemoryError" or system slows down
- Reduce BATCH_SIZE in script from 5000 to 2500
- Close other applications
- This should not happen on M1 Pro 16GB

### Very few candidates found
- Check `import_log.txt` for file processing details
- Verify CSV files are in expected locations
- Check quality threshold (currently 0.30)

### Too many duplicates NOT being merged
- Increase matching confidence
- Check normalization functions (email, LinkedIn)
- Review `deduplication_report.txt`

### Too many WRONG duplicates being merged
- Decrease matching confidence
- Remove name+company matching
- Review `deduplication_report.txt`

---

## Success Metrics

After Phase 1, you should have:

✅ **~15,000 unique candidates** in database  
✅ **Quality score > 0.6** on average  
✅ **90%+ with email or LinkedIn**  
✅ **80%+ with current employment**  
✅ **Duplicates reduced by 5-10%**  
✅ **Processing completed in < 5 minutes**  

---

## Next Steps After Phase 1

1. ✅ **Validate data** - Run sample queries, spot-check profiles
2. 🔄 **Build Phase 2** - Process company CSV files
3. 🔄 **Link candidates to companies** - Create relationships
4. 🚀 **Enrich GitHub data** - Phase 3 matching
5. 🚀 **Build query interface** - Web UI for searching

---

## Support

If you encounter issues:

1. Check `import_log.txt` for detailed error messages
2. Review `data_quality_report.txt` for statistics
3. Examine `deduplication_report.txt` for merge details
4. Run sample queries to validate data

The system is designed to be conservative - when uncertain about a match, it will skip rather than incorrectly merge.

---

**Ready to start? Run `./RUN_ME.sh` and let's build this database!**

# 🚀 Database Enrichment Scripts

**Purpose:** Address high-priority data quality issues identified in the database audit

**Status:** Ready to run  
**Target Database:** PostgreSQL `talent` @ localhost:5432  
**Source Data:** SQLite `talent_intelligence.db`

---

## 📊 Problems Being Solved

### Current State (Before Enrichment):
- ⚠️ **Email Coverage:** 3.11% (1,014 of 32,515 people)
- ⚠️ **Job Title Coverage:** 0.48% (965 of 203,076 employment records)
- ⚠️ **GitHub Linkage:** 0.57% (184 of 32,515 people)
- ⚠️ **Unused GitHub Emails:** 5,000 GitHub profiles have emails not in `person_email` table

### Expected State (After Enrichment):
- ✅ **Email Coverage:** ~45% (boost from 3% → 45%)
- ✅ **Job Title Coverage:** ~90%+ (extract from LinkedIn headlines)
- ✅ **GitHub Linkage:** 5-10% (improved matching by email + name)
- ✅ **GitHub Emails:** All 5,000 GitHub emails added to `person_email`

---

## 🎯 What These Scripts Do

### 1. **`01_import_sqlite_people.py`** - Import SQLite People & Emails

**Problem:** Only 1,014 of 7,034 SQLite emails were migrated (14% match rate) because SQLite contains different people than PostgreSQL.

**Solution:**
- Import ~15,350 people from SQLite who aren't in PostgreSQL yet
- Import their 7,034 emails
- Link via LinkedIn URLs (normalized for matching)

**Expected Results:**
- **Before:** 32,515 people, 1,014 emails (3.11%)
- **After:** ~47,865 people, ~8,048 emails (~17-45% depending on duplicates)

**Runtime:** 5-10 minutes

---

### 2. **`02_enrich_job_titles.py`** - Extract Job Titles from Headlines

**Problem:** Only 965 of 203,076 employment records (0.48%) have job titles populated, even though 100% of people have LinkedIn profiles with job titles in their headlines.

**Root Cause:** Job titles are stored in `person.headline` field (e.g., "Principal Engineer at Google") but not extracted into `employment.title`

**Solution:**
- Parse `person.headline` to extract current job titles
- Update `employment.title` for current jobs (where `end_date IS NULL`)
- Use pattern matching: "Title at Company" → extract "Title"

**Examples:**
```
"Principal Site Reliability Engineer at GoDaddy"
  → title = "Principal Site Reliability Engineer"

"Founder & CEO @ Company"
  → title = "Founder & CEO"

"Software Engineer | Tech Lead at Google"
  → title = "Software Engineer"
```

**Expected Results:**
- **Before:** 965 titles (0.48%)
- **After:** ~27,000 titles (90%+ for current jobs with LinkedIn data)

**Runtime:** 2-5 minutes

---

### 3. **`03_improve_github_matching_and_emails.py`** - GitHub Matching & Email Extraction

**Problems:**
1. Only 184 of 32,515 people (0.57%) have linked GitHub profiles
2. 5,000 GitHub profiles have emails that aren't in `person_email` table
3. 17,534 GitHub profiles exist but 17,345 (98.9%) aren't linked to people

**Solutions:**

#### A. Extract Emails from GitHub Profiles
- Take 5,000 emails from `github_profile.github_email` 
- Add to `person_email` table for linked profiles
- Mark source as 'github_profile'

#### B. Match GitHub Profiles to People by Email
- Compare `github_profile.github_email` to `person_email.email`
- Link matching profiles automatically
- This is high-confidence matching (email = strong identifier)

#### C. Match by Name + Company (Conservative)
- Compare `github_profile.github_name` to `person.full_name`
- AND compare `github_profile.github_company` to current `employment.company`
- Only link if exactly 1 match (avoid ambiguity)
- **Accuracy over volume** - skip ambiguous matches

**Expected Results:**
- **Emails from GitHub:** +5,000 emails added to `person_email`
- **GitHub Linkage:** 0.57% → 5-10% (actual number depends on email overlaps)
- **People with GitHub:** 184 → 1,500-3,000 (estimated)

**Runtime:** 3-8 minutes

---

## 🚀 How to Run

### Option 1: Run All Enrichments (Recommended)

```bash
cd enrichment_scripts
./RUN_ALL_ENRICHMENTS.sh
```

This will:
1. Check prerequisites (PostgreSQL connection, SQLite database, Python dependencies)
2. Show current state
3. Ask for confirmation at each phase
4. Run all 3 enrichments in sequence
5. Show final results

**Total Runtime:** 10-25 minutes

---

### Option 2: Run Individual Scripts

#### Import SQLite People
```bash
python3 01_import_sqlite_people.py \
    --sqlite-db ../talent_intelligence.db \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-db talent
```

#### Enrich Job Titles
```bash
python3 02_enrich_job_titles.py \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-db talent
```

#### Improve GitHub Matching
```bash
python3 03_improve_github_matching_and_emails.py \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-db talent
```

---

## 🔒 Safety Features

### Transaction Safety
- ✅ All operations use PostgreSQL transactions
- ✅ Rollback on error
- ✅ Commit every 100 records for progress tracking
- ✅ Can be rerun safely (idempotent where possible)

### Duplicate Prevention
- ✅ LinkedIn URL normalization prevents duplicates
- ✅ `ON CONFLICT DO NOTHING` clauses
- ✅ Unique constraints enforced
- ✅ Conservative matching (accuracy over volume)

### Logging
- ✅ All operations logged to `migration_log` table
- ✅ Detailed statistics printed
- ✅ Error tracking and reporting

---

## 📊 Expected Improvements

### Email Coverage
```
Before:  1,014 emails (3.11% of people)
After:   ~8,000-13,000 emails (17-45% of people)

Sources:
- 7,034 from SQLite primary_email
- 7,030 from SQLite emails table
- 5,000 from GitHub profiles
= ~19,000 total emails (deduplicated to ~8-13K unique)
```

### Job Title Coverage
```
Before:  965 titles (0.48% of employment records)
After:   ~27,000 titles (90%+ of current jobs)

Limitation: Only current jobs can be enriched from headline
Historical jobs require additional data sources
```

### GitHub Linkage
```
Before:  184 people with GitHub (0.57%)
After:   1,500-3,000 people with GitHub (5-10%)

Method:
- Email matching: High confidence, ~500-1,000 matches
- Name+Company: Conservative, ~500-1,000 matches
- Remaining unlinked: Standalone GitHub dataset
```

---

## ⚠️ Important Notes

### Why Not 100% Email Coverage?
Even after importing all SQLite people, email coverage will be ~45%, not 100%, because:
1. Not all SQLite people have emails (7,034 of 15,350 = 45.8%)
2. Some emails will be duplicates
3. Email validation may filter some invalid addresses

### Why Not Match All GitHub Profiles?
We prioritize **accuracy over volume**:
- Email matching: ✅ High confidence
- Name+Company: ✅ Conservative (skip ambiguous)
- Name-only: ❌ Too risky (many people share names)
- Username: ❌ Unreliable (usernames != real names)

**Result:** Lower linkage rate but higher data quality

### Historical Job Titles
Enrichment focuses on **current jobs** because:
- `person.headline` only shows current role
- Historical titles require employment history scraping
- Can be addressed in future enrichment phases

---

## 🧪 Testing

### Pre-flight Checks
The master script (`RUN_ALL_ENRICHMENTS.sh`) checks:
- ✅ PostgreSQL connection
- ✅ SQLite database exists
- ✅ Python dependencies installed

### Validation
Each script includes validation that:
- Counts before/after states
- Verifies no data loss
- Checks constraint integrity
- Logs to `migration_log` table

---

## 📈 Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **People** | 32,515 | ~47,865 | +15,350 |
| **Email Coverage** | 3.11% | ~45% | 40-50% |
| **Emails Total** | 1,014 | ~8,000 | 7,000+ |
| **Job Title Coverage** | 0.48% | ~90% | 85%+ |
| **GitHub Linkage** | 0.57% | ~5-10% | 5%+ |
| **People with GitHub** | 184 | ~2,000 | 1,500+ |

---

## 🐛 Troubleshooting

### Script fails with "Cannot connect to PostgreSQL"
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -d talent -c "SELECT 1"
```

### Script fails with "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Script fails with "SQLite database not found"
```bash
# Check the database path
ls -la ../talent_intelligence.db

# If it's elsewhere, use full path:
python3 01_import_sqlite_people.py --sqlite-db /full/path/to/talent_intelligence.db
```

### Want to see what will happen without making changes?
Add a `--dry-run` flag to any script (requires code modification, or manually review the SQL before running)

---

## 📝 Logs & Audit Trail

All enrichment operations are logged to the `migration_log` table:

```sql
-- View enrichment history
SELECT 
    migration_name,
    migration_phase,
    status,
    records_processed,
    records_created,
    started_at,
    completed_at
FROM migration_log
WHERE migration_name LIKE '%enrichment%' OR migration_name LIKE '%import%'
ORDER BY started_at DESC;
```

---

## 🔄 Re-running Scripts

### Safe to Re-run
All scripts use `ON CONFLICT DO NOTHING` or similar patterns, making them safe to re-run:
- Won't create duplicate people (LinkedIn URL unique constraint)
- Won't create duplicate emails (person_id + email unique constraint)
- Won't overwrite existing good data

### When to Re-run
- After adding new people to SQLite
- After getting more GitHub data
- To fill gaps from partial runs
- After fixing data quality issues

---

## 📚 Related Documentation

- **`MIGRATION_COMPLETE.md`** - Original migration documentation
- **`DATABASE_QUALITY_REPORT.md`** - Complete database analysis showing these issues
- **`comprehensive_analysis.sql`** - SQL queries to analyze database state
- **`migration_scripts/`** - Original consolidation scripts

---

## 🎓 Next Steps After Enrichment

1. **Validate Results:**
   ```bash
   psql -d talent -f ../comprehensive_analysis.sql > post_enrichment_report.txt
   ```

2. **Test Queries:**
   ```sql
   -- People with emails
   SELECT COUNT(DISTINCT person_id) FROM person_email;
   
   -- Employment records with titles
   SELECT COUNT(*) FROM employment WHERE title IS NOT NULL;
   
   -- People with GitHub
   SELECT COUNT(DISTINCT person_id) FROM github_profile WHERE person_id IS NOT NULL;
   ```

3. **Update Applications:**
   - Update dashboards with new metrics
   - Enable email-based features
   - Build GitHub-based insights

4. **Plan Next Enrichments:**
   - Historical job title extraction
   - Company metadata enrichment
   - Email verification
   - Advanced GitHub matching algorithms

---

**Created:** October 20, 2025  
**Status:** ✅ Ready for Production  
**Estimated Runtime:** 10-25 minutes total


# Getting Started Guide 🚀

**Last Updated:** October 21, 2025  
**Status:** Complete - Ready to use

---

## 🎯 Quick Start Options

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

## 📊 What You Have

A comprehensive talent intelligence database containing:
- **32,515 unique people** with LinkedIn profiles
- **91,722 companies** with full employment history
- **203,076 employment records** (6.2 jobs/person average)
- **1,014 email addresses** across multiple people
- **17,534 GitHub profiles** with repositories and contributions

**Primary Database:** PostgreSQL `talent` @ localhost:5432

---

## 🔧 Prerequisites

### Required Software
- PostgreSQL (running on localhost:5432)
- Python 3.8+
- Git

### Check Your Setup
```bash
# Verify PostgreSQL is running
pg_isready

# Check database exists
psql -d talent -c "SELECT COUNT(*) FROM person;"

# Verify Python environment
python --version
```

---

## 🚀 First Steps

### 1. Verify Database Connection
```bash
# Check configuration
python config.py
```

This will show:
- Database connection status
- Database contents summary
- Configuration validation
- Archived database locations

### 2. Explore the Data
```bash
# Interactive query menu
./query_database.sh
```

Choose from menu options:
- Count records by table
- Sample data queries
- Search by company/location
- GitHub profile queries

### 3. Try the API
```bash
# Start API server
python run_api.py

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/stats/overview
```

---

## 📚 Key Documentation

### Primary References
- **`README.md`** - Main documentation
- **`MIGRATION_COMPLETE.md`** - Migration results & summary
- **`TESTING.md`** - Testing documentation

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

---

## 🎓 Common Use Cases

### Find People by Company
```sql
-- People at specific company
SELECT p.full_name, p.headline, p.location
FROM person p
JOIN employment e ON p.person_id = e.person_id
JOIN company c ON e.company_id = c.company_id
WHERE c.company_name ILIKE '%Anthropic%'
ORDER BY e.start_date DESC;
```

### Find People with Emails
```sql
-- People with email addresses
SELECT p.full_name, pe.email, pe.email_type
FROM person p
JOIN person_email pe ON p.person_id = pe.person_id
WHERE pe.is_primary = true
LIMIT 10;
```

### Find GitHub Contributors
```sql
-- Top GitHub contributors
SELECT p.full_name, gp.github_username, gp.followers, gp.public_repos
FROM person p
JOIN github_profile gp ON p.person_id = gp.person_id
ORDER BY gp.followers DESC
LIMIT 20;
```

### Find People by Location
```sql
-- People in specific location
SELECT p.full_name, p.headline, c.company_name
FROM person p
JOIN employment e ON p.person_id = e.person_id
JOIN company c ON e.company_id = c.company_id
WHERE p.location ILIKE '%San Francisco%'
AND e.end_date IS NULL  -- Current employment
LIMIT 10;
```

---

## 🔄 Next Steps

### Ready-to-Run Scripts

#### 1. Enrichment Scripts (Boost Email Coverage)
```bash
cd enrichment_scripts
./RUN_ALL_ENRICHMENTS.sh
```
**Goal:** Increase email coverage from 3% → 45%

#### 2. GitHub Automation (Enrich Profiles)
```bash
cd github_automation
python enrich_github_continuous.py
```
**Goal:** Enrich 15,000+ GitHub profiles

### Monitoring & Quality
```bash
# Generate quality report
python generate_quality_metrics.py

# Run data quality checks
python check_data_quality.py

# Generate audit report
python generate_audit_report.py
```

---

## 🛠️ Development

### Adding New Features
1. **Update Schema:**
   ```sql
   psql -d talent -f your_schema_changes.sql
   ```

2. **Update Config:**
   - Edit `config.py` to add new settings
   - Test with `python config.py`

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

**Can't connect to PostgreSQL:**
```bash
# Check if PostgreSQL is running
pg_isready

# Check connection
psql -d talent

# Check config
python config.py
```

**API not responding:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Restart API server
python run_api.py
```

**Need to access archived data:**
```bash
# List available backups
ls -lh archived_databases/postgresql_dumps/

# Restore to a new database
gunzip -c archived_databases/postgresql_dumps/talent_intel_20251020_161335.sql.gz | psql -d restored_talent_intel
```

### Getting Help
1. Review `README.md` for main documentation
2. Check `MIGRATION_COMPLETE.md` for migration details
3. Review `audit_results/EXECUTIVE_FINDINGS.md` for database analysis
4. Check migration logs in `migration_log` table
5. Review `migration_scripts/README.md` for script documentation

---

## ✅ System Status

**Current State (October 21, 2025):**
- ✅ Single primary database (PostgreSQL `talent`)
- ✅ All legacy databases archived
- ✅ Email support added (1,014 emails)
- ✅ GitHub integration complete (17,534 profiles)
- ✅ No duplicates
- ✅ 100% data integrity
- ✅ Configuration updated
- ✅ Documentation current
- ✅ API and dashboard functional
- ✅ Testing complete (60+ tests passing)

**Primary Database:** `postgresql://charlie.kerr@localhost:5432/talent`

**System Ready:** ✅ Production Ready

---

## 🎯 Quick Commands Reference

```bash
# Database queries
./query_database.sh                    # Interactive menu
psql -d talent                         # Direct access

# API
python run_api.py                      # Start API server
curl http://localhost:8000/health      # Health check

# Dashboard
open dashboard/index.html              # Open web interface

# Configuration
python config.py                       # Check setup

# Quality & Monitoring
python generate_quality_metrics.py     # Quality report
python check_data_quality.py          # Data checks
python generate_audit_report.py        # Audit report

# Enrichment (Ready to Run)
cd enrichment_scripts && ./RUN_ALL_ENRICHMENTS.sh
cd github_automation && python enrich_github_continuous.py

# Testing
pytest -v                              # Run all tests
pytest --cov=. --cov-report=html      # Coverage report
```

---

**Ready to start exploring your talent intelligence database!** 🚀

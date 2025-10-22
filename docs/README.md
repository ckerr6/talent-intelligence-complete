# Documentation Index

Complete documentation for the Talent Intelligence Database.

**Last Updated:** October 22, 2025

---

## 📚 Quick Links

### For New Users
1. [**README.md**](../README.md) - Start here for overview and quick start
2. [**GETTING_STARTED.md**](GETTING_STARTED.md) - Detailed setup instructions
3. [**QUICK_STATS.txt**](../QUICK_STATS.txt) - Current database statistics

### For Developers
1. [**API_DOCUMENTATION.md**](../api/README.md) - API reference
2. [**TESTING.md**](TESTING.md) - Testing guide
3. [**GITHUB_AUTOMATION.md**](GITHUB_AUTOMATION.md) - GitHub automation

### For Troubleshooting
1. [**PERFORMANCE_FIX_SUMMARY.md**](../reports/current/PERFORMANCE_FIX_SUMMARY.md) - Recent performance fixes
2. [**DATABASE_STATE_OCTOBER_22_2025.md**](../reports/current/DATABASE_STATE_OCTOBER_22_2025.md) - Current database state
3. Support section below

---

## 📖 Documentation Structure

### Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](../README.md) | Main entry point, overview, quick start | Everyone |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and changes | Everyone |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Detailed setup and first steps | New users |
| [QUICK_STATS.txt](../QUICK_STATS.txt) | Current database statistics | Everyone |

### Technical Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [API Documentation](../api/README.md) | API endpoints and usage | Developers |
| [TESTING.md](TESTING.md) | Testing strategy and tools | Developers |
| [GITHUB_AUTOMATION.md](GITHUB_AUTOMATION.md) | GitHub enrichment system | Developers |
| [Dashboard Guide](../dashboard/README.md) | Web interface usage | Users |

### Process Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [CLAY_IMPORT.md](CLAY_IMPORT.md) | Clay data import process | Data team |
| [GITHUB_DISCOVERY.md](GITHUB_DISCOVERY.md) | GitHub profile discovery | Data team |
| [IMPORT_STRATEGY.md](IMPORT_STRATEGY.md) | Data import strategies | Data team |

### Reports & Analysis

| Document | Purpose | Audience |
|----------|---------|----------|
| [DATABASE_STATE_OCTOBER_22_2025.md](../reports/current/DATABASE_STATE_OCTOBER_22_2025.md) | Current database state | Everyone |
| [PERFORMANCE_FIX_SUMMARY.md](../reports/current/PERFORMANCE_FIX_SUMMARY.md) | Performance optimization | Technical |
| [REPOSITORY_AUDIT_2025.md](../REPOSITORY_AUDIT_2025.md) | Repository organization audit | Maintainers |

---

## 🎯 Documentation by Task

### I want to...

#### ...get started with the database
1. Read [README.md](../README.md) for overview
2. Follow [GETTING_STARTED.md](GETTING_STARTED.md) for setup
3. Check [QUICK_STATS.txt](../QUICK_STATS.txt) for current data

#### ...query the database
1. See "Database Queries" section in [README.md](../README.md)
2. Use `query_database.sh` for interactive queries
3. Check `sql/queries/sample_queries.sql` for examples

#### ...use the API
1. Read [API Documentation](../api/README.md)
2. Start API: `python run_api.py`
3. Visit Swagger UI: http://localhost:8000/docs

#### ...use the dashboard
1. Read [Dashboard Guide](../dashboard/README.md)
2. Start API: `python run_api.py`
3. Open `dashboard/index.html` in browser

#### ...import data
1. Read [IMPORT_STRATEGY.md](IMPORT_STRATEGY.md)
2. For Clay data: [CLAY_IMPORT.md](CLAY_IMPORT.md)
3. For GitHub: [GITHUB_AUTOMATION.md](GITHUB_AUTOMATION.md)

#### ...run GitHub enrichment
1. Read [GITHUB_AUTOMATION.md](GITHUB_AUTOMATION.md)
2. Read [GITHUB_DISCOVERY.md](GITHUB_DISCOVERY.md)
3. Run: `python scripts/github/match_github_profiles.py`

#### ...run tests
1. Read [TESTING.md](TESTING.md)
2. Run: `pytest tests/`

#### ...troubleshoot issues
1. Check [PERFORMANCE_FIX_SUMMARY.md](../reports/current/PERFORMANCE_FIX_SUMMARY.md)
2. Check [DATABASE_STATE_OCTOBER_22_2025.md](../reports/current/DATABASE_STATE_OCTOBER_22_2025.md)
3. See "Troubleshooting" section in [README.md](../README.md)

#### ...understand the schema
1. Read "Database Structure" in [README.md](../README.md)
2. Check `migration_scripts/01_schema_enhancement.sql`
3. Query: `\d+ tablename` in psql

#### ...monitor performance
1. Run: `python scripts/diagnostics/diagnostic_check.py`
2. Run: `python scripts/diagnostics/monitor_hung_queries.py`
3. Check: `python scripts/diagnostics/verify_performance.py`

---

## 📁 File Organization

### Root Level Documentation
```
README.md                          # Main documentation
CHANGELOG.md                       # Version history
QUICK_STATS.txt                    # Quick reference
REPOSITORY_AUDIT_2025.md           # Repository organization
```

### docs/ Directory (This Directory)
```
docs/
├── README.md                      # This file - navigation guide
├── GETTING_STARTED.md             # Setup instructions
├── TESTING.md                     # Testing guide
├── GITHUB_AUTOMATION.md           # GitHub enrichment
├── CLAY_IMPORT.md                 # Clay import process
├── GITHUB_DISCOVERY.md            # GitHub discovery
└── IMPORT_STRATEGY.md             # Import strategies
```

### reports/ Directory
```
reports/
├── current/                       # Active reports
│   ├── DATABASE_STATE_2025_10_22.md
│   └── PERFORMANCE_FIX_2025_10_22.md
└── historical/                    # Old reports
    └── [archived reports]
```

### Component Documentation
```
api/README.md                      # API documentation
dashboard/README.md                # Dashboard documentation
github_automation/README.md        # GitHub automation
migration_scripts/README.md        # Migration scripts
enrichment_scripts/README.md       # Enrichment scripts
```

---

## 🔍 Finding Information

### Current Database Statistics
- **Quick Reference:** [QUICK_STATS.txt](../QUICK_STATS.txt)
- **Detailed State:** [DATABASE_STATE_OCTOBER_22_2025.md](../reports/current/DATABASE_STATE_OCTOBER_22_2025.md)
- **Run Live Check:** `python scripts/diagnostics/diagnostic_check.py`

### Performance Information
- **Latest Fix:** [PERFORMANCE_FIX_SUMMARY.md](../reports/current/PERFORMANCE_FIX_SUMMARY.md)
- **Query Performance:** Run `python scripts/diagnostics/verify_performance.py`
- **Monitor Queries:** `python scripts/diagnostics/monitor_hung_queries.py`

### API Information
- **API Documentation:** [api/README.md](../api/README.md)
- **Interactive Docs:** http://localhost:8000/docs (when API running)
- **Endpoints:** Check `/api/routers/` for implementation

### Schema Information
- **Overview:** [README.md](../README.md) - "Database Structure" section
- **Migration Scripts:** `migration_scripts/01_schema_enhancement.sql`
- **Live Schema:** Run `psql -d talent` then `\d+` for tables

---

## 🆘 Support & Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
pg_isready

# Test connection
psql -d talent

# Check config
python3 config.py
```

#### Performance Issues
```bash
# Check current performance
python scripts/diagnostics/verify_performance.py

# Monitor for hung queries
python scripts/diagnostics/monitor_hung_queries.py

# Emergency: kill hung queries
python scripts/diagnostics/kill_hung_queries.py
```

#### API Not Working
```bash
# Check API status
curl http://localhost:8000/health

# View API logs
python run_api.py

# Test endpoints
curl http://localhost:8000/stats/overview
```

#### Dashboard Not Loading
1. Ensure API is running: `python run_api.py`
2. Check browser console for errors
3. Verify API is accessible: http://localhost:8000/docs
4. Check dashboard README: [dashboard/README.md](../dashboard/README.md)

### Getting Help

1. **Check Recent Changes:** [CHANGELOG.md](../CHANGELOG.md)
2. **Check Current State:** [DATABASE_STATE_OCTOBER_22_2025.md](../reports/current/DATABASE_STATE_OCTOBER_22_2025.md)
3. **Run Diagnostics:** `python scripts/diagnostics/diagnostic_check.py`
4. **Review Logs:** Check `logs/` directory
5. **Check Migration Logs:** `SELECT * FROM migration_log ORDER BY started_at DESC;`

---

## 📋 Document Templates

### When Adding New Documentation

**For Technical Docs:**
```markdown
# Title

**Author:** [Name]  
**Date:** [YYYY-MM-DD]  
**Status:** [Draft/Review/Final]

## Overview
Brief description of what this document covers.

## Prerequisites
What you need before starting.

## Instructions
Step-by-step guide.

## Troubleshooting
Common issues and solutions.

## References
Links to related documentation.
```

**For Reports:**
```markdown
# Report Title

**Generated:** [YYYY-MM-DD HH:MM]  
**Type:** [Analysis/Audit/Performance]

## Summary
Key findings in 3-5 bullet points.

## Detailed Findings
In-depth analysis.

## Recommendations
Actionable next steps.

## Appendix
Supporting data and queries.
```

---

## 🔄 Keeping Documentation Updated

### When to Update Documentation

- ✅ After major feature additions
- ✅ After schema changes
- ✅ After performance optimizations
- ✅ When statistics change significantly (10%+)
- ✅ When troubleshooting patterns emerge

### What to Update

1. **CHANGELOG.md** - Every significant change
2. **README.md** - Statistics, status, quick start
3. **QUICK_STATS.txt** - After data imports
4. **Component READMEs** - When component changes
5. **This file** - When adding new documentation

### How to Update

```bash
# Update statistics
python scripts/diagnostics/diagnostic_check.py > QUICK_STATS.txt

# Update state report
# Run diagnostics and save to reports/current/

# Update CHANGELOG
# Add entry to CHANGELOG.md with version and changes

# Update README
# Edit README.md with new statistics and status
```

---

## 📊 Documentation Health

**Last Full Audit:** October 22, 2025

**Status:**
- ✅ README.md - Current (Oct 22, 2025)
- ✅ CHANGELOG.md - Current (Oct 22, 2025)
- ✅ QUICK_STATS.txt - Current (Oct 22, 2025)
- ✅ Core docs - Current
- ⚠️ Some historical docs - Outdated but archived

**Next Review:** November 2025 or after next major update

---

## 📝 Notes

- Documentation follows Markdown format for GitHub compatibility
- All timestamps in Eastern Time (ET)
- File paths use forward slashes for cross-platform compatibility
- All SQL examples tested on PostgreSQL 14+

---

**Last Updated:** October 22, 2025  
**Maintainer:** System Admin  
**Status:** ✅ Current


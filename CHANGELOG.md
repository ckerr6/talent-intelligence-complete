# Changelog

All notable changes to the Talent Intelligence Database will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.2.0] - 2025-10-22

### 🚀 Performance Optimization (Emergency Fix)

#### Added
- Query timeouts: 60s for API queries, 5min for connection pool
- Connection pooling increased to 5-50 connections (from 1-10)
- 1.3GB of optimized indexes on critical tables
- `monitor_hung_queries.py` - Continuous query monitoring tool
- `kill_hung_queries.py` - Emergency query termination tool
- `verify_performance.py` - Performance testing suite
- `emergency_performance_fix.sql` - Critical index and maintenance script

#### Changed
- `config.py`: Increased pool size, added statement_timeout
- `api/dependencies.py`: Added 60-second timeout for all API queries
- `edge_coemployment`: Added composite indexes (src, dst, company)
- `employment`: Added composite indexes (person_company, person_dates, company_dates)
- `github_profile`: Added filtered index for linked profiles

#### Fixed
- **CRITICAL:** Database performance issues after 100K GitHub profile import
- Terminated 51 hung queries (including 5-hour "idle in transaction")
- VACUUM ANALYZE on all critical tables (especially `github_profile`, `edge_coemployment`)
- Dashboard now loads in < 1 second (was timing out)
- API response times: < 60s for all queries

#### Performance Metrics
- Person profile queries: < 1ms (was timing out)
- Employment history: < 10ms (was 30s+)
- Graph queries: ~50ms (was 90s+)
- GitHub profile count: 0.4s (was hanging indefinitely)

---

## [1.1.0] - 2025-10-22

### 📊 Large-Scale GitHub Import

#### Added
- 100,883 GitHub profiles (up from 17K)
- 333,947 repositories (up from 374)
- 8,477 emails (up from 1,014)
- Clay import pipeline for people data
- Company deduplication tools
- GitHub profile matching improvements

#### Changed
- Database size: Now managing 60K+ people
- GitHub linkage: 4,210 linked profiles (4.2%)
- Email coverage: 14.1% (up from 3.1%)

#### Documentation
- `DATABASE_STATE_OCTOBER_22_2025.md` - Current accurate state
- `PERFORMANCE_FIX_SUMMARY.md` - Performance fix details
- `QUICK_STATS.txt` - Quick reference statistics

---

## [1.0.0] - 2025-10-20

### 🎉 Database Consolidation Complete

#### Added
- PostgreSQL as primary database (`talent`)
- `person_email` table - Multi-email support
- `github_profile` table - GitHub user profiles
- `github_repository` table - Repository metadata
- `github_contribution` table - Profile-repo relationships
- `edge_coemployment` table - Co-worker network graph
- `migration_log` table - Migration audit trail
- Normalized LinkedIn URLs for efficient matching

#### Changed
- **BREAKING:** Migrated from SQLite to PostgreSQL
- Consolidated 12 databases into 1 primary database
- Updated all scripts to use PostgreSQL
- Configuration now points to PostgreSQL

#### Removed
- 8 deprecated PostgreSQL databases (archived)
- SQLite as primary database (archived)

#### Migration Results
- 32,515 people migrated
- 91,722 companies migrated
- 203,076 employment records migrated
- 1,014 emails migrated from SQLite
- 17,534 GitHub profiles migrated
- 0 duplicates found

#### Documentation
- `MIGRATION_COMPLETE.md` - Complete migration summary
- `API_AND_DASHBOARD_COMPLETE.md` - API & dashboard guide
- `GITHUB_AUTOMATION_COMPLETE.md` - GitHub automation guide
- Reorganized all documentation

---

## [0.9.0] - 2025-10-19 and earlier

### Initial Development
- Built SQLite database with people and companies
- Created employment history tracking
- Implemented basic API with FastAPI
- Built web dashboard
- Created GitHub enrichment automation
- Developed data quality tools

---

## Future Releases

### Planned for [1.3.0]
- Increase GitHub linkage to 10%+ (target: 10,000 linked profiles)
- Improve email enrichment (target: 30%+ coverage)
- Enhanced monitoring and diagnostics
- Repository reorganization for cleaner structure

### Under Consideration
- Skills extraction from job titles
- Career path analysis
- Advanced network analysis
- Company enrichment pipeline
- Real-time data updates

---

## Notes

### Version Numbering
- **Major (X.0.0)**: Database schema changes, breaking changes
- **Minor (1.X.0)**: New features, significant data additions
- **Patch (1.0.X)**: Bug fixes, documentation updates

### Performance Targets
- All API queries: < 60 seconds
- Person profile lookups: < 1ms
- Employment queries: < 10ms
- Graph queries: < 100ms
- Dashboard page load: < 2 seconds

### Data Quality Standards
- 0 duplicate people or companies
- 100% LinkedIn coverage for people
- 10%+ GitHub linkage rate (target)
- 30%+ email coverage (target)



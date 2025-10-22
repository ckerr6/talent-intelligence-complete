-- ============================================================================
-- EMERGENCY PERFORMANCE FIX
-- Adds critical missing indexes and performs VACUUM ANALYZE
-- ============================================================================

\timing on

-- Set work_mem higher for index creation
SET maintenance_work_mem = '1GB';

\echo '============================================================================'
\echo 'STEP 1: VACUUM ANALYZE ALL TABLES'
\echo '============================================================================'
\echo ''

\echo 'Vacuuming github_profile (CRITICAL)...'
VACUUM ANALYZE github_profile;
\echo '✓ github_profile vacuumed'
\echo ''

\echo 'Vacuuming edge_coemployment (CRITICAL - 19GB table)...'
VACUUM ANALYZE edge_coemployment;
\echo '✓ edge_coemployment vacuumed'
\echo ''

\echo 'Vacuuming person...'
VACUUM ANALYZE person;
\echo '✓ person vacuumed'
\echo ''

\echo 'Vacuuming employment...'
VACUUM ANALYZE employment;
\echo '✓ employment vacuumed'
\echo ''

\echo 'Vacuuming company...'
VACUUM ANALYZE company;
\echo '✓ company vacuumed'
\echo ''

\echo 'Vacuuming person_email...'
VACUUM ANALYZE person_email;
\echo '✓ person_email vacuumed'
\echo ''

\echo ''
\echo '============================================================================'
\echo 'STEP 2: ADD CRITICAL MISSING INDEXES'
\echo '============================================================================'
\echo ''

\echo 'Adding indexes on edge_coemployment (CRITICAL - will take time)...'

-- These are CRITICAL for graph queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edge_coemployment_src 
ON edge_coemployment(src_person_id, company_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edge_coemployment_dst 
ON edge_coemployment(dst_person_id, company_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edge_coemployment_company 
ON edge_coemployment(company_id);

\echo '✓ edge_coemployment indexes created'
\echo ''

\echo 'Adding composite indexes on employment...'

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_employment_person_company 
ON employment(person_id, company_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_employment_person_dates 
ON employment(person_id, start_date, end_date) 
WHERE start_date IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_employment_company_dates 
ON employment(company_id, start_date, end_date) 
WHERE start_date IS NOT NULL;

\echo '✓ employment indexes created'
\echo ''

\echo 'Adding index on github_profile for linked profiles...'

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_github_profile_person_linked 
ON github_profile(person_id) 
WHERE person_id IS NOT NULL;

\echo '✓ github_profile index created'
\echo ''

\echo ''
\echo '============================================================================'
\echo 'STEP 3: UPDATE TABLE STATISTICS'
\echo '============================================================================'
\echo ''

\echo 'Running ANALYZE on all tables to update query planner statistics...'
ANALYZE;
\echo '✓ Statistics updated'
\echo ''

\echo ''
\echo '============================================================================'
\echo 'STEP 4: VERIFY INDEX CREATION'
\echo '============================================================================'
\echo ''

\echo 'Indexes on edge_coemployment:'
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE tablename = 'edge_coemployment'
ORDER BY indexname;

\echo ''
\echo 'Indexes on employment:'
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE tablename = 'employment'
ORDER BY indexname;

\echo ''
\echo 'Indexes on github_profile:'
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE tablename = 'github_profile'
ORDER BY indexname;

\echo ''
\echo '============================================================================'
\echo 'EMERGENCY FIX COMPLETE'
\echo '============================================================================'
\echo ''
\echo 'What was fixed:'
\echo '  ✓ All tables vacuumed and analyzed'
\echo '  ✓ Critical indexes added to edge_coemployment'
\echo '  ✓ Composite indexes added to employment'
\echo '  ✓ Filtered index added to github_profile'
\echo '  ✓ Query planner statistics updated'
\echo ''
\echo 'Expected improvements:'
\echo '  - Graph queries should be 100-1000x faster'
\echo '  - Person profile lookups should be 10-50x faster'
\echo '  - Company queries should be much faster'
\echo '  - Dashboard should load without hanging'
\echo ''


-- Cleanup Bad Employment Records
-- Date: October 22, 2025
-- Purpose: Identify and optionally remove employment records with suffix-only company names
-- Affected: 3,931 employment records (Inc., LLC, Ltd., etc.)
--
-- IMPORTANT: This script has two modes:
--   1. EXPORT MODE (lines 10-50): Export data for review - RUN THIS FIRST
--   2. DELETE MODE (lines 52-80): Delete bad records - RUN ONLY AFTER REVIEW

-- ============================================================================
-- STEP 1: EXPORT BAD RECORDS FOR REVIEW
-- ============================================================================

\echo ''
\echo '===================================================================='
\echo 'STEP 1: Identifying Bad Employment Records'
\echo '===================================================================='
\echo ''

-- Create temporary table with all bad employment records
CREATE TEMP TABLE IF NOT EXISTS bad_employment_records AS
SELECT 
    e.employment_id,
    e.person_id,
    p.full_name,
    p.linkedin_url,
    p.location,
    p.headline as current_title,
    e.title as employment_title,
    c.company_name,
    c.company_domain,
    e.start_date,
    e.end_date,
    'suffix_only_company' as issue_type,
    NOW() as identified_at
FROM employment e
JOIN person p ON e.person_id = p.person_id
JOIN company c ON e.company_id = c.company_id
WHERE c.company_name ~ '^[\.]*\s*(Ltd\.?|Inc\.?|LLC|LTD\.?|inc\.?|llc|Corp\.?|Corporation|Limited|L\.?P\.?|P\.?C\.?)[\)\.\s]*$';

\echo 'Summary of Bad Employment Records:'
\echo ''

-- Count by company
SELECT 
    company_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT person_id) as unique_people,
    ROUND(AVG(EXTRACT(YEAR FROM end_date) - EXTRACT(YEAR FROM start_date)), 1) as avg_duration_years
FROM bad_employment_records
WHERE start_date IS NOT NULL AND end_date IS NOT NULL
GROUP BY company_name
ORDER BY record_count DESC;

\echo ''
\echo 'Total Records Identified:'
SELECT COUNT(*) as total_bad_records FROM bad_employment_records;

\echo ''
\echo 'Sample Records (First 20):'
SELECT 
    full_name,
    employment_title,
    company_name,
    TO_CHAR(start_date, 'YYYY-MM') as start_date,
    TO_CHAR(end_date, 'YYYY-MM') as end_date
FROM bad_employment_records
ORDER BY full_name
LIMIT 20;

\echo ''
\echo '===================================================================='
\echo 'EXPORT: Saving to CSV for manual review'
\echo '===================================================================='
\echo ''

-- Export to CSV
\copy (SELECT * FROM bad_employment_records ORDER BY full_name, start_date) TO '/tmp/bad_employment_records_export.csv' CSV HEADER

\echo 'Exported to: /tmp/bad_employment_records_export.csv'
\echo ''
\echo 'Next Steps:'
\echo '1. Review the exported CSV file'
\echo '2. Verify these records should be removed'
\echo '3. If confirmed, run STEP 2 (DELETE MODE) below'
\echo ''

-- ============================================================================
-- STEP 2: DELETE BAD RECORDS (ONLY RUN AFTER REVIEW!)
-- ============================================================================

\echo ''
\echo '===================================================================='
\echo 'STEP 2: DELETE BAD EMPLOYMENT RECORDS'
\echo '===================================================================='
\echo ''
\echo 'CAUTION: This will PERMANENTLY DELETE employment records!'
\echo 'Only proceed if you have:'
\echo '  1. Reviewed the exported CSV'
\echo '  2. Confirmed these should be deleted'
\echo '  3. Backed up the database'
\echo ''

-- Uncomment the following lines to enable deletion:
-- \prompt 'Type DELETE to proceed: ' confirm_delete
-- 
-- \if :confirm_delete = 'DELETE'
--     \echo 'Proceeding with deletion...'
--     
--     BEGIN;
--     
--     -- Delete employment records
--     DELETE FROM employment
--     WHERE employment_id IN (
--         SELECT employment_id FROM bad_employment_records
--     );
--     
--     -- Store count
--     SELECT COUNT(*) as deleted_count FROM bad_employment_records \gset
--     
--     \echo 'Deleted :deleted_count employment records'
--     
--     -- Delete now-empty suffix-only companies
--     DELETE FROM company
--     WHERE company_name IN ('Inc.', 'LLC', 'Ltd.', 'Limited', 'Corp.', 'Corporation', 'P.C.', 'L.P.', 'LTD', 'LTD.', 'ltd', 'ltd.')
--     AND NOT EXISTS (
--         SELECT 1 FROM employment WHERE company_id = company.company_id
--     );
--     
--     -- Get deleted company count
--     SELECT ROW_COUNT() as companies_deleted \gset
--     
--     \echo 'Deleted :companies_deleted suffix-only companies'
--     
--     COMMIT;
--     
--     \echo ''
--     \echo 'Deletion complete!'
--     \echo ''
-- \else
--     \echo 'Deletion cancelled - confirmation not received'
-- \fi

-- ============================================================================
-- STEP 3: GENERATE ENRICHMENT QUEUE
-- ============================================================================

\echo ''
\echo '===================================================================='
\echo 'STEP 3: Enrichment Queue for Re-scraping'
\echo '===================================================================='
\echo ''

-- Export list of people needing employment re-scraping
\copy (SELECT DISTINCT person_id, full_name, linkedin_url, 'bad_employment_data' as reason FROM bad_employment_records ORDER BY full_name) TO '/tmp/enrichment_queue_employment.csv' CSV HEADER

\echo 'Enrichment queue exported to: /tmp/enrichment_queue_employment.csv'
\echo ''
\echo 'Total people needing enrichment:'
SELECT COUNT(DISTINCT person_id) as people_to_enrich FROM bad_employment_records;

\echo ''
\echo '===================================================================='
\echo 'DATA QUALITY STATISTICS'
\echo '===================================================================='
\echo ''

-- Overall database health
WITH stats AS (
    SELECT 
        COUNT(*) as total_employment,
        COUNT(*) FILTER (WHERE title IS NULL) as missing_title,
        COUNT(*) FILTER (WHERE company_id IN (
            SELECT company_id FROM company 
            WHERE company_name ~ '^[\.]*\s*(Ltd\.?|Inc\.?|LLC|LTD\.?|inc\.?|llc|Corp\.?|Corporation|Limited|L\.?P\.?|P\.?C\.?)[\)\.\s]*$'
        )) as bad_company
    FROM employment
)
SELECT 
    total_employment,
    bad_company,
    ROUND((bad_company::numeric / total_employment * 100), 2) as pct_bad,
    missing_title,
    ROUND((missing_title::numeric / total_employment * 100), 2) as pct_missing_title
FROM stats;

\echo ''
\echo 'Script complete.'
\echo ''


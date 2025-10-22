-- Delete Bad Employment Records (Safe Deletion)
-- Date: October 22, 2025
-- Purpose: Remove employment records with suffix-only company names
-- SAFE: Only deletes employment records, preserves all person data

BEGIN;

\echo ''
\echo '===================================================================='
\echo 'DELETING BAD EMPLOYMENT RECORDS - SAFE MODE'
\echo '===================================================================='
\echo ''

-- Create temp table with bad employment records
CREATE TEMP TABLE bad_employment_to_delete AS
SELECT 
    e.employment_id,
    e.person_id,
    p.full_name,
    p.linkedin_url,
    e.title,
    c.company_name,
    c.company_id,
    e.start_date,
    e.end_date
FROM employment e
JOIN person p ON e.person_id = p.person_id
JOIN company c ON e.company_id = c.company_id
WHERE c.company_name ~ '^[\.]*\s*(Ltd\.?|Inc\.?|LLC|LTD\.?|inc\.?|llc|Corp\.?|Corporation|Limited|L\.?P\.?|P\.?C\.?)[\)\.\s]*$';

\echo 'Records to be deleted:'
SELECT company_name, COUNT(*) as count
FROM bad_employment_to_delete
GROUP BY company_name
ORDER BY count DESC;

\echo ''
\echo 'Total employment records to delete:'
SELECT COUNT(*) FROM bad_employment_to_delete;

\echo ''
\echo 'People affected (will keep ALL their other data):'
SELECT COUNT(DISTINCT person_id) FROM bad_employment_to_delete;

\echo ''
\echo 'Sample of records being deleted:'
SELECT full_name, company_name, start_date, end_date
FROM bad_employment_to_delete
ORDER BY full_name
LIMIT 10;

\echo ''
\echo 'Proceeding with deletion...'
\echo ''

-- Delete the bad employment records
DELETE FROM employment
WHERE employment_id IN (
    SELECT employment_id FROM bad_employment_to_delete
);

\echo 'Deleted employment records:'
SELECT COUNT(*) as deleted_count FROM bad_employment_to_delete \gset
\echo :deleted_count

\echo ''
\echo 'Now deleting suffix-only companies (now empty)...'

-- Delete suffix-only companies that now have no employment records
DELETE FROM company
WHERE company_name IN ('Inc.', 'LLC', 'Ltd.', 'Limited', 'Corp.', 'Corporation', 'P.C.', 'L.P.', 'LTD', 'LTD.', 'ltd', 'ltd.')
AND NOT EXISTS (
    SELECT 1 FROM employment WHERE company_id = company.company_id
);

SELECT ROW_COUNT() as companies_deleted \gset
\echo 'Deleted companies: ':companies_deleted

\echo ''
\echo '===================================================================='
\echo 'VERIFICATION - Checking remaining data for affected people'
\echo '===================================================================='
\echo ''

-- Verify people still exist with their good data
\echo 'Verifying people still exist in database:'
SELECT COUNT(DISTINCT p.person_id) as people_still_exist
FROM person p
WHERE p.person_id IN (SELECT DISTINCT person_id FROM bad_employment_to_delete);

\echo ''
\echo 'Checking if affected people have OTHER good employment records:'
SELECT 
    COUNT(DISTINCT e.person_id) as people_with_other_jobs,
    COUNT(e.employment_id) as other_employment_records
FROM employment e
WHERE e.person_id IN (SELECT DISTINCT person_id FROM bad_employment_to_delete)
AND e.employment_id NOT IN (SELECT employment_id FROM bad_employment_to_delete);

\echo ''
\echo 'Checking other data preserved (emails, GitHub, education):'
SELECT 
    (SELECT COUNT(*) FROM person_email WHERE person_id IN (SELECT DISTINCT person_id FROM bad_employment_to_delete)) as emails_preserved,
    (SELECT COUNT(*) FROM github_profile WHERE person_id IN (SELECT DISTINCT person_id FROM bad_employment_to_delete)) as github_profiles_preserved,
    (SELECT COUNT(*) FROM education WHERE person_id IN (SELECT DISTINCT person_id FROM bad_employment_to_delete)) as education_records_preserved;

\echo ''
\echo '===================================================================='
\echo 'DELETION COMPLETE'
\echo '===================================================================='
\echo ''

COMMIT;

\echo 'Transaction committed successfully!'
\echo ''
\echo 'Summary:'
\echo '- Bad employment records deleted: ':deleted_count
\echo '- Suffix-only companies deleted: ':companies_deleted
\echo '- People records preserved: ALL'
\echo '- Other good data preserved: ALL (emails, GitHub, education, other jobs)'
\echo ''

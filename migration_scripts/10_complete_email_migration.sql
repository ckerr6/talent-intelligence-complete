-- ============================================================================
-- Complete Email Data Migration
-- Consolidates all emails into person_email table
-- Created: 2025-10-24
-- ============================================================================

-- Purpose: Migrate emails from github_profile.github_email to person_email table
-- to ensure all emails are in one centralized location

BEGIN;

-- Log migration start
INSERT INTO migration_log (migration_name, migration_phase, status, records_processed)
VALUES ('10_complete_email_migration', 'email_consolidation', 'started', 0);

-- ============================================================================
-- STEP 1: Migrate emails from github_profile to person_email
-- ============================================================================

INSERT INTO person_email (person_id, email, email_type, is_primary, source, verified)
SELECT 
    gp.person_id,
    gp.github_email,
    'unknown' as email_type,
    FALSE as is_primary,  -- Don't override existing primary emails
    'github_profile_migration' as source,
    FALSE as verified
FROM github_profile gp
WHERE gp.github_email IS NOT NULL 
  AND gp.github_email != ''
  AND gp.person_id IS NOT NULL
  AND NOT EXISTS (
    -- Only insert if this email doesn't already exist for this person
    SELECT 1 FROM person_email pe 
    WHERE pe.person_id = gp.person_id 
    AND LOWER(pe.email) = LOWER(gp.github_email)
  )
ON CONFLICT (person_id, lower(email)) DO NOTHING;

-- Get count of migrated records
WITH migration_count AS (
    SELECT COUNT(*) as migrated FROM person_email WHERE source = 'github_profile_migration'
)
UPDATE migration_log
SET 
    records_created = (SELECT migrated FROM migration_count),
    status = 'completed',
    completed_at = NOW()
WHERE migration_name = '10_complete_email_migration';

-- ============================================================================
-- STEP 2: Ensure people with multiple emails have one marked as primary
-- ============================================================================

-- For people with multiple emails but no primary, mark the first one as primary
WITH people_needing_primary AS (
    SELECT DISTINCT person_id
    FROM person_email
    GROUP BY person_id
    HAVING COUNT(*) > 1 AND SUM(CASE WHEN is_primary THEN 1 ELSE 0 END) = 0
),
first_email_per_person AS (
    SELECT DISTINCT ON (pe.person_id) 
        pe.email_id
    FROM person_email pe
    JOIN people_needing_primary pnp ON pe.person_id = pnp.person_id
    ORDER BY pe.person_id, pe.created_at ASC
)
UPDATE person_email
SET is_primary = TRUE
WHERE email_id IN (SELECT email_id FROM first_email_per_person);

-- ============================================================================
-- STEP 3: Generate summary report
-- ============================================================================

DO $$
DECLARE
    total_people INT;
    people_with_emails INT;
    total_email_records INT;
    github_emails_migrated INT;
    coverage_pct NUMERIC;
BEGIN
    SELECT COUNT(*) INTO total_people FROM person;
    SELECT COUNT(DISTINCT person_id) INTO people_with_emails FROM person_email;
    SELECT COUNT(*) INTO total_email_records FROM person_email;
    SELECT COUNT(*) INTO github_emails_migrated FROM person_email WHERE source = 'github_profile_migration';
    coverage_pct := ROUND(100.0 * people_with_emails / NULLIF(total_people, 0), 2);
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Email Migration Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total People: %', total_people;
    RAISE NOTICE 'People with Emails: % (%.2f%%)', people_with_emails, coverage_pct;
    RAISE NOTICE 'Total Email Records: %', total_email_records;
    RAISE NOTICE 'GitHub Emails Migrated: %', github_emails_migrated;
    RAISE NOTICE '========================================';
END $$;

-- Verify data quality
SELECT 
    'Email Migration Summary' as report,
    (SELECT COUNT(*) FROM person) as total_people,
    (SELECT COUNT(DISTINCT person_id) FROM person_email) as people_with_emails,
    (SELECT COUNT(*) FROM person_email) as total_email_records,
    (SELECT COUNT(*) FROM person_email WHERE is_primary) as primary_emails,
    (SELECT COUNT(*) FROM person_email WHERE email_type = 'work') as work_emails,
    (SELECT COUNT(*) FROM person_email WHERE email_type = 'personal') as personal_emails,
    (SELECT COUNT(*) FROM person_email WHERE email_type = 'unknown') as unknown_type_emails,
    ROUND(100.0 * (SELECT COUNT(DISTINCT person_id) FROM person_email) / 
          (SELECT COUNT(*) FROM person), 2) as email_coverage_percentage;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES (run these after migration to verify success)
-- ============================================================================

-- Check for duplicate emails per person
-- SELECT person_id, email, COUNT(*) as count
-- FROM person_email
-- GROUP BY person_id, lower(email)
-- HAVING COUNT(*) > 1;

-- Check people with multiple primary emails (should be 0)
-- SELECT person_id, COUNT(*) as primary_count
-- FROM person_email
-- WHERE is_primary = TRUE
-- GROUP BY person_id
-- HAVING COUNT(*) > 1;

-- Sample of migrated GitHub emails
-- SELECT p.full_name, pe.email, pe.source
-- FROM person_email pe
-- JOIN person p ON pe.person_id = p.person_id
-- WHERE pe.source = 'github_profile_migration'
-- LIMIT 10;


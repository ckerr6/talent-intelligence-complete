-- Enrichment Queue - Helpful Queries
-- Date: October 22, 2025
-- Purpose: Work with people flagged for employment data re-scraping

-- ============================================================================
-- VIEW QUEUE STATUS
-- ============================================================================

-- Quick overview
SELECT 
    reason,
    status,
    priority,
    COUNT(*) as count
FROM enrichment_queue
GROUP BY reason, status, priority
ORDER BY reason, priority DESC;

-- ============================================================================
-- GET NEXT BATCH FOR PROCESSING
-- ============================================================================

-- Get top 50 priority people to enrich
SELECT 
    eq.queue_id,
    eq.person_id::text,
    p.full_name,
    p.linkedin_url,
    p.headline,
    p.location,
    eq.priority,
    eq.metadata->>'has_other_employment' as has_other_jobs
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.reason = 'bad_employment_data_deleted'
  AND eq.status = 'pending'
ORDER BY eq.priority DESC, eq.created_at
LIMIT 50;

-- ============================================================================
-- MARK PEOPLE AS IN PROGRESS
-- ============================================================================

-- Update status for a specific person
-- UPDATE enrichment_queue
-- SET status = 'in_progress',
--     last_attempt = NOW(),
--     attempts = attempts + 1
-- WHERE queue_id = '<paste-queue-id-here>';

-- ============================================================================
-- MARK PEOPLE AS COMPLETED
-- ============================================================================

-- After successfully re-scraping employment data
-- UPDATE enrichment_queue
-- SET status = 'completed',
--     completed_at = NOW()
-- WHERE queue_id = '<paste-queue-id-here>';

-- ============================================================================
-- MARK PEOPLE AS FAILED (with error message)
-- ============================================================================

-- If enrichment fails
-- UPDATE enrichment_queue
-- SET status = 'failed',
--     error_message = 'LinkedIn profile not found'
-- WHERE queue_id = '<paste-queue-id-here>';

-- ============================================================================
-- RESET FAILED ATTEMPTS
-- ============================================================================

-- Reset failed enrichments to try again
-- UPDATE enrichment_queue
-- SET status = 'pending',
--     attempts = 0,
--     error_message = NULL
-- WHERE status = 'failed' 
--   AND reason = 'bad_employment_data_deleted';

-- ============================================================================
-- VIEW PEOPLE WITH HIGHEST PRIORITY
-- ============================================================================

-- People with job titles (most likely to find employment data)
SELECT 
    p.full_name,
    p.linkedin_url,
    p.headline as current_title,
    p.location,
    eq.priority,
    (SELECT COUNT(*) FROM employment WHERE person_id = p.person_id) as other_jobs_count
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.reason = 'bad_employment_data_deleted'
  AND eq.status = 'pending'
  AND eq.priority = 5
ORDER BY p.full_name
LIMIT 100;

-- ============================================================================
-- CHECK PROGRESS
-- ============================================================================

-- Overall progress tracking
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    ROUND(COUNT(*) FILTER (WHERE status = 'completed')::numeric / COUNT(*) * 100, 2) as pct_complete
FROM enrichment_queue
WHERE reason = 'bad_employment_data_deleted';

-- ============================================================================
-- EXPORT TO CSV FOR MANUAL REVIEW
-- ============================================================================

-- Export high-priority people for manual enrichment
\copy (SELECT p.full_name, p.linkedin_url, p.headline, p.location, eq.priority FROM enrichment_queue eq JOIN person p ON eq.person_id = p.person_id WHERE eq.reason = 'bad_employment_data_deleted' AND eq.priority >= 5 AND eq.status = 'pending' ORDER BY p.full_name LIMIT 100) TO '/tmp/enrichment_high_priority.csv' CSV HEADER;

-- ============================================================================
-- FIND PEOPLE WHO MIGHT BE EASY TO ENRICH
-- ============================================================================

-- People with other employment records (can use those for context)
SELECT 
    p.full_name,
    p.linkedin_url,
    p.headline,
    eq.priority,
    COUNT(e.employment_id) as other_jobs,
    STRING_AGG(DISTINCT c.company_name, ', ') as other_companies
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
LEFT JOIN employment e ON p.person_id = e.person_id
LEFT JOIN company c ON e.company_id = c.company_id
WHERE eq.reason = 'bad_employment_data_deleted'
  AND eq.status = 'pending'
GROUP BY eq.queue_id, p.person_id, p.full_name, p.linkedin_url, p.headline, eq.priority
HAVING COUNT(e.employment_id) > 0
ORDER BY COUNT(e.employment_id) DESC, eq.priority DESC
LIMIT 50;

-- ============================================================================
-- VIEW METADATA FOR A PERSON
-- ============================================================================

-- See what we know about a specific person
SELECT 
    p.full_name,
    p.linkedin_url,
    p.headline,
    p.location,
    p.followers_count,
    eq.priority,
    eq.status,
    eq.created_at,
    eq.attempts,
    eq.last_attempt,
    eq.error_message,
    eq.metadata
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.reason = 'bad_employment_data_deleted'
  AND p.full_name ILIKE '%name%'; -- Replace with search term

-- ============================================================================
-- SAMPLE QUERY FOR ENRICHMENT SCRIPT
-- ============================================================================

-- This is what your enrichment script would query
WITH next_batch AS (
    SELECT 
        eq.queue_id,
        eq.person_id,
        p.linkedin_url,
        p.full_name,
        eq.priority
    FROM enrichment_queue eq
    JOIN person p ON eq.person_id = p.person_id
    WHERE eq.reason = 'bad_employment_data_deleted'
      AND eq.status = 'pending'
    ORDER BY eq.priority DESC, eq.created_at
    LIMIT 10
)
SELECT * FROM next_batch;

-- Then in your script:
-- 1. Fetch this batch
-- 2. For each person:
--    a. Mark as 'in_progress'
--    b. Scrape LinkedIn
--    c. Update employment records
--    d. Mark as 'completed' (or 'failed' with error)
-- 3. Sleep/rate limit
-- 4. Repeat

-- ============================================================================
-- STATISTICS
-- ============================================================================

-- Enrichment attempts analysis
SELECT 
    attempts,
    status,
    COUNT(*) as count
FROM enrichment_queue
WHERE reason = 'bad_employment_data_deleted'
GROUP BY attempts, status
ORDER BY attempts, status;

-- Priority distribution
SELECT 
    priority,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) FILTER (WHERE status = 'completed') as completed
FROM enrichment_queue
WHERE reason = 'bad_employment_data_deleted'
GROUP BY priority
ORDER BY priority DESC;

-- ============================================================================
-- CLEANUP (IF NEEDED)
-- ============================================================================

-- Remove completed items after verification (optional)
-- DELETE FROM enrichment_queue
-- WHERE reason = 'bad_employment_data_deleted'
--   AND status = 'completed'
--   AND completed_at < NOW() - INTERVAL '30 days';


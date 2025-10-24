-- Enrichment Test Batch Selection
-- Select 15 random profiles from queue for testing
-- Date: 2025-10-24
-- Purpose: Get a diverse test batch for PhantomBuster MCP integration testing

-- ============================================================================
-- SELECT TEST BATCH (Random 15 profiles)
-- ============================================================================

SELECT 
    eq.queue_id,
    eq.person_id::text,
    p.full_name,
    p.linkedin_url,
    p.headline,
    p.location,
    eq.priority,
    eq.created_at,
    eq.metadata
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.status = 'pending'
ORDER BY RANDOM()  -- Random selection for diverse test
LIMIT 15;  -- Test with 15 profiles

-- ============================================================================
-- ALTERNATIVE: Select high-priority profiles first
-- ============================================================================

-- SELECT 
--     eq.queue_id,
--     eq.person_id::text,
--     p.full_name,
--     p.linkedin_url,
--     p.headline,
--     eq.priority,
--     eq.created_at
-- FROM enrichment_queue eq
-- JOIN person p ON eq.person_id = p.person_id
-- WHERE eq.status = 'pending'
-- ORDER BY eq.priority DESC, RANDOM()
-- LIMIT 15;

-- ============================================================================
-- COUNT BY PRIORITY (for test batch distribution analysis)
-- ============================================================================

SELECT 
    priority,
    COUNT(*) as available_count
FROM enrichment_queue
WHERE status = 'pending'
GROUP BY priority
ORDER BY priority DESC;


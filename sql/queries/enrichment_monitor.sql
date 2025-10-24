-- Enrichment Queue Monitoring Queries
-- Date: 2025-10-24
-- Purpose: Monitor PhantomBuster enrichment progress and status

-- ============================================================================
-- OVERALL QUEUE STATUS
-- ============================================================================

SELECT 
    status,
    priority,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(last_attempt) as last_processed,
    AVG(attempts) as avg_attempts
FROM enrichment_queue
GROUP BY status, priority
ORDER BY priority DESC, status;

-- ============================================================================
-- RECENT COMPLETIONS (Last 20)
-- ============================================================================

SELECT 
    p.full_name,
    p.linkedin_url,
    eq.status,
    eq.priority,
    eq.completed_at,
    eq.attempts,
    eq.created_at,
    (eq.completed_at - eq.created_at) as time_to_complete
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.status = 'completed'
ORDER BY eq.completed_at DESC
LIMIT 20;

-- ============================================================================
-- RECENT FAILURES (Last 20)
-- ============================================================================

SELECT 
    p.full_name,
    p.linkedin_url,
    eq.error_message,
    eq.attempts,
    eq.last_attempt,
    eq.priority
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.status = 'failed'
ORDER BY eq.last_attempt DESC
LIMIT 20;

-- ============================================================================
-- IN PROGRESS (Currently being processed)
-- ============================================================================

SELECT 
    p.full_name,
    p.linkedin_url,
    eq.priority,
    eq.attempts,
    eq.last_attempt,
    NOW() - eq.last_attempt as time_since_start
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.status = 'in_progress'
ORDER BY eq.last_attempt DESC;

-- ============================================================================
-- SUCCESS RATE SUMMARY
-- ============================================================================

SELECT 
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) as total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'completed') / 
        NULLIF(COUNT(*) FILTER (WHERE status IN ('completed', 'failed')), 0),
        2
    ) as success_rate_pct
FROM enrichment_queue;

-- ============================================================================
-- RECENT ACTIVITY (Last hour)
-- ============================================================================

SELECT 
    p.full_name,
    eq.status,
    eq.last_attempt,
    eq.attempts,
    eq.error_message
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.last_attempt > NOW() - INTERVAL '1 hour'
ORDER BY eq.last_attempt DESC;

-- ============================================================================
-- RETRY CANDIDATES (Failed but attempts < 3)
-- ============================================================================

SELECT 
    p.full_name,
    p.linkedin_url,
    eq.attempts,
    eq.error_message,
    eq.last_attempt
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.status = 'failed'
  AND eq.attempts < 3
ORDER BY eq.priority DESC, eq.last_attempt ASC
LIMIT 20;


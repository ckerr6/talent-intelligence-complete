-- Database Enrichment Summary Report
-- Generated after running enrichment scripts

SELECT '=== DATABASE ENRICHMENT SUMMARY ===' as report_section;

-- People and Email Coverage
SELECT 'PEOPLE & EMAIL COVERAGE' as section;
SELECT 
    'Total People' as metric, 
    COUNT(*)::text as value,
    'Baseline' as status
FROM person
UNION ALL
SELECT 
    'Total Emails', 
    COUNT(*)::text,
    'Current'
FROM person_email
UNION ALL
SELECT 
    'People with Emails', 
    COUNT(DISTINCT person_id)::text || ' (' || 
    ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text || 
    '%)',
    'Coverage'
FROM person_email;

-- Employment and Job Titles
SELECT 'EMPLOYMENT & JOB TITLES' as section;
SELECT 
    'Total Employment Records' as metric,
    COUNT(*)::text as value,
    'All Time' as status
FROM employment
UNION ALL
SELECT 
    'Current Jobs (Active)',
    COUNT(*)::text,
    'Active'
FROM employment WHERE end_date IS NULL
UNION ALL
SELECT 
    'Current Jobs with Titles',
    COUNT(*)::text || ' (' ||
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM employment WHERE end_date IS NULL) * 100, 2)::text ||
    '%)',
    'Coverage'
FROM employment WHERE end_date IS NULL AND title IS NOT NULL AND title != ''
UNION ALL
SELECT 
    'Historical Jobs',
    COUNT(*)::text,
    'Past'
FROM employment WHERE end_date IS NOT NULL
UNION ALL
SELECT 
    'Historical Jobs with Titles',
    COUNT(*)::text || ' (' ||
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM employment WHERE end_date IS NOT NULL) * 100, 2)::text ||
    '%)',
    'Coverage'
FROM employment WHERE end_date IS NOT NULL AND title IS NOT NULL AND title != '';

-- GitHub Profiles and Matching
SELECT 'GITHUB PROFILES & MATCHING' as section;
SELECT 
    'Total GitHub Profiles' as metric,
    COUNT(*)::text as value,
    'Available' as status
FROM github_profile
UNION ALL
SELECT 
    'GitHub Profiles with Emails',
    COUNT(*)::text || ' (' ||
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM github_profile) * 100, 2)::text ||
    '%)',
    'Have Email'
FROM github_profile WHERE github_email IS NOT NULL AND github_email != ''
UNION ALL
SELECT 
    'Enriched GitHub Profiles',
    COUNT(*)::text || ' (' ||
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM github_profile) * 100, 2)::text ||
    '%)',
    'API Enriched'
FROM github_profile WHERE followers > 0 OR public_repos > 0
UNION ALL
SELECT 
    'GitHub Profiles Linked to People',
    COUNT(*)::text || ' (' ||
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM github_profile) * 100, 2)::text ||
    '%)',
    'Matched'
FROM github_profile WHERE person_id IS NOT NULL
UNION ALL
SELECT 
    'People with GitHub Profiles',
    COUNT(DISTINCT person_id)::text || ' (' ||
    ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text ||
    '%)',
    'Coverage'
FROM github_profile WHERE person_id IS NOT NULL;

-- Companies
SELECT 'COMPANIES' as section;
SELECT 
    'Total Companies' as metric,
    COUNT(*)::text as value,
    'In Database' as status
FROM company;


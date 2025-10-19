#!/bin/bash
# Query companies with their candidate counts

DB="/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db"

echo "==================================================================="
echo "COMPANIES WITH MOST CANDIDATES"
echo "==================================================================="
echo ""

sqlite3 -header -column "$DB" "
SELECT 
    c.name,
    c.website,
    c.linkedin_url,
    COUNT(DISTINCT e.person_id) as candidate_count
FROM companies c
JOIN employment e ON c.company_id = e.company_id
WHERE e.is_current = 1
GROUP BY c.company_id
ORDER BY candidate_count DESC
LIMIT 20;
"

echo ""
echo "==================================================================="
echo "UNISWAP COMPANY PROFILE"
echo "==================================================================="
echo ""

sqlite3 -line "$DB" "
SELECT 
    c.*,
    COUNT(DISTINCT e.person_id) as total_candidates,
    (SELECT COUNT(*) FROM company_social_profiles WHERE company_id = c.company_id) as social_profiles_count
FROM companies c
LEFT JOIN employment e ON c.company_id = e.company_id
WHERE LOWER(c.name) LIKE '%uniswap%'
GROUP BY c.company_id;
"

echo ""
echo "==================================================================="
echo "UNISWAP EMPLOYEES WITH COMPLETE PROFILES"
echo "==================================================================="
echo ""

sqlite3 -header -column "$DB" "
SELECT 
    p.first_name,
    p.last_name,
    p.primary_email,
    e.title,
    sp_linkedin.profile_url as linkedin,
    sp_github.profile_url as github
FROM companies c
JOIN employment e ON c.company_id = e.company_id
JOIN people p ON e.person_id = p.person_id
LEFT JOIN social_profiles sp_linkedin ON p.person_id = sp_linkedin.person_id AND sp_linkedin.platform = 'linkedin'
LEFT JOIN social_profiles sp_github ON p.person_id = sp_github.person_id AND sp_github.platform = 'github'
WHERE LOWER(c.name) LIKE '%uniswap%'
    AND e.is_current = 1
ORDER BY p.last_name, p.first_name
LIMIT 20;
"

echo ""

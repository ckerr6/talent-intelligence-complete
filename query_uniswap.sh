#!/bin/bash
# Query for Uniswap employees with GitHub or Twitter accounts

DB="/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db"

echo "==================================================================="
echo "UNISWAP EMPLOYEES WITH GITHUB OR TWITTER ACCOUNTS"
echo "==================================================================="
echo ""

sqlite3 -header -column "$DB" "
SELECT 
    p.first_name,
    p.last_name,
    p.primary_email,
    e.title,
    sp_github.profile_url as github_url,
    sp_twitter.profile_url as twitter_url
FROM people p
JOIN employment e ON p.person_id = e.person_id
LEFT JOIN social_profiles sp_github 
    ON p.person_id = sp_github.person_id 
    AND sp_github.platform = 'github'
LEFT JOIN social_profiles sp_twitter 
    ON p.person_id = sp_twitter.person_id 
    AND sp_twitter.platform = 'twitter'
WHERE LOWER(e.company_name) LIKE '%uniswap%'
    AND e.is_current = 1
    AND (sp_github.profile_url IS NOT NULL OR sp_twitter.profile_url IS NOT NULL)
ORDER BY p.last_name, p.first_name;
"

echo ""
echo "==================================================================="
echo "SUMMARY"
echo "==================================================================="

sqlite3 "$DB" "
SELECT 
    COUNT(DISTINCT p.person_id) as total_count,
    SUM(CASE WHEN sp_github.profile_url IS NOT NULL THEN 1 ELSE 0 END) as with_github,
    SUM(CASE WHEN sp_twitter.profile_url IS NOT NULL THEN 1 ELSE 0 END) as with_twitter
FROM people p
JOIN employment e ON p.person_id = e.person_id
LEFT JOIN social_profiles sp_github 
    ON p.person_id = sp_github.person_id 
    AND sp_github.platform = 'github'
LEFT JOIN social_profiles sp_twitter 
    ON p.person_id = sp_twitter.person_id 
    AND sp_twitter.platform = 'twitter'
WHERE LOWER(e.company_name) LIKE '%uniswap%'
    AND e.is_current = 1
    AND (sp_github.profile_url IS NOT NULL OR sp_twitter.profile_url IS NOT NULL);
" | awk -F'|' '{print "Total people: " $1 "\nWith GitHub: " $2 "\nWith Twitter: " $3}'

echo ""

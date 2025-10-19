#!/bin/bash
# Review GitHub matches that need manual verification

DB="/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db"

echo "==================================================================="
echo "GITHUB MATCHES PENDING MANUAL REVIEW"
echo "==================================================================="
echo ""

echo "Total pending reviews:"
sqlite3 "$DB" "SELECT COUNT(*) FROM github_match_reviews WHERE status='pending';"

echo ""
echo "Top 20 matches to review:"
echo "-------------------------------------------------------------------"

sqlite3 -header -column "$DB" "
SELECT 
    r.review_id,
    gp.github_username,
    gp.github_name,
    gp.github_email,
    gp.github_company,
    p.first_name || ' ' || p.last_name as candidate_name,
    p.primary_email as candidate_email,
    r.match_confidence,
    r.match_reason
FROM github_match_reviews r
JOIN github_profiles gp ON r.github_profile_id = gp.github_profile_id
JOIN people p ON r.candidate_person_id = p.person_id
WHERE r.status = 'pending'
ORDER BY r.match_confidence DESC
LIMIT 20;
"

echo ""
echo "==================================================================="
echo "NEW CANDIDATES CREATED FROM GITHUB"
echo "==================================================================="
echo ""

sqlite3 -header -column "$DB" "
SELECT 
    p.person_id,
    p.first_name,
    p.last_name,
    p.primary_email,
    gp.github_username,
    gp.github_company,
    gp.followers,
    gp.public_repos
FROM people p
JOIN github_profiles gp ON p.person_id = gp.person_id
WHERE p.status = 'github_sourced'
ORDER BY gp.followers DESC
LIMIT 20;
"

echo ""
echo "==================================================================="
echo "ENRICHED EXISTING CANDIDATES"
echo "==================================================================="
echo ""

sqlite3 -header -column "$DB" "
SELECT 
    p.first_name,
    p.last_name,
    p.primary_email,
    gp.github_username,
    gp.followers,
    gp.public_repos,
    gp.num_contributions
FROM people p
JOIN github_profiles gp ON p.person_id = gp.person_id
WHERE p.status != 'github_sourced'
AND gp.match_confidence = 1.0
ORDER BY gp.followers DESC
LIMIT 20;
"

echo ""

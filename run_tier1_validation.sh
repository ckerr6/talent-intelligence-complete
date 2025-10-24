#!/bin/bash
# ABOUTME: Quick validation test suite for Tier 1 implementations
# ABOUTME: Runs key queries to verify skills, ecosystems, emails, and GitHub integration

set -e

echo "======================================================================="
echo "Tier 1 Validation Test Suite"
echo "======================================================================="
echo ""

DB="talent"
OUTPUT_FILE="tier1_validation_results_$(date +%Y%m%d_%H%M%S).txt"

echo "Database: $DB"
echo "Output: $OUTPUT_FILE"
echo ""

# Redirect all output to file and stdout
exec > >(tee -a "$OUTPUT_FILE")
exec 2>&1

echo "======================================================================="
echo "Test 1: Skills System"
echo "======================================================================="
echo ""

echo "Test 1.1: Solidity Developers (Top 10)"
psql -d $DB -c "
SELECT 
    p.full_name,
    p.location,
    ps.proficiency_score,
    ps.evidence_sources
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
WHERE s.skill_name = 'Solidity'
ORDER BY ps.proficiency_score DESC
LIMIT 10;
"
echo ""

echo "Test 1.2: Skills Coverage Stats"
psql -d $DB -c "
SELECT 
    COUNT(DISTINCT p.person_id) as total_people,
    COUNT(DISTINCT ps.person_id) as people_with_skills,
    ROUND(100.0 * COUNT(DISTINCT ps.person_id) / COUNT(DISTINCT p.person_id), 2) as coverage_pct,
    COUNT(ps.person_skills_id) as total_skill_records,
    ROUND(COUNT(ps.person_skills_id)::NUMERIC / NULLIF(COUNT(DISTINCT ps.person_id), 0), 2) as avg_skills_per_person
FROM person p
LEFT JOIN person_skills ps ON p.person_id = ps.person_id;
"
echo ""

echo "Test 1.3: Top 10 Skills by Popularity"
psql -d $DB -c "
SELECT 
    s.skill_name,
    s.category,
    COUNT(DISTINCT ps.person_id) as people_count
FROM skills s
LEFT JOIN person_skills ps ON s.skill_id = ps.skill_id
GROUP BY s.skill_id, s.skill_name, s.category
HAVING COUNT(DISTINCT ps.person_id) > 0
ORDER BY people_count DESC
LIMIT 10;
"
echo ""

echo "======================================================================="
echo "Test 2: Ecosystem Organization"
echo "======================================================================="
echo ""

echo "Test 2.1: Top Ecosystems by Developer Count"
psql -d $DB -c "
SELECT 
    ce.ecosystem_name,
    COUNT(DISTINCT pea.person_id) as developer_count,
    SUM(pea.contribution_count) as total_contributions
FROM crypto_ecosystem ce
LEFT JOIN person_ecosystem_activity pea ON ce.ecosystem_id = pea.ecosystem_id
GROUP BY ce.ecosystem_id, ce.ecosystem_name
HAVING COUNT(DISTINCT pea.person_id) > 0
ORDER BY developer_count DESC
LIMIT 10;
"
echo ""

echo "Test 2.2: Repository Ecosystem Coverage"
psql -d $DB -c "
SELECT 
    COUNT(*) as total_repos,
    COUNT(CASE WHEN ecosystem_ids IS NOT NULL AND array_length(ecosystem_ids, 1) > 0 
          THEN 1 END) as repos_with_ecosystems,
    ROUND(100.0 * COUNT(CASE WHEN ecosystem_ids IS NOT NULL AND array_length(ecosystem_ids, 1) > 0 
          THEN 1 END) / COUNT(*), 2) as coverage_pct
FROM github_repository;
"
echo ""

echo "======================================================================="
echo "Test 3: Email Management"
echo "======================================================================="
echo ""

echo "Test 3.1: Email Coverage"
psql -d $DB -c "
SELECT 
    COUNT(DISTINCT p.person_id) as total_people,
    COUNT(DISTINCT pe.person_id) as people_with_emails,
    ROUND(100.0 * COUNT(DISTINCT pe.person_id) / COUNT(DISTINCT p.person_id), 2) as coverage_pct,
    COUNT(pe.email_id) as total_email_records
FROM person p
LEFT JOIN person_email pe ON p.person_id = pe.person_id;
"
echo ""

echo "Test 3.2: Email Type Distribution"
psql -d $DB -c "
SELECT 
    email_type,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM person_email
GROUP BY email_type
ORDER BY count DESC;
"
echo ""

echo "======================================================================="
echo "Test 4: GitHub Integration"
echo "======================================================================="
echo ""

echo "Test 4.1: GitHub Profile Linkage"
psql -d $DB -c "
SELECT 
    COUNT(*) as total_profiles,
    COUNT(person_id) as linked_profiles,
    COUNT(*) - COUNT(person_id) as unlinked_profiles,
    ROUND(100.0 * COUNT(person_id) / COUNT(*), 2) as linkage_pct
FROM github_profile;
"
echo ""

echo "Test 4.2: People with GitHub Coverage"
psql -d $DB -c "
SELECT 
    COUNT(DISTINCT p.person_id) as total_people,
    COUNT(DISTINCT gp.person_id) as people_with_github,
    ROUND(100.0 * COUNT(DISTINCT gp.person_id) / COUNT(DISTINCT p.person_id), 2) as coverage_pct
FROM person p
LEFT JOIN github_profile gp ON p.person_id = gp.person_id;
"
echo ""

echo "======================================================================="
echo "Test 5: Cross-Functional Query (Recruiter Use Case)"
echo "======================================================================="
echo ""

echo "Test 5.1: Find Senior Solidity Developers with GitHub (Top 5)"
psql -d $DB -c "
SELECT 
    p.full_name,
    p.location,
    ps.proficiency_score as solidity_proficiency,
    gp.github_username,
    gp.followers,
    COUNT(DISTINCT pe.email) as email_count
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
LEFT JOIN github_profile gp ON p.person_id = gp.person_id
LEFT JOIN person_email pe ON p.person_id = pe.person_id
WHERE s.skill_name = 'Solidity'
AND ps.proficiency_score >= 70
GROUP BY p.person_id, p.full_name, p.location, ps.proficiency_score, 
         gp.github_username, gp.followers
ORDER BY ps.proficiency_score DESC
LIMIT 5;
"
echo ""

echo "======================================================================="
echo "Test 6: Data Quality"
echo "======================================================================="
echo ""

echo "Test 6.1: Check for Duplicate Person-Skills"
psql -d $DB -c "
SELECT COUNT(*) as duplicate_count
FROM (
    SELECT person_id, skill_id, COUNT(*) as count
    FROM person_skills
    GROUP BY person_id, skill_id
    HAVING COUNT(*) > 1
) duplicates;
"
echo ""

echo "Test 6.2: Check for Missing Critical Data"
psql -d $DB -c "
SELECT 
    'person' as table_name,
    COUNT(*) as total,
    COUNT(CASE WHEN full_name IS NULL OR full_name = '' THEN 1 END) as missing_names
FROM person
UNION ALL
SELECT 
    'person_skills',
    COUNT(*),
    COUNT(CASE WHEN proficiency_score IS NULL THEN 1 END)
FROM person_skills
UNION ALL
SELECT 
    'person_email',
    COUNT(*),
    COUNT(CASE WHEN email IS NULL OR email = '' THEN 1 END)
FROM person_email;
"
echo ""

echo "======================================================================="
echo "Summary"
echo "======================================================================="
echo ""
echo "✅ Validation tests complete!"
echo "📄 Full results saved to: $OUTPUT_FILE"
echo ""
echo "Key Metrics to Check:"
echo "  - Skills coverage should be > 60%"
echo "  - Email coverage should be > 15%"
echo "  - GitHub linkage should be 100%"
echo "  - Ecosystem repo coverage should be > 90%"
echo "  - No duplicate person-skills records"
echo ""
echo "Review the output above and check $OUTPUT_FILE for details."
echo ""


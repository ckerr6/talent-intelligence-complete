#!/bin/bash
# Diagnose duplicate employment records

DB="/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db"

echo "==================================================================="
echo "DUPLICATE EMPLOYMENT RECORDS ANALYSIS"
echo "==================================================================="
echo ""

echo "1. Total employment records vs unique people:"
sqlite3 "$DB" "
SELECT 
    (SELECT COUNT(*) FROM employment) as total_employment_records,
    (SELECT COUNT(DISTINCT person_id) FROM employment) as unique_people_in_employment,
    (SELECT COUNT(*) FROM employment) - (SELECT COUNT(DISTINCT person_id) FROM employment) as duplicate_records;
"

echo ""
echo "2. People with multiple employment records at SAME company:"
sqlite3 -header -column "$DB" "
SELECT 
    p.first_name,
    p.last_name,
    p.primary_email,
    e.company_name,
    COUNT(*) as record_count
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE e.is_current = 1
GROUP BY p.person_id, e.company_name
HAVING COUNT(*) > 1
ORDER BY record_count DESC
LIMIT 20;
"

echo ""
echo "3. Marvin Ammori's employment records (example):"
sqlite3 -header -column "$DB" "
SELECT 
    e.employment_id,
    e.person_id,
    e.company_name,
    e.title,
    e.is_current,
    e.company_id
FROM employment e
JOIN people p ON e.person_id = p.person_id
WHERE p.primary_email = 'ammorim@gmail.com'
ORDER BY e.employment_id;
"

echo ""
echo "4. Distribution of duplicate employment records:"
sqlite3 -header -column "$DB" "
SELECT 
    duplicate_count,
    COUNT(*) as people_with_this_many_duplicates
FROM (
    SELECT person_id, company_name, COUNT(*) as duplicate_count
    FROM employment
    WHERE is_current = 1
    GROUP BY person_id, company_name
    HAVING COUNT(*) > 1
)
GROUP BY duplicate_count
ORDER BY duplicate_count;
"

echo ""

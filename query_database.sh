#!/bin/bash
# ABOUTME: Interactive database query helper
# ABOUTME: Makes it easy to explore your data without writing SQL

DB="talent_intelligence.db"

if [ ! -f "$DB" ]; then
    echo "❌ Database not found: $DB"
    echo "Run ./RUN_ME.sh first to build the database"
    exit 1
fi

echo "============================================================"
echo "🔍 Talent Intelligence Database Explorer"
echo "============================================================"
echo ""
echo "What would you like to do?"
echo ""
echo "1. Show database statistics"
echo "2. Find candidates by company"
echo "3. Find candidates by email domain"
echo "4. Show high-quality candidates"
echo "5. Get complete profile by email"
echo "6. Search by name"
echo "7. Show all LinkedIn profiles"
echo "8. Export candidates to CSV"
echo "9. Open SQLite interactive shell"
echo "0. Exit"
echo ""
read -p "Enter choice (0-9): " choice

case $choice in
    1)
        echo ""
        echo "=== DATABASE STATISTICS ==="
        sqlite3 $DB <<EOF
.mode column
.headers on
SELECT 
    (SELECT COUNT(*) FROM people) as total_people,
    (SELECT COUNT(*) FROM people WHERE primary_email IS NOT NULL) as with_email,
    (SELECT COUNT(*) FROM social_profiles WHERE platform='linkedin') as with_linkedin,
    (SELECT COUNT(*) FROM social_profiles WHERE platform='github') as with_github,
    (SELECT COUNT(*) FROM employment WHERE is_current=1) as with_current_job,
    (SELECT ROUND(AVG(data_quality_score), 2) FROM people) as avg_quality_score;
EOF
        ;;
    
    2)
        echo ""
        read -p "Enter company name (or part of it): " company
        echo ""
        echo "=== CANDIDATES AT $company ==="
        sqlite3 $DB <<EOF
.mode column
.headers on
.width 15 15 30 25
SELECT 
    p.first_name,
    p.last_name,
    p.primary_email,
    e.title
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE LOWER(e.company_name) LIKE LOWER('%$company%')
AND e.is_current = 1
LIMIT 50;
EOF
        ;;
    
    3)
        echo ""
        read -p "Enter email domain (e.g., uniswap.org): " domain
        echo ""
        echo "=== CANDIDATES WITH @$domain EMAILS ==="
        sqlite3 $DB <<EOF
.mode column
.headers on
.width 15 15 30
SELECT 
    first_name,
    last_name,
    primary_email
FROM people
WHERE primary_email LIKE '%@$domain'
LIMIT 50;
EOF
        ;;
    
    4)
        echo ""
        echo "=== HIGH-QUALITY CANDIDATES (Score > 0.7) ==="
        sqlite3 $DB <<EOF
.mode column
.headers on
.width 15 15 30 8
SELECT 
    first_name,
    last_name,
    primary_email,
    data_quality_score as quality
FROM people
WHERE data_quality_score > 0.7
ORDER BY data_quality_score DESC
LIMIT 50;
EOF
        ;;
    
    5)
        echo ""
        read -p "Enter email address: " email
        echo ""
        echo "=== COMPLETE PROFILE ==="
        sqlite3 $DB <<EOF
.mode line
SELECT 
    p.first_name || ' ' || p.last_name as name,
    p.primary_email,
    p.location,
    e.company_name as current_company,
    e.title as current_title,
    (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='linkedin') as linkedin,
    (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='github') as github,
    (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='twitter') as twitter,
    p.data_quality_score,
    p.created_at
FROM people p
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
WHERE p.primary_email = '$email';
EOF
        ;;
    
    6)
        echo ""
        read -p "Enter first name: " first
        read -p "Enter last name: " last
        echo ""
        echo "=== SEARCH RESULTS ==="
        sqlite3 $DB <<EOF
.mode column
.headers on
.width 15 15 30 25
SELECT 
    p.first_name,
    p.last_name,
    p.primary_email,
    e.company_name
FROM people p
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
WHERE LOWER(p.first_name) LIKE LOWER('%$first%')
AND LOWER(p.last_name) LIKE LOWER('%$last%')
LIMIT 50;
EOF
        ;;
    
    7)
        echo ""
        echo "=== ALL LINKEDIN PROFILES ==="
        sqlite3 $DB <<EOF
.mode column
.headers on
.width 15 15 50
SELECT 
    p.first_name,
    p.last_name,
    sp.profile_url
FROM people p
JOIN social_profiles sp ON p.person_id = sp.person_id
WHERE sp.platform = 'linkedin'
LIMIT 100;
EOF
        ;;
    
    8)
        echo ""
        read -p "Enter output filename (e.g., candidates.csv): " filename
        echo ""
        echo "Exporting to $filename..."
        sqlite3 -header -csv $DB "SELECT 
            p.first_name,
            p.last_name,
            p.primary_email,
            p.location,
            e.company_name as current_company,
            e.title as current_title,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='linkedin') as linkedin_url,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='github') as github_url,
            p.data_quality_score
        FROM people p
        LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1;" > "$filename"
        echo "✅ Exported to $filename"
        ;;
    
    9)
        echo ""
        echo "Opening SQLite shell..."
        echo "Useful commands:"
        echo "  .tables          - List all tables"
        echo "  .schema people   - Show table structure"
        echo "  .quit            - Exit"
        echo ""
        sqlite3 $DB
        ;;
    
    0)
        echo "Goodbye!"
        exit 0
        ;;
    
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "============================================================"

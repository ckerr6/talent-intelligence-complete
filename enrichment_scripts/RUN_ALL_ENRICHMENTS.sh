#!/bin/bash

# Master script to run all database enrichments
# This addresses the high-priority recommendations from the database audit

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "  DATABASE ENRICHMENT - HIGH PRIORITY IMPROVEMENTS"
echo "================================================================================"
echo ""
echo "This will perform 3 major enrichments:"
echo "  1. Import SQLite people → Boost email coverage from 3% to 45%"
echo "  2. Enrich job titles → Fix 0.48% title coverage to 99%+"
echo "  3. Improve GitHub matching → Match profiles by email + name"
echo ""
echo "PostgreSQL Database: talent @ localhost:5432"
echo "SQLite Database: ../talent_intelligence.db"
echo ""
echo "================================================================================"
echo ""

# Pre-flight checks
echo "🔍 Pre-flight checks..."
echo ""

# Check PostgreSQL connection
if ! psql -d talent -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Cannot connect to PostgreSQL database 'talent'"
    echo "   Please ensure PostgreSQL is running and you have access"
    exit 1
fi
echo "✅ PostgreSQL connection OK"

# Check SQLite database exists
if [ ! -f "../talent_intelligence.db" ]; then
    echo "❌ SQLite database not found: ../talent_intelligence.db"
    exit 1
fi
echo "✅ SQLite database found"

# Check Python dependencies
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "❌ psycopg2 not installed. Run: pip install psycopg2-binary"
    exit 1
fi
echo "✅ Python dependencies OK"

echo ""
echo "================================================================================"
echo "  Phase 1: Import SQLite People & Emails"
echo "================================================================================"
echo ""
echo "Current state:"
psql -d talent -c "
SELECT 
    (SELECT COUNT(*) FROM person) as total_people,
    (SELECT COUNT(*) FROM person_email) as total_emails,
    (SELECT COUNT(DISTINCT person_id) FROM person_email) as people_with_emails,
    ROUND((SELECT COUNT(DISTINCT person_id)::numeric FROM person_email) / (SELECT COUNT(*)::numeric FROM person) * 100, 2) as email_coverage_pct
" -t

echo ""
echo "This will import ~15,350 people from SQLite (those not already in PostgreSQL)"
echo "Expected result: Email coverage will increase from 3% to ~45%"
echo ""
read -p "Proceed with SQLite import? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Skipping SQLite import"
else
    echo "Starting SQLite import..."
    python3 01_import_sqlite_people.py \
        --sqlite-db ../talent_intelligence.db \
        --pg-host localhost \
        --pg-port 5432 \
        --pg-db talent
    
    if [ $? -ne 0 ]; then
        echo "❌ SQLite import failed"
        exit 1
    fi
    
    echo "✅ SQLite import complete"
fi

echo ""
echo "================================================================================"
echo "  Phase 2: Enrich Job Titles"
echo "================================================================================"
echo ""
echo "Current state:"
psql -d talent -c "
SELECT 
    COUNT(*) as total_employment,
    COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as has_title,
    ROUND(COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as title_coverage_pct
FROM employment
" -t

echo ""
echo "This will extract job titles from person.headline field"
echo "Expected result: Title coverage will increase from 0.48% to 90%+"
echo ""
read -p "Proceed with job title enrichment? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Skipping job title enrichment"
else
    echo "Starting job title enrichment..."
    python3 02_enrich_job_titles.py \
        --pg-host localhost \
        --pg-port 5432 \
        --pg-db talent
    
    if [ $? -ne 0 ]; then
        echo "❌ Job title enrichment failed"
        exit 1
    fi
    
    echo "✅ Job title enrichment complete"
fi

echo ""
echo "================================================================================"
echo "  Phase 3: Improve GitHub Matching & Extract Emails"
echo "================================================================================"
echo ""
echo "Current state:"
psql -d talent -c "
SELECT 
    (SELECT COUNT(*) FROM github_profile) as total_github_profiles,
    (SELECT COUNT(*) FROM github_profile WHERE person_id IS NOT NULL) as linked_profiles,
    ROUND((SELECT COUNT(*)::numeric FROM github_profile WHERE person_id IS NOT NULL) / (SELECT COUNT(*)::numeric FROM github_profile) * 100, 2) as linkage_pct,
    (SELECT COUNT(*) FROM github_profile WHERE github_email IS NOT NULL) as profiles_with_email
" -t

echo ""
echo "This will:"
echo "  • Extract 5,000 emails from GitHub profiles"
echo "  • Match unlinked GitHub profiles to people by email"
echo "  • Match by name + company (conservative, high accuracy)"
echo ""
read -p "Proceed with GitHub matching enrichment? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Skipping GitHub matching enrichment"
else
    echo "Starting GitHub matching enrichment..."
    python3 03_improve_github_matching_and_emails.py \
        --pg-host localhost \
        --pg-port 5432 \
        --pg-db talent
    
    if [ $? -ne 0 ]; then
        echo "❌ GitHub matching enrichment failed"
        exit 1
    fi
    
    echo "✅ GitHub matching enrichment complete"
fi

echo ""
echo "================================================================================"
echo "  ENRICHMENT COMPLETE - FINAL STATE"
echo "================================================================================"
echo ""

# Show final statistics
psql -d talent -c "
SELECT 'People' as metric, COUNT(*)::text as value FROM person
UNION ALL
SELECT 'Emails', COUNT(*)::text FROM person_email
UNION ALL
SELECT 'People with Emails', 
    COUNT(DISTINCT person_id)::text || ' (' || 
    ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text || 
    '%)' 
FROM person_email
UNION ALL
SELECT 'Employment Records', COUNT(*)::text FROM employment
UNION ALL
SELECT 'Employment with Titles',
    COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END)::text || ' (' ||
    ROUND(COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END)::numeric / COUNT(*) * 100, 2)::text ||
    '%)'
FROM employment
UNION ALL
SELECT 'GitHub Profiles', COUNT(*)::text FROM github_profile
UNION ALL
SELECT 'GitHub Linked to People',
    COUNT(*)::text || ' (' ||
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM github_profile) * 100, 2)::text ||
    '%)'
FROM github_profile WHERE person_id IS NOT NULL
UNION ALL
SELECT 'People with GitHub',
    COUNT(DISTINCT person_id)::text || ' (' ||
    ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text ||
    '%)'
FROM github_profile WHERE person_id IS NOT NULL
" -t

echo ""
echo "================================================================================"
echo "✅ ALL ENRICHMENTS COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Review the results above"
echo "  2. Run: psql -d talent"
echo "  3. Test queries with enriched data"
echo "  4. Run updated database analysis: psql -d talent -f comprehensive_analysis.sql"
echo ""
echo "================================================================================"


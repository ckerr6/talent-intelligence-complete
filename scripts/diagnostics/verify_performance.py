#!/usr/bin/env python3
# ABOUTME: Verify performance improvements after emergency fix
# ABOUTME: Tests query speeds on critical operations

import psycopg2
import psycopg2.extras
import os
import time

def log(message):
    """Log with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def test_query(cursor, name, query, params=None):
    """Test a query and log timing"""
    log(f"Testing: {name}...")
    start = time.time()
    cursor.execute(query, params or ())
    result = cursor.fetchall()
    elapsed = time.time() - start
    
    status = "✓"
    if elapsed > 5:
        status = "🔴 SLOW"
    elif elapsed > 1:
        status = "⚠️"
    
    log(f"  {status} {elapsed*1000:.2f}ms - {len(result)} results")
    return elapsed

log("=" * 80)
log("PERFORMANCE VERIFICATION AFTER EMERGENCY FIX")
log("=" * 80)
log("")

conn = psycopg2.connect(
    dbname='talent',
    user=os.environ.get('PGUSER', os.environ.get('USER')),
    host=os.environ.get('PGHOST', 'localhost'),
    port=os.environ.get('PGPORT', '5432')
)
conn.cursor_factory = psycopg2.extras.RealDictCursor
cursor = conn.cursor()
log("✓ Connected to database")
log("")

# Get a sample person for testing
cursor.execute("SELECT person_id FROM person LIMIT 1")
person_id = cursor.fetchone()['person_id']

# Get a sample company for testing
cursor.execute("""
    SELECT company_id 
    FROM employment 
    GROUP BY company_id 
    ORDER BY COUNT(*) DESC 
    LIMIT 1
""")
company_id = cursor.fetchone()['company_id']

log("=" * 80)
log("TEST 1: BASIC TABLE COUNTS")
log("=" * 80)
log("")

test_query(cursor, "COUNT person", "SELECT COUNT(*) as count FROM person")
test_query(cursor, "COUNT github_profile", "SELECT COUNT(*) as count FROM github_profile")
test_query(cursor, "COUNT edge_coemployment", "SELECT COUNT(*) as count FROM edge_coemployment")
test_query(cursor, "COUNT employment", "SELECT COUNT(*) as count FROM employment")

log("")
log("=" * 80)
log("TEST 2: PERSON PROFILE LOOKUP (with emails + employment)")
log("=" * 80)
log("")

test_query(cursor, "Get person basic info", """
    SELECT person_id, full_name, linkedin_url, location, headline
    FROM person
    WHERE person_id = %s
""", (person_id,))

test_query(cursor, "Get person emails", """
    SELECT email, email_type, is_primary
    FROM person_email
    WHERE person_id = %s
""", (person_id,))

test_query(cursor, "Get person employment history", """
    SELECT e.title, e.start_date, e.end_date, c.company_name
    FROM employment e
    LEFT JOIN company c ON e.company_id = c.company_id
    WHERE e.person_id = %s
    ORDER BY e.start_date DESC
    LIMIT 10
""", (person_id,))

log("")
log("=" * 80)
log("TEST 3: GRAPH QUERIES (THE CRITICAL TEST)")
log("=" * 80)
log("")

test_query(cursor, "Get coworkers count for person", """
    SELECT COUNT(DISTINCT 
        CASE 
            WHEN src_person_id = %s THEN dst_person_id
            ELSE src_person_id
        END
    ) as count
    FROM edge_coemployment
    WHERE src_person_id = %s OR dst_person_id = %s
""", (person_id, person_id, person_id))

test_query(cursor, "Get coworkers with details", """
    WITH coworker_edges AS (
        SELECT 
            CASE 
                WHEN src_person_id = %s THEN dst_person_id
                ELSE src_person_id
            END as coworker_id,
            company_id,
            overlap_months
        FROM edge_coemployment
        WHERE src_person_id = %s OR dst_person_id = %s
        LIMIT 50
    )
    SELECT 
        p.person_id,
        p.full_name,
        p.location,
        c.company_name,
        ce.overlap_months
    FROM coworker_edges ce
    JOIN person p ON p.person_id = ce.coworker_id
    LEFT JOIN company c ON c.company_id = ce.company_id
    ORDER BY ce.overlap_months DESC
""", (person_id, person_id, person_id))

test_query(cursor, "Get company network edges", """
    SELECT 
        src_person_id,
        dst_person_id,
        overlap_months
    FROM edge_coemployment
    WHERE company_id = %s
    LIMIT 500
""", (company_id,))

log("")
log("=" * 80)
log("TEST 4: COMPLEX QUERIES")
log("=" * 80)
log("")

test_query(cursor, "Search people by company", """
    SELECT DISTINCT
        p.person_id,
        p.full_name,
        p.location
    FROM person p
    JOIN employment e ON p.person_id = e.person_id
    JOIN company c ON e.company_id = c.company_id
    WHERE c.company_name ILIKE %s
    LIMIT 50
""", ('%Uniswap%',))

test_query(cursor, "Find people with GitHub profiles", """
    SELECT 
        p.person_id,
        p.full_name,
        gp.github_username,
        gp.followers
    FROM person p
    JOIN github_profile gp ON p.person_id = gp.person_id
    ORDER BY gp.followers DESC
    LIMIT 50
""")

test_query(cursor, "Get employment with date ranges", """
    SELECT 
        p.full_name,
        c.company_name,
        e.title,
        e.start_date,
        e.end_date
    FROM employment e
    JOIN person p ON e.person_id = p.person_id
    JOIN company c ON e.company_id = c.company_id
    WHERE e.start_date > '2020-01-01'
    ORDER BY e.start_date DESC
    LIMIT 100
""")

conn.close()

log("")
log("=" * 80)
log("PERFORMANCE VERIFICATION COMPLETE")
log("=" * 80)
log("")
log("Summary:")
log("  - All queries should complete in < 1 second")
log("  - Graph queries should be DRAMATICALLY faster than before")
log("  - If any queries show 🔴 SLOW or ⚠️ warnings, further optimization needed")
log("")


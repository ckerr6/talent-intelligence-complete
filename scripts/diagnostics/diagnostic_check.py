#!/usr/bin/env python3
# ABOUTME: Diagnostic script to check actual database state
# ABOUTME: Gets source of truth for all counts and performance metrics

import psycopg2
import psycopg2.extras
import os
import time
import sys

def log(message):
    """Log with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def log_query(query_name):
    """Log start of query"""
    log(f"Starting: {query_name}...")

def log_result(query_name, elapsed, result=None):
    """Log query completion"""
    msg = f"✓ {query_name} completed in {elapsed:.2f}s"
    if result:
        msg += f" - {result}"
    log(msg)

log("=" * 80)
log("ACTUAL DATABASE STATE - SOURCE OF TRUTH")
log("=" * 80)
log("")

log("Connecting to PostgreSQL database 'talent'...")
try:
    conn = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432'),
        connect_timeout=10
    )
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    cursor = conn.cursor()
    log("✓ Connected successfully")
except Exception as e:
    log(f"✗ Connection failed: {e}")
    sys.exit(1)

log("")
log("=" * 80)
log("COUNTING CORE TABLES")
log("=" * 80)
log("")

# Total counts
log_query("COUNT person")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM person")
total_people = cursor.fetchone()['count']
log_result("COUNT person", time.time() - start, f"{total_people:,} people")
print(f"Total People: {total_people:,}")

log_query("COUNT company")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM company")
total_companies = cursor.fetchone()['count']
log_result("COUNT company", time.time() - start, f"{total_companies:,} companies")
print(f"Total Companies: {total_companies:,}")

log_query("COUNT employment")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM employment")
total_employment = cursor.fetchone()['count']
log_result("COUNT employment", time.time() - start, f"{total_employment:,} records")
print(f"Total Employment Records: {total_employment:,}")

log("")
log("=" * 80)
log("GITHUB PROFILE ANALYSIS")
log("=" * 80)
log("")

# GitHub profiles - TOTAL
log_query("COUNT github_profile (total)")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM github_profile")
total_github = cursor.fetchone()['count']
log_result("COUNT github_profile", time.time() - start, f"{total_github:,} profiles")
print(f"Total GitHub Profiles in DB: {total_github:,}")

# GitHub profiles - LINKED to people
log_query("COUNT github_profile (linked)")
start = time.time()
cursor.execute("""
    SELECT COUNT(*) as count 
    FROM github_profile 
    WHERE person_id IS NOT NULL
""")
linked_github = cursor.fetchone()['count']
log_result("COUNT linked profiles", time.time() - start, f"{linked_github:,} linked")
print(f"GitHub Profiles LINKED to People: {linked_github:,}")

# GitHub profiles - ORPHANED
log_query("COUNT github_profile (orphaned)")
start = time.time()
cursor.execute("""
    SELECT COUNT(*) as count 
    FROM github_profile 
    WHERE person_id IS NULL
""")
orphaned_github = cursor.fetchone()['count']
log_result("COUNT orphaned profiles", time.time() - start, f"{orphaned_github:,} orphaned")
print(f"GitHub Profiles ORPHANED (not linked): {orphaned_github:,}")

if total_github > 0:
    print(f"Linkage Rate: {(linked_github/total_github*100):.2f}%")

log("")
log("=" * 80)
log("EMAIL ANALYSIS")
log("=" * 80)
log("")

log_query("COUNT person_email")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM person_email")
total_emails = cursor.fetchone()['count']
log_result("COUNT person_email", time.time() - start, f"{total_emails:,} emails")
print(f"Total Email Records: {total_emails:,}")

log_query("COUNT DISTINCT person_id in person_email")
start = time.time()
cursor.execute("SELECT COUNT(DISTINCT person_id) as count FROM person_email")
people_with_email = cursor.fetchone()['count']
log_result("COUNT people with emails", time.time() - start, f"{people_with_email:,} people")
print(f"People with Emails: {people_with_email:,}")
if total_people > 0:
    print(f"Email Coverage: {(people_with_email/total_people*100):.2f}%")

log("")
log("=" * 80)
log("GRAPH TABLE ANALYSIS - ⚠️ THIS MAY BE SLOW")
log("=" * 80)
log("")

log_query("COUNT edge_coemployment - THIS IS THE CRITICAL TEST")
log("⚠️  If this hangs for >30 seconds, we have a major performance problem")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
total_edges = cursor.fetchone()['count']
elapsed = time.time() - start
log_result("COUNT edge_coemployment", elapsed, f"{total_edges:,} edges")
if elapsed > 30:
    log("🔴 CRITICAL: Graph table count took >30 seconds!")
elif elapsed > 5:
    log("⚠️  WARNING: Graph table count took >5 seconds")
print(f"Total Graph Edges: {total_edges:,}")

log_query("Get edge_coemployment table sizes")
start = time.time()
cursor.execute("""
    SELECT 
        pg_size_pretty(pg_total_relation_size('edge_coemployment')) as total_size,
        pg_size_pretty(pg_table_size('edge_coemployment')) as table_size,
        pg_size_pretty(pg_indexes_size('edge_coemployment')) as index_size
""")
sizes = cursor.fetchone()
log_result("Get table sizes", time.time() - start)
print(f"Total Size: {sizes['total_size']}")
print(f"Table Size: {sizes['table_size']}")
print(f"Index Size: {sizes['index_size']}")

log("")
log("=" * 80)
log("TABLE SIZES - ALL TABLES")
log("=" * 80)
log("")

log_query("Get all table sizes")
start = time.time()
cursor.execute("""
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
        pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as table_size,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    LIMIT 15
""")
log_result("Get all table sizes", time.time() - start)

print(f"{'Table':<30} {'Total Size':<15} {'Table Size':<15} {'Index Size':<15}")
print("-" * 75)
for row in cursor.fetchall():
    print(f"{row['tablename']:<30} {row['total_size']:<15} {row['table_size']:<15} {row['index_size']:<15}")

log("")
log("=" * 80)
log("INDEXES ON GITHUB_PROFILE")
log("=" * 80)
log("")

log_query("Check indexes on github_profile")
start = time.time()
cursor.execute("""
    SELECT 
        indexname,
        indexdef
    FROM pg_indexes
    WHERE tablename = 'github_profile'
    ORDER BY indexname
""")

indexes = cursor.fetchall()
log_result("Check github_profile indexes", time.time() - start, f"{len(indexes)} indexes found")
if indexes:
    for row in indexes:
        print(f"{row['indexname']}:")
        print(f"  {row['indexdef']}")
        print()
else:
    print("⚠️  NO INDEXES ON GITHUB_PROFILE!")

log("")
log("=" * 80)
log("INDEXES ON EDGE_COEMPLOYMENT - CRITICAL CHECK")
log("=" * 80)
log("")

log_query("Check indexes on edge_coemployment")
start = time.time()
cursor.execute("""
    SELECT 
        indexname,
        indexdef
    FROM pg_indexes
    WHERE tablename = 'edge_coemployment'
    ORDER BY indexname
""")

indexes = cursor.fetchall()
log_result("Check edge_coemployment indexes", time.time() - start, f"{len(indexes)} indexes found")
if indexes:
    for row in indexes:
        print(f"{row['indexname']}:")
        print(f"  {row['indexdef']}")
        print()
else:
    log("🔴 CRITICAL: NO INDEXES ON EDGE_COEMPLOYMENT TABLE!")
    log("This is definitely causing your performance problems!")
    print("⚠️  NO INDEXES ON EDGE_COEMPLOYMENT TABLE!")
    print("This is likely causing your performance problems.")
    print()

log("")
log("=" * 80)
log("GITHUB REPOSITORIES")
log("=" * 80)
log("")

log_query("COUNT github_repository")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM github_repository")
total_repos = cursor.fetchone()['count']
log_result("COUNT github_repository", time.time() - start, f"{total_repos:,} repos")
print(f"Total GitHub Repositories: {total_repos:,}")

log_query("COUNT github_contribution")
start = time.time()
cursor.execute("SELECT COUNT(*) as count FROM github_contribution")
total_contributions = cursor.fetchone()['count']
log_result("COUNT github_contribution", time.time() - start, f"{total_contributions:,} contributions")
print(f"Total GitHub Contributions: {total_contributions:,}")

log("")
log("=" * 80)
log("QUERY PERFORMANCE TEST - Person Lookup")
log("=" * 80)
log("")

# Test a simple person query
log_query("Simple person query (LIMIT 1)")
start = time.time()
cursor.execute("SELECT person_id, full_name FROM person LIMIT 1")
result = cursor.fetchone()
elapsed = time.time() - start
log_result("Simple person query", elapsed, f"{elapsed*1000:.2f}ms")
print(f"Simple person query: {elapsed*1000:.2f}ms")

if result:
    person_id = result['person_id']
    
    # Test getting emails
    log_query("Email lookup for person")
    start = time.time()
    cursor.execute("SELECT * FROM person_email WHERE person_id = %s", (person_id,))
    emails = cursor.fetchall()
    elapsed = time.time() - start
    log_result("Email lookup", elapsed, f"{elapsed*1000:.2f}ms, {len(emails)} emails")
    print(f"Email lookup: {elapsed*1000:.2f}ms")
    
    # Test getting employment
    log_query("Employment lookup for person")
    start = time.time()
    cursor.execute("""
        SELECT e.*, c.company_name 
        FROM employment e 
        LEFT JOIN company c ON e.company_id = c.company_id 
        WHERE e.person_id = %s 
        LIMIT 10
    """, (person_id,))
    jobs = cursor.fetchall()
    elapsed = time.time() - start
    log_result("Employment lookup", elapsed, f"{elapsed*1000:.2f}ms, {len(jobs)} jobs")
    print(f"Employment lookup: {elapsed*1000:.2f}ms")
    
    # Test getting coworkers (DANGEROUS - might hang)
    log("")
    log("🔴 CRITICAL TEST: Graph query for coworkers - THIS MAY HANG")
    log("Setting 60 second timeout on this query...")
    
    try:
        # Set statement timeout to 60 seconds
        cursor.execute("SET statement_timeout = '60s'")
        
        log_query("Graph query (coworkers count)")
        start = time.time()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM edge_coemployment
            WHERE src_person_id = %s OR dst_person_id = %s
        """, (person_id, person_id))
        result = cursor.fetchone()
        elapsed = time.time() - start
        log_result("Graph query", elapsed, f"{elapsed*1000:.2f}ms - {result['count']} coworkers")
        print(f"Graph query (count only): {elapsed*1000:.2f}ms - Found {result['count']} coworkers")
        
        if elapsed > 10.0:
            log("🔴 CRITICAL: Graph query took > 10 seconds. Major performance bottleneck!")
        elif elapsed > 1.0:
            log("⚠️  WARNING: Graph query took > 1 second. Performance issue!")
            
        # Reset timeout
        cursor.execute("SET statement_timeout = 0")
            
    except Exception as e:
        log(f"🔴 CRITICAL: Graph query failed or timed out: {e}")
        print(f"⚠️  Graph query failed or timed out: {e}")
        # Reset timeout
        try:
            cursor.execute("SET statement_timeout = 0")
        except:
            pass

conn.close()
log("Database connection closed")

log("")
log("=" * 80)
log("DIAGNOSTIC COMPLETE")
log("=" * 80)


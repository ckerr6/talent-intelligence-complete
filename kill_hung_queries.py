#!/usr/bin/env python3
# ABOUTME: Kill hung queries blocking database operations
# ABOUTME: Finds and terminates long-running idle transactions and stuck queries

import psycopg2
import psycopg2.extras
import os
import time

def log(message):
    """Log with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

log("=" * 80)
log("KILLING HUNG QUERIES - EMERGENCY FIX")
log("=" * 80)
log("")

log("Connecting to PostgreSQL...")
conn = psycopg2.connect(
    dbname='talent',
    user=os.environ.get('PGUSER', os.environ.get('USER')),
    host=os.environ.get('PGHOST', 'localhost'),
    port=os.environ.get('PGPORT', '5432'),
    connect_timeout=10
)
conn.cursor_factory = psycopg2.extras.RealDictCursor
conn.autocommit = True
cursor = conn.cursor()
log("✓ Connected")
log("")

# Find queries to kill
log("=" * 80)
log("FINDING QUERIES TO KILL")
log("=" * 80)
log("")

cursor.execute("""
    SELECT 
        pid,
        usename,
        application_name,
        state,
        query_start,
        NOW() - query_start as duration,
        LEFT(query, 150) as query_snippet
    FROM pg_stat_activity
    WHERE datname = 'talent'
        AND pid != pg_backend_pid()
        AND (
            -- Idle in transaction for more than 5 minutes
            (state = 'idle in transaction' AND NOW() - query_start > INTERVAL '5 minutes')
            OR
            -- Active query running for more than 1 hour
            (state = 'active' AND NOW() - query_start > INTERVAL '1 hour')
        )
    ORDER BY query_start
""")

queries_to_kill = cursor.fetchall()

if not queries_to_kill:
    log("✓ No hung queries found")
else:
    log(f"Found {len(queries_to_kill)} queries to kill:")
    log("")
    
    for q in queries_to_kill:
        log(f"PID {q['pid']}:")
        log(f"  User: {q['usename']}")
        log(f"  State: {q['state']}")
        log(f"  Duration: {q['duration']}")
        log(f"  Query: {q['query_snippet']}")
        log("")
    
    log("=" * 80)
    log("KILLING QUERIES")
    log("=" * 80)
    log("")
    
    killed_count = 0
    failed_count = 0
    
    for q in queries_to_kill:
        try:
            log(f"Killing PID {q['pid']}...")
            cursor.execute("SELECT pg_terminate_backend(%s)", (q['pid'],))
            result = cursor.fetchone()
            if result and result['pg_terminate_backend']:
                log(f"  ✓ Killed PID {q['pid']}")
                killed_count += 1
            else:
                log(f"  ✗ Failed to kill PID {q['pid']}")
                failed_count += 1
        except Exception as e:
            log(f"  ✗ Error killing PID {q['pid']}: {e}")
            failed_count += 1
    
    log("")
    log(f"Results: {killed_count} killed, {failed_count} failed")

log("")
log("=" * 80)
log("CHECKING REMAINING ACTIVE QUERIES")
log("=" * 80)
log("")

cursor.execute("""
    SELECT COUNT(*) as count
    FROM pg_stat_activity
    WHERE datname = 'talent'
        AND state != 'idle'
        AND pid != pg_backend_pid()
""")

remaining = cursor.fetchone()
log(f"Remaining active queries: {remaining['count']}")

if remaining['count'] > 10:
    log("⚠️  Still have many active queries. May need to investigate further.")

log("")
log("=" * 80)
log("QUICK DATABASE CHECK")
log("=" * 80)
log("")

# Try a quick count now that locks should be released
try:
    log("Testing person table count...")
    start = time.time()
    cursor.execute("SELECT COUNT(*) as count FROM person")
    person_count = cursor.fetchone()['count']
    elapsed = time.time() - start
    log(f"  ✓ {person_count:,} people ({elapsed:.2f}s)")
    
    log("Testing github_profile table count...")
    cursor.execute("SET statement_timeout = '30s'")
    start = time.time()
    cursor.execute("SELECT COUNT(*) as count FROM github_profile")
    github_count = cursor.fetchone()['count']
    elapsed = time.time() - start
    cursor.execute("SET statement_timeout = 0")
    log(f"  ✓ {github_count:,} GitHub profiles ({elapsed:.2f}s)")
    
    if elapsed > 5:
        log(f"  ⚠️  Still slow ({elapsed:.2f}s) - table needs VACUUM ANALYZE")
    
except Exception as e:
    log(f"  ✗ Still having issues: {e}")
    log("  The table likely needs VACUUM ANALYZE")

conn.close()

log("")
log("=" * 80)
log("CLEANUP COMPLETE")
log("=" * 80)
log("")
log("NEXT STEPS:")
log("1. Run VACUUM ANALYZE on github_profile table")
log("2. Add missing indexes")
log("3. Check what caused those hung queries")


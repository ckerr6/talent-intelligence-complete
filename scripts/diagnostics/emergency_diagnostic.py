#!/usr/bin/env python3
# ABOUTME: Emergency diagnostic for stuck github_profile table
# ABOUTME: Checks for locks, bloat, and active queries

import psycopg2
import psycopg2.extras
import os
import time

def log(message):
    """Log with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

log("=" * 80)
log("EMERGENCY DIAGNOSTIC - GITHUB_PROFILE TABLE")
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
conn.autocommit = True  # Important for killing queries
cursor = conn.cursor()
log("✓ Connected")
log("")

# Check for active queries
log("=" * 80)
log("CHECKING FOR ACTIVE/BLOCKING QUERIES")
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
        LEFT(query, 100) as query_snippet
    FROM pg_stat_activity
    WHERE datname = 'talent'
        AND state != 'idle'
        AND pid != pg_backend_pid()
    ORDER BY query_start
""")

active_queries = cursor.fetchall()
if active_queries:
    log(f"Found {len(active_queries)} active queries:")
    for q in active_queries:
        log(f"  PID {q['pid']}: {q['state']} for {q['duration']} - {q['query_snippet']}")
        if 'github_profile' in q['query_snippet'].lower():
            log(f"  ⚠️  This query is touching github_profile!")
else:
    log("No other active queries found")

log("")

# Check for locks on github_profile
log("=" * 80)
log("CHECKING FOR LOCKS ON GITHUB_PROFILE")
log("=" * 80)
log("")

cursor.execute("""
    SELECT 
        l.pid,
        l.mode,
        l.granted,
        a.usename,
        a.query_start,
        NOW() - a.query_start as duration,
        LEFT(a.query, 100) as query_snippet
    FROM pg_locks l
    JOIN pg_stat_activity a ON l.pid = a.pid
    WHERE l.relation = 'github_profile'::regclass
    ORDER BY l.granted DESC, a.query_start
""")

locks = cursor.fetchall()
if locks:
    log(f"Found {len(locks)} locks on github_profile:")
    for lock in locks:
        granted = "✓ GRANTED" if lock['granted'] else "⏳ WAITING"
        log(f"  PID {lock['pid']}: {lock['mode']} - {granted} - {lock['duration']}")
        log(f"    Query: {lock['query_snippet']}")
else:
    log("No locks on github_profile")

log("")

# Check table stats and bloat
log("=" * 80)
log("TABLE STATISTICS")
log("=" * 80)
log("")

cursor.execute("""
    SELECT 
        relname,
        n_live_tup as live_rows,
        n_dead_tup as dead_rows,
        last_vacuum,
        last_autovacuum,
        last_analyze,
        last_autoanalyze
    FROM pg_stat_user_tables
    WHERE relname = 'github_profile'
""")

stats = cursor.fetchone()
if stats:
    log(f"Table: {stats['relname']}")
    log(f"  Live rows (approximate): {stats['live_rows']:,}")
    log(f"  Dead rows: {stats['dead_rows']:,}")
    if stats['dead_rows'] > stats['live_rows'] * 0.2:
        log(f"  ⚠️  HIGH DEAD ROW COUNT - Table needs VACUUM!")
    log(f"  Last vacuum: {stats['last_vacuum']}")
    log(f"  Last autovacuum: {stats['last_autovacuum']}")
    log(f"  Last analyze: {stats['last_analyze']}")
    log(f"  Last autoanalyze: {stats['last_autoanalyze']}")
else:
    log("No stats found for github_profile")

log("")

# Check actual table size
log("=" * 80)
log("TABLE SIZE")
log("=" * 80)
log("")

cursor.execute("""
    SELECT 
        pg_size_pretty(pg_total_relation_size('github_profile')) as total_size,
        pg_size_pretty(pg_table_size('github_profile')) as table_size,
        pg_size_pretty(pg_indexes_size('github_profile')) as index_size
""")

sizes = cursor.fetchone()
log(f"Total size: {sizes['total_size']}")
log(f"Table size: {sizes['table_size']}")
log(f"Index size: {sizes['index_size']}")

log("")

# Try to get row count using pg_class estimate (FAST)
log("=" * 80)
log("ESTIMATED ROW COUNT (from pg_class - FAST)")
log("=" * 80)
log("")

cursor.execute("""
    SELECT reltuples::bigint as estimate
    FROM pg_class
    WHERE relname = 'github_profile'
""")

estimate = cursor.fetchone()
if estimate:
    log(f"Estimated rows: {estimate['estimate']:,}")
    log("")
    log("Note: This is an estimate based on last ANALYZE")
    log("If you just did a large import, this might be inaccurate")

log("")

# Check if autovacuum is running
log("=" * 80)
log("CHECKING FOR AUTOVACUUM/VACUUM")
log("=" * 80)
log("")

cursor.execute("""
    SELECT 
        pid,
        query_start,
        NOW() - query_start as duration,
        query
    FROM pg_stat_activity
    WHERE query LIKE '%VACUUM%'
        OR query LIKE '%ANALYZE%'
""")

vacuum_queries = cursor.fetchall()
if vacuum_queries:
    log(f"Found {len(vacuum_queries)} vacuum/analyze operations:")
    for vq in vacuum_queries:
        log(f"  PID {vq['pid']}: Running for {vq['duration']}")
        log(f"    {vq['query']}")
else:
    log("No vacuum/analyze operations running")

log("")

# Now try an actual COUNT with a timeout
log("=" * 80)
log("ATTEMPTING ACTUAL COUNT (with 30 second timeout)")
log("=" * 80)
log("")

try:
    cursor.execute("SET statement_timeout = '30s'")
    log("Starting COUNT(*) on github_profile...")
    start = time.time()
    
    cursor.execute("SELECT COUNT(*) as count FROM github_profile")
    result = cursor.fetchone()
    elapsed = time.time() - start
    
    log(f"✓ COUNT completed in {elapsed:.2f}s")
    log(f"ACTUAL ROW COUNT: {result['count']:,}")
    
    cursor.execute("SET statement_timeout = 0")
    
except Exception as e:
    elapsed = time.time() - start
    log(f"✗ COUNT failed after {elapsed:.2f}s: {e}")
    log("")
    log("DIAGNOSIS: The github_profile table is severely degraded")
    log("This likely happened because:")
    log("  1. Large batch insert last night without VACUUM/ANALYZE")
    log("  2. Table bloat from many updates/deletes")
    log("  3. Missing or corrupted indexes")
    
    try:
        cursor.execute("SET statement_timeout = 0")
    except:
        pass

conn.close()
log("")
log("=" * 80)
log("EMERGENCY DIAGNOSTIC COMPLETE")
log("=" * 80)


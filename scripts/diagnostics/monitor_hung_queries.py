#!/usr/bin/env python3
# ABOUTME: Monitor for hung queries and alert/kill them automatically
# ABOUTME: Run periodically to prevent database lockups

import psycopg2
import psycopg2.extras
import os
import time
from datetime import datetime

def log(message):
    """Log with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def check_for_hung_queries(kill_threshold_minutes=60, warn_threshold_minutes=10):
    """
    Check for hung queries and optionally kill them
    
    Args:
        kill_threshold_minutes: Kill queries running longer than this
        warn_threshold_minutes: Warn about queries running longer than this
    """
    log("=" * 80)
    log("HUNG QUERY MONITOR")
    log("=" * 80)
    log("")
    
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
    
    # Check for active queries
    cursor.execute("""
        SELECT 
            pid,
            usename,
            application_name,
            state,
            query_start,
            NOW() - query_start as duration,
            EXTRACT(EPOCH FROM (NOW() - query_start))/60 as duration_minutes,
            LEFT(query, 100) as query_snippet
        FROM pg_stat_activity
        WHERE datname = 'talent'
            AND pid != pg_backend_pid()
            AND state != 'idle'
        ORDER BY query_start
    """)
    
    active_queries = cursor.fetchall()
    
    if not active_queries:
        log("✓ No active queries")
        conn.close()
        return
    
    log(f"Found {len(active_queries)} active queries")
    log("")
    
    # Categorize queries
    to_kill = []
    to_warn = []
    normal = []
    
    for q in active_queries:
        duration_min = q['duration_minutes']
        if duration_min >= kill_threshold_minutes:
            to_kill.append(q)
        elif duration_min >= warn_threshold_minutes:
            to_warn.append(q)
        else:
            normal.append(q)
    
    # Report
    if to_kill:
        log(f"🔴 CRITICAL: {len(to_kill)} queries need to be killed (>{kill_threshold_minutes} min):")
        for q in to_kill:
            log(f"  PID {q['pid']}: {q['state']} for {q['duration']} - {q['query_snippet']}")
        log("")
    
    if to_warn:
        log(f"⚠️  WARNING: {len(to_warn)} queries running long (>{warn_threshold_minutes} min):")
        for q in to_warn:
            log(f"  PID {q['pid']}: {q['state']} for {q['duration']} - {q['query_snippet']}")
        log("")
    
    if normal:
        log(f"✓ {len(normal)} queries running normally (<{warn_threshold_minutes} min)")
        log("")
    
    # Kill hung queries
    if to_kill:
        log("Killing hung queries...")
        killed = 0
        for q in to_kill:
            try:
                cursor.execute("SELECT pg_terminate_backend(%s)", (q['pid'],))
                result = cursor.fetchone()
                if result and result['pg_terminate_backend']:
                    log(f"  ✓ Killed PID {q['pid']}")
                    killed += 1
                else:
                    log(f"  ✗ Failed to kill PID {q['pid']}")
            except Exception as e:
                log(f"  ✗ Error killing PID {q['pid']}: {e}")
        
        log(f"Killed {killed} of {len(to_kill)} hung queries")
        log("")
    
    # Check connection count
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM pg_stat_activity
        WHERE datname = 'talent'
    """)
    total_connections = cursor.fetchone()['count']
    
    log(f"Total connections to 'talent' database: {total_connections}")
    
    # Check max connections
    cursor.execute("SHOW max_connections")
    max_conn = cursor.fetchone()['max_connections']
    usage_pct = (total_connections / int(max_conn)) * 100
    
    if usage_pct > 80:
        log(f"⚠️  WARNING: Using {usage_pct:.1f}% of max connections ({max_conn})")
    else:
        log(f"✓ Connection usage: {usage_pct:.1f}% of {max_conn}")
    
    conn.close()
    
    log("")
    log("=" * 80)
    log("MONITOR COMPLETE")
    log("=" * 80)
    
    return {
        'active': len(active_queries),
        'to_kill': len(to_kill),
        'to_warn': len(to_warn),
        'normal': len(normal),
        'killed': killed if to_kill else 0
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor and kill hung database queries')
    parser.add_argument('--kill-after', type=int, default=60, 
                        help='Kill queries running longer than N minutes (default: 60)')
    parser.add_argument('--warn-after', type=int, default=10,
                        help='Warn about queries running longer than N minutes (default: 10)')
    parser.add_argument('--loop', action='store_true',
                        help='Run continuously every 5 minutes')
    parser.add_argument('--interval', type=int, default=300,
                        help='Seconds between checks when looping (default: 300)')
    
    args = parser.parse_args()
    
    if args.loop:
        log(f"Starting continuous monitoring (checking every {args.interval}s)")
        log(f"Kill threshold: {args.kill_after} minutes")
        log(f"Warn threshold: {args.warn_after} minutes")
        log("")
        
        try:
            while True:
                check_for_hung_queries(args.kill_after, args.warn_after)
                log(f"Sleeping for {args.interval} seconds...")
                log("")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            log("\nMonitoring stopped by user")
    else:
        check_for_hung_queries(args.kill_after, args.warn_after)


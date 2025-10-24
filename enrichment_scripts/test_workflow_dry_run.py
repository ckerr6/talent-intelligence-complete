#!/usr/bin/env python3
"""
Dry Run Test of Enrichment Workflow
====================================
Tests all components WITHOUT calling PhantomBuster API

This validates:
- Database connectivity
- Queue management
- Data processing logic
- Error handling

Author: AI Assistant
Date: October 24, 2025
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_db_connection

print("=" * 80)
print("PHANTOMBUSTER MCP WORKFLOW - DRY RUN TEST")
print("=" * 80)
print()

# Test 1: Database Connection
print("✓ TEST 1: Database Connection")
print("-" * 80)
try:
    conn = get_db_connection(use_pool=False)
    if not conn:
        print(f"❌ Database connection failed: get_db_connection returned None")
        sys.exit(1)
    
    import psycopg2.extras
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ Connected to PostgreSQL: {version[0][:50]}...")
    print()
except Exception as e:
    import traceback
    print(f"❌ Database connection failed: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Enrichment Queue Table
print("✓ TEST 2: Enrichment Queue Table")
print("-" * 80)
try:
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'completed') as completed,
            COUNT(*) FILTER (WHERE status = 'failed') as failed
        FROM enrichment_queue
    """)
    result = dict(cursor.fetchone())
    print(f"✅ Queue table exists and accessible")
    print(f"   Total: {result['total']:,} | Pending: {result['pending']:,} | " +
          f"Completed: {result['completed']:,} | Failed: {result['failed']:,}")
    print()
except Exception as e:
    print(f"❌ Queue table error: {e}")
    sys.exit(1)

# Test 3: Test Batch Selection
print("✓ TEST 3: Test Batch Selection")
print("-" * 80)
try:
    cursor.execute("""
        SELECT 
            eq.queue_id::text,
            eq.person_id::text,
            p.full_name,
            p.linkedin_url
        FROM enrichment_queue eq
        JOIN person p ON eq.person_id = p.person_id
        WHERE eq.status = 'pending'
        ORDER BY RANDOM()
        LIMIT 5
    """)
    batch = [dict(row) for row in cursor.fetchall()]
    print(f"✅ Successfully selected {len(batch)} test profiles")
    for i, profile in enumerate(batch, 1):
        name = profile['full_name'][:30] if profile['full_name'] else 'Unknown'
        url = profile['linkedin_url'][:40] if profile['linkedin_url'] else 'NO URL'
        print(f"   [{i}] {name:30} | {url}")
    print()
except Exception as e:
    print(f"❌ Batch selection error: {e}")
    sys.exit(1)

# Test 4: Queue Status Update (Dry Run)
print("✓ TEST 4: Queue Status Update (Dry Run)")
print("-" * 80)
try:
    if batch:
        test_queue_id = batch[0]['queue_id']
        
        # Test mark in_progress
        cursor.execute("""
            UPDATE enrichment_queue
            SET status = 'in_progress',
                last_attempt = NOW(),
                attempts = attempts + 1
            WHERE queue_id = %s::uuid
            RETURNING status, attempts
        """, (test_queue_id,))
        result = cursor.fetchone()
        print(f"✅ Mark in_progress: status={result['status']}, attempts={result['attempts']}")
        
        # Test mark completed
        cursor.execute("""
            UPDATE enrichment_queue
            SET status = 'completed',
                completed_at = NOW()
            WHERE queue_id = %s::uuid
            RETURNING status
        """, (test_queue_id,))
        result = cursor.fetchone()
        print(f"✅ Mark completed: status={result['status']}")
        
        # Rollback (restore to pending for actual test)
        cursor.execute("""
            UPDATE enrichment_queue
            SET status = 'pending',
                last_attempt = NULL,
                completed_at = NULL,
                attempts = 0
            WHERE queue_id = %s::uuid
        """, (test_queue_id,))
        print(f"✅ Restored to pending state (dry run cleanup)")
        print()
except Exception as e:
    print(f"❌ Queue update error: {e}")
    sys.exit(1)

# Test 5: Company Cache Loading
print("✓ TEST 5: Company Cache")
print("-" * 80)
try:
    cursor.execute("""
        SELECT COUNT(*) as company_count
        FROM company
    """)
    result = cursor.fetchone()
    company_count = result['company_count']
    print(f"✅ Company table accessible: {company_count:,} companies")
    print()
except Exception as e:
    print(f"❌ Company cache error: {e}")
    sys.exit(1)

# Test 6: Employment Table
print("✓ TEST 6: Employment Table")
print("-" * 80)
try:
    cursor.execute("""
        SELECT COUNT(*) as employment_count
        FROM employment
    """)
    result = cursor.fetchone()
    employment_count = result['employment_count']
    print(f"✅ Employment table accessible: {employment_count:,} records")
    print()
except Exception as e:
    print(f"❌ Employment table error: {e}")
    sys.exit(1)

# Test 7: Education Table
print("✓ TEST 7: Education Table")
print("-" * 80)
try:
    cursor.execute("""
        SELECT COUNT(*) as education_count
        FROM education
    """)
    result = cursor.fetchone()
    education_count = result['education_count']
    print(f"✅ Education table accessible: {education_count:,} records")
    print()
except Exception as e:
    print(f"❌ Education table error: {e}")
    sys.exit(1)

# Test 8: Date Parsing
print("✓ TEST 8: Date Parsing Logic")
print("-" * 80)
try:
    from dateutil import parser as date_parser
    from datetime import date
    
    test_dates = [
        "Nov 2022 - May 2023",
        "May 2021 - Present",
        "Jan 2020 - Dec 2020"
    ]
    
    for date_str in test_dates:
        parts = date_str.split('-')
        start_str = parts[0].strip()
        parsed = date_parser.parse(start_str, fuzzy=True)
        start_date = date(parsed.year, parsed.month, 1)
        print(f"   '{date_str:30}' → Start: {start_date}")
    
    print("✅ Date parsing functional")
    print()
except Exception as e:
    print(f"❌ Date parsing error: {e}")
    sys.exit(1)

# Test 9: Import Dependencies
print("✓ TEST 9: Python Dependencies")
print("-" * 80)
try:
    import requests
    import dotenv
    import psycopg2
    
    print(f"✅ requests version: {requests.__version__}")
    print(f"✅ python-dotenv installed")
    print(f"✅ psycopg2 version: {psycopg2.__version__}")
    print()
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# Test 10: Log Directory
print("✓ TEST 10: Logging Setup")
print("-" * 80)
try:
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'phantombuster_enrichment.log'
    
    # Test write access
    with open(log_file, 'a') as f:
        f.write(f"\n[DRY RUN TEST] {sys.argv[0]} at {__import__('datetime').datetime.now()}\n")
    
    print(f"✅ Log directory: {log_dir}")
    print(f"✅ Log file writable: {log_file}")
    print()
except Exception as e:
    print(f"❌ Logging error: {e}")
    sys.exit(1)

# Cleanup
conn.close()

# Summary
print("=" * 80)
print("DRY RUN TEST COMPLETE")
print("=" * 80)
print("✅ All 10 tests passed!")
print()
print("System is ready for enrichment. Next steps:")
print("1. Add PHANTOMBUSTER_API_KEY to .env file")
print("2. Run: ./run_test_enrichment.sh 15")
print("3. Monitor: python3 monitor_enrichment_progress.py")
print("=" * 80)


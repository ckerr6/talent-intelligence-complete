#!/usr/bin/env python3
"""
Validate Test Batch Before Enrichment
======================================
Pre-flight checks for enrichment batch to ensure data quality

Author: AI Assistant
Date: October 24, 2025
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_db_connection


def validate_batch():
    """Validate test batch for enrichment"""
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ENRICHMENT TEST BATCH VALIDATION")
    print("=" * 80)
    print()
    
    # Get test batch
    cursor.execute("""
        SELECT 
            eq.queue_id::text,
            eq.person_id::text,
            p.full_name,
            p.linkedin_url,
            p.headline,
            eq.priority
        FROM enrichment_queue eq
        JOIN person p ON eq.person_id = p.person_id
        WHERE eq.status = 'pending'
        ORDER BY RANDOM()
        LIMIT 15
    """)
    
    batch = [dict(row) for row in cursor.fetchall()]
    
    print(f"📋 Test Batch: {len(batch)} profiles")
    print()
    
    # Validate each profile
    valid_count = 0
    invalid_count = 0
    
    print("🔍 VALIDATION CHECKS")
    print("-" * 80)
    
    for i, profile in enumerate(batch, 1):
        name = profile['full_name'] or 'Unknown'
        linkedin_url = profile['linkedin_url']
        
        if not linkedin_url or linkedin_url.strip() == '':
            print(f"❌ [{i:2}] {name:40} | NO LINKEDIN URL")
            invalid_count += 1
        else:
            print(f"✅ [{i:2}] {name:40} | {linkedin_url[:50]}")
            valid_count += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Valid profiles:   {valid_count}")
    print(f"Invalid profiles: {invalid_count}")
    print()
    
    if invalid_count > 0:
        print("⚠️  WARNING: Some profiles have no LinkedIn URL and will fail enrichment")
        print("   These will be automatically marked as 'failed' during processing")
    else:
        print("✅ All profiles have LinkedIn URLs and are ready for enrichment")
    
    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Add your PhantomBuster API key to .env file:")
    print("   PHANTOMBUSTER_API_KEY=your_key_here")
    print()
    print("2. Run test enrichment:")
    print("   python phantombuster_linkedin_enrichment.py --test --batch-size 15")
    print()
    print("3. Monitor progress:")
    print("   python monitor_enrichment_progress.py")
    print("=" * 80)
    
    conn.close()


if __name__ == "__main__":
    try:
        validate_batch()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


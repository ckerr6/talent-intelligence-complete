#!/usr/bin/env python3
"""
Smart finish for co-employment graph
Processes remaining medium-sized companies, skips mega-companies
"""

import psycopg2
import psycopg2.extras
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_utils import Logger

def finish_smart():
    logger = Logger("SmartFinish")
    
    logger.section("SMART CO-EMPLOYMENT FINISH")
    logger.info("Processing remaining companies under 500 employees")
    logger.info("Skipping mega-companies (>500 employees) for performance")
    
    conn = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Check current state
        cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
        current_edges = cursor.fetchone()['count']
        logger.info(f"Current edges: {current_edges:,}")
        
        # Get companies not yet processed (under 500 employees)
        cursor.execute("""
            WITH processed_companies AS (
                SELECT DISTINCT company_id FROM edge_coemployment
            )
            SELECT 
                c.company_id,
                c.company_name,
                COUNT(DISTINCT e.person_id) as employees
            FROM company c
            JOIN employment e ON c.company_id = e.company_id
            WHERE c.company_id NOT IN (SELECT company_id FROM processed_companies)
            AND c.company_id IS NOT NULL
            GROUP BY c.company_id, c.company_name
            HAVING COUNT(DISTINCT e.person_id) BETWEEN 2 AND 500
            ORDER BY COUNT(DISTINCT e.person_id) ASC
        """)
        remaining = cursor.fetchall()
        
        logger.success(f"Found {len(remaining)} remaining companies to process (2-500 employees)")
        
        if len(remaining) == 0:
            logger.success("Nothing left to process!")
            return
        
        logger.section("PROCESSING")
        total_added = 0
        start = datetime.now()
        
        for idx, co in enumerate(remaining, 1):
            cursor.execute("""
                WITH pairs AS (
                    SELECT e1.person_id as src, e2.person_id as dst, e1.company_id,
                           MIN(e1.start_date) as e1_start, MAX(e1.end_date) as e1_end,
                           MIN(e2.start_date) as e2_start, MAX(e2.end_date) as e2_end
                    FROM employment e1
                    JOIN employment e2 ON e1.company_id = e2.company_id
                    WHERE e1.company_id = %s AND e1.person_id < e2.person_id
                    GROUP BY e1.person_id, e2.person_id, e1.company_id
                )
                INSERT INTO edge_coemployment (src_person_id, dst_person_id, company_id, overlap_months)
                SELECT src, dst, company_id,
                    CASE WHEN e1_start IS NOT NULL AND e2_start IS NOT NULL THEN
                        EXTRACT(YEAR FROM AGE(
                            LEAST(COALESCE(e1_end, CURRENT_DATE), COALESCE(e2_end, CURRENT_DATE)),
                            GREATEST(e1_start, e2_start)
                        )) * 12 + 
                        EXTRACT(MONTH FROM AGE(
                            LEAST(COALESCE(e1_end, CURRENT_DATE), COALESCE(e2_end, CURRENT_DATE)),
                            GREATEST(e1_start, e2_start)
                        ))
                    ELSE NULL END::int
                FROM pairs
                ON CONFLICT DO NOTHING
            """, (co['company_id'],))
            
            added = cursor.rowcount
            total_added += added
            conn.commit()
            
            if idx % 10 == 0 or added > 100:
                logger.info(f"[{idx}/{len(remaining)}] {co['company_name'][:40]}: +{added:,} | Total added: {total_added:,}")
        
        duration = (datetime.now() - start).total_seconds()
        
        cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
        final_count = cursor.fetchone()['count']
        
        logger.section("✅ SMART FINISH COMPLETE!")
        logger.success(f"Added {total_added:,} new edges in {duration:.1f}s")
        logger.success(f"Final edge count: {final_count:,}")
        logger.info(f"Skipped mega-companies for performance - can add later if needed")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    finish_smart()


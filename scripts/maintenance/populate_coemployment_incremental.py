#!/usr/bin/env python3
"""
Incremental Co-employment Graph Population
Processes ONE company at a time with immediate progress updates
"""

import psycopg2
import psycopg2.extras
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_utils import Logger

def populate_coemployment_incremental():
    """Populate edge_coemployment processing one company at a time"""
    
    logger = Logger("CoemploymentIncremental")
    
    logger.section("INCREMENTAL CO-EMPLOYMENT GRAPH POPULATION")
    logger.info("Processing ONE company at a time for maximum visibility")
    
    # Connect to database
    logger.info("Connecting to database...")
    conn = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    logger.success("Connected to database")
    
    overall_start = datetime.now()
    total_edges_created = 0
    companies_processed = 0
    
    try:
        # Clear existing edges using TRUNCATE
        logger.info("Clearing existing edges...")
        cursor.execute("SELECT COUNT(*) FROM edge_coemployment")
        existing = cursor.fetchone()['count']
        if existing > 0:
            logger.info(f"Found {existing:,} edges to clear")
            cursor.execute("TRUNCATE edge_coemployment")
            conn.commit()
            logger.success(f"Cleared in {(datetime.now() - overall_start).total_seconds():.1f}s")
        else:
            logger.info("Table is empty, nothing to clear")
        
        # Get companies sorted by size (smallest first for faster initial progress)
        logger.info("Getting companies...")
        cursor.execute("""
            SELECT 
                c.company_id,
                c.company_name,
                COUNT(DISTINCT e.person_id) as employee_count
            FROM company c
            JOIN employment e ON c.company_id = e.company_id
            GROUP BY c.company_id, c.company_name
            HAVING COUNT(DISTINCT e.person_id) >= 2
            ORDER BY COUNT(DISTINCT e.person_id) ASC
        """)
        companies = cursor.fetchall()
        total_companies = len(companies)
        logger.success(f"Found {total_companies:,} companies to process")
        
        # Calculate expected edges
        expected = sum(c['employee_count'] * (c['employee_count'] - 1) // 2 for c in companies)
        logger.info(f"Expected total edges: ~{expected:,}")
        
        logger.section("PROCESSING COMPANIES")
        logger.info("Processing smallest companies first for fast initial progress...")
        logger.info("")
        
        last_log_time = datetime.now()
        batch_edges = 0
        batch_companies = 0
        
        for idx, company in enumerate(companies, 1):
            company_start = datetime.now()
            
            # Process this single company
            cursor.execute("""
                WITH person_pairs AS (
                    SELECT 
                        e1.person_id as src_person_id,
                        e2.person_id as dst_person_id,
                        e1.company_id,
                        e1.start_date as e1_start,
                        e1.end_date as e1_end,
                        e2.start_date as e2_start,
                        e2.end_date as e2_end
                    FROM (
                        SELECT person_id, company_id, MIN(start_date) as start_date, MAX(end_date) as end_date
                        FROM employment
                        WHERE company_id = %s
                        GROUP BY person_id, company_id
                    ) e1
                    JOIN (
                        SELECT person_id, company_id, MIN(start_date) as start_date, MAX(end_date) as end_date
                        FROM employment
                        WHERE company_id = %s
                        GROUP BY person_id, company_id
                    ) e2 ON e1.company_id = e2.company_id
                    WHERE e1.person_id < e2.person_id
                )
                INSERT INTO edge_coemployment 
                (src_person_id, dst_person_id, company_id, overlap_months, first_overlap_start, last_overlap_end)
                SELECT 
                    src_person_id,
                    dst_person_id,
                    company_id,
                    CASE 
                        WHEN e1_start IS NOT NULL AND e2_start IS NOT NULL THEN
                            EXTRACT(YEAR FROM AGE(
                                LEAST(COALESCE(e1_end, CURRENT_DATE), COALESCE(e2_end, CURRENT_DATE)),
                                GREATEST(e1_start, e2_start)
                            )) * 12 + 
                            EXTRACT(MONTH FROM AGE(
                                LEAST(COALESCE(e1_end, CURRENT_DATE), COALESCE(e2_end, CURRENT_DATE)),
                                GREATEST(e1_start, e2_start)
                            ))
                        ELSE NULL
                    END::integer as overlap_months,
                    CASE 
                        WHEN e1_start IS NOT NULL AND e2_start IS NOT NULL THEN
                            GREATEST(e1_start, e2_start)
                        ELSE NULL
                    END as first_overlap_start,
                    CASE 
                        WHEN e1_start IS NOT NULL AND e2_start IS NOT NULL THEN
                            LEAST(COALESCE(e1_end, CURRENT_DATE), COALESCE(e2_end, CURRENT_DATE))
                        ELSE NULL
                    END as last_overlap_end
                FROM person_pairs
                ON CONFLICT DO NOTHING
            """, (company['company_id'], company['company_id']))
            
            edges_added = cursor.rowcount
            total_edges_created += edges_added
            companies_processed += 1
            batch_edges += edges_added
            batch_companies += 1
            conn.commit()
            
            company_duration = (datetime.now() - company_start).total_seconds()
            elapsed = (datetime.now() - overall_start).total_seconds()
            
            # Log every company that takes > 0.5s OR every 5 seconds OR every 100 companies
            time_since_log = (datetime.now() - last_log_time).total_seconds()
            should_log = (
                company_duration > 0.5 or 
                time_since_log >= 5 or 
                idx % 100 == 0 or
                idx == total_companies
            )
            
            if should_log:
                rate = total_edges_created / elapsed if elapsed > 0 else 0
                pct = (idx / total_companies * 100)
                remaining = (total_companies - idx) * (elapsed / idx) if idx > 0 else 0
                eta_min = remaining / 60
                
                if batch_companies == 1:
                    msg = f"[{idx}/{total_companies}] {pct:.1f}% | {company['company_name'][:40]}: +{edges_added:,} edges in {company_duration:.1f}s | Total: {total_edges_created:,} | ETA: {eta_min:.1f}m"
                else:
                    msg = f"[{idx}/{total_companies}] {pct:.1f}% | Last {batch_companies} cos: +{batch_edges:,} edges | Total: {total_edges_created:,} ({rate:.0f}/s) | ETA: {eta_min:.1f}m"
                
                logger.info(msg)
                sys.stdout.flush()
                
                last_log_time = datetime.now()
                batch_edges = 0
                batch_companies = 0
        
        overall_duration = (datetime.now() - overall_start).total_seconds()
        
        logger.section("✅ PROCESSING COMPLETE!")
        logger.success(f"Companies processed: {companies_processed:,}")
        logger.success(f"Total edges created: {total_edges_created:,}")
        logger.success(f"Total time: {overall_duration/60:.1f} minutes")
        logger.success(f"Average rate: {total_edges_created/overall_duration:.0f} edges/second")
        
        # Quick stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT src_person_id) + COUNT(DISTINCT dst_person_id) as people_count,
                AVG(overlap_months) FILTER (WHERE overlap_months IS NOT NULL)::int as avg_overlap
            FROM edge_coemployment
        """)
        stats = cursor.fetchone()
        logger.info(f"People in network: ~{stats['people_count']:,}")
        if stats['avg_overlap']:
            logger.info(f"Average overlap: {stats['avg_overlap']} months")
        
        logger.section("✅ SUCCESS!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    populate_coemployment_incremental()


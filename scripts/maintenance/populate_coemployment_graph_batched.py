#!/usr/bin/env python3
"""
Optimized Batched Co-employment Graph Population
Processes companies in batches for better performance and progress tracking
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
from progress_reporter import ProgressReporter

def populate_coemployment_graph_batched():
    """Populate edge_coemployment table using batched approach for efficiency"""
    
    logger = Logger("CoemploymentGraphBatched")
    
    logger.section("OPTIMIZED BATCHED CO-EMPLOYMENT GRAPH POPULATION")
    logger.info("Processing companies in batches for better performance and monitoring")
    
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
    
    try:
        # Clear existing edges using TRUNCATE (much faster than DELETE)
        logger.info("Clearing existing edges from edge_coemployment...")
        cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
        existing_count = cursor.fetchone()['count']
        logger.info(f"Found {existing_count:,} existing edges to clear")
        
        start = datetime.now()
        cursor.execute("TRUNCATE edge_coemployment")
        conn.commit()
        duration = (datetime.now() - start).total_seconds()
        logger.success(f"Cleared {existing_count:,} existing edges in {duration:.2f}s using TRUNCATE")
        
        # Get companies to process
        logger.info("Gathering companies to process...")
        cursor.execute("""
            SELECT 
                company_id,
                COUNT(DISTINCT person_id) as employee_count
            FROM employment
            WHERE company_id IS NOT NULL
            GROUP BY company_id
            HAVING COUNT(DISTINCT person_id) >= 2
            ORDER BY COUNT(DISTINCT person_id) DESC
        """)
        companies = cursor.fetchall()
        total_companies = len(companies)
        logger.success(f"Found {total_companies:,} companies with 2+ employees")
        
        # Calculate expected edges
        expected_edges = sum(c['employee_count'] * (c['employee_count'] - 1) // 2 for c in companies)
        logger.info(f"Expected edges to create: ~{expected_edges:,}")
        
        # Process in batches
        batch_size = 50  # Smaller batches for more frequent updates
        progress = ProgressReporter(total_companies, "companies")
        
        logger.section("PROCESSING COMPANIES IN BATCHES")
        logger.info(f"Batch size: {batch_size} companies per batch")
        logger.info(f"You will see progress updates every ~5-15 seconds")
        
        for batch_start in range(0, total_companies, batch_size):
            batch_end = min(batch_start + batch_size, total_companies)
            batch_companies = companies[batch_start:batch_end]
            company_ids = [c['company_id'] for c in batch_companies]
            
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_companies + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(company_ids)} companies)...")
            
            batch_start_time = datetime.now()
            
            # Insert edges for this batch of companies
            cursor.execute("""
                WITH person_company_pairs AS (
                    SELECT 
                        person_id,
                        company_id,
                        MIN(start_date) as start_date,
                        MAX(end_date) as end_date
                    FROM employment
                    WHERE company_id = ANY(%s::uuid[])
                    GROUP BY person_id, company_id
                )
                INSERT INTO edge_coemployment 
                (src_person_id, dst_person_id, company_id, overlap_months, first_overlap_start, last_overlap_end)
                SELECT 
                    e1.person_id as src_person_id,
                    e2.person_id as dst_person_id,
                    e1.company_id,
                    CASE 
                        WHEN e1.start_date IS NOT NULL AND e2.start_date IS NOT NULL THEN
                            EXTRACT(YEAR FROM AGE(
                                LEAST(COALESCE(e1.end_date, CURRENT_DATE), COALESCE(e2.end_date, CURRENT_DATE)),
                                GREATEST(e1.start_date, e2.start_date)
                            )) * 12 + 
                            EXTRACT(MONTH FROM AGE(
                                LEAST(COALESCE(e1.end_date, CURRENT_DATE), COALESCE(e2.end_date, CURRENT_DATE)),
                                GREATEST(e1.start_date, e2.start_date)
                            ))
                        ELSE NULL
                    END::integer as overlap_months,
                    CASE 
                        WHEN e1.start_date IS NOT NULL AND e2.start_date IS NOT NULL THEN
                            GREATEST(e1.start_date, e2.start_date)
                        ELSE NULL
                    END as first_overlap_start,
                    CASE 
                        WHEN e1.start_date IS NOT NULL AND e2.start_date IS NOT NULL THEN
                            LEAST(COALESCE(e1.end_date, CURRENT_DATE), COALESCE(e2.end_date, CURRENT_DATE))
                        ELSE NULL
                    END as last_overlap_end
                FROM person_company_pairs e1
                JOIN person_company_pairs e2 ON e1.company_id = e2.company_id
                WHERE e1.person_id < e2.person_id
                ON CONFLICT DO NOTHING
            """, (company_ids,))
            
            batch_edges = cursor.rowcount
            total_edges_created += batch_edges
            conn.commit()
            
            batch_duration = (datetime.now() - batch_start_time).total_seconds()
            rate = batch_edges / batch_duration if batch_duration > 0 else 0
            
            # Update progress with detailed info
            progress.update(
                batch_end,
                f"Batch {batch_num}: +{batch_edges:,} edges in {batch_duration:.1f}s ({rate:.0f}/sec) | Total: {total_edges_created:,}"
            )
            
            # Also log immediately for visibility
            sys.stdout.flush()
        
        progress.finish()
        
        overall_duration = (datetime.now() - overall_start).total_seconds()
        
        logger.section("✅ BATCHED PROCESSING COMPLETE!")
        logger.success(f"Total edges created: {total_edges_created:,}")
        logger.success(f"Total time: {overall_duration:.1f}s ({overall_duration/60:.1f} minutes)")
        logger.success(f"Average rate: {total_edges_created/overall_duration:.0f} edges/second")
        
        # Verify results
        logger.info("Verifying final count...")
        cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
        final_count = cursor.fetchone()['count']
        logger.success(f"Final edge count: {final_count:,}")
        
        # Get statistics
        logger.info("Calculating graph statistics...")
        cursor.execute("""
            WITH connection_counts AS (
                SELECT person_id, COUNT(*) as connections
                FROM (
                    SELECT src_person_id as person_id FROM edge_coemployment
                    UNION ALL
                    SELECT dst_person_id as person_id FROM edge_coemployment
                ) all_connections
                GROUP BY person_id
            )
            SELECT 
                COUNT(*) as people_connected,
                MIN(connections) as min_connections,
                MAX(connections) as max_connections,
                AVG(connections)::integer as avg_connections,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY connections)::integer as median_connections
            FROM connection_counts
        """)
        stats = cursor.fetchone()
        
        logger.section("GRAPH STATISTICS")
        logger.info(f"People in network: {stats['people_connected']:,}")
        logger.info(f"Min connections: {stats['min_connections']:,}")
        logger.info(f"Max connections: {stats['max_connections']:,}")
        logger.info(f"Avg connections: {stats['avg_connections']:,}")
        logger.info(f"Median connections: {stats['median_connections']:,}")
        
        # Get top connected people
        cursor.execute("""
            WITH all_connections AS (
                SELECT src_person_id as person_id FROM edge_coemployment
                UNION ALL
                SELECT dst_person_id as person_id FROM edge_coemployment
            )
            SELECT 
                p.full_name,
                COUNT(*) as connection_count
            FROM all_connections ac
            JOIN person p ON ac.person_id = p.person_id
            GROUP BY p.person_id, p.full_name
            ORDER BY connection_count DESC
            LIMIT 10
        """)
        top_connected = cursor.fetchall()
        
        logger.info("🌟 Top 10 Most Connected People:")
        for i, person in enumerate(top_connected, 1):
            logger.info(f"  {i:2d}. {person['full_name']}: {person['connection_count']:,} connections")
        
        logger.section("✅ ALL DONE!")
        logger.success(f"Co-employment graph successfully populated in {overall_duration/60:.1f} minutes")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    populate_coemployment_graph_batched()


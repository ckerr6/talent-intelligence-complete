#!/usr/bin/env python3
# ABOUTME: Populates edge_coemployment table with co-worker relationships
# ABOUTME: Creates graph edges for people who worked at the same company with overlapping dates

import psycopg2
import psycopg2.extras
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_utils import Logger

def populate_coemployment_graph():
    """Populate edge_coemployment table using SQL for efficiency"""
    
    logger = Logger("CoemploymentGraphPopulation")
    
    logger.section("POPULATING CO-EMPLOYMENT GRAPH")
    logger.info("Using optimized SQL-based approach with detailed progress tracking")
    
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
    
    try:
        # First, clear existing edges
        logger.info("Clearing existing edges from edge_coemployment...")
        start = datetime.now()
        cursor.execute("DELETE FROM edge_coemployment")
        cleared_count = cursor.rowcount
        conn.commit()
        duration = (datetime.now() - start).total_seconds()
        logger.success(f"Cleared {cleared_count:,} existing edges in {duration:.2f}s")
        
        # Get detailed statistics
        logger.info("Gathering dataset statistics...")
        
        cursor.execute("SELECT COUNT(*) as count FROM employment")
        total_employment = cursor.fetchone()['count']
        logger.info(f"Total employment records: {total_employment:,}")
        
        cursor.execute("SELECT COUNT(DISTINCT person_id) as count FROM employment WHERE company_id IS NOT NULL")
        total_people = cursor.fetchone()['count']
        logger.info(f"Unique people with company employment: {total_people:,}")
        
        cursor.execute("SELECT COUNT(DISTINCT company_id) as count FROM employment WHERE company_id IS NOT NULL")
        total_companies = cursor.fetchone()['count']
        logger.info(f"Unique companies with employees: {total_companies:,}")
        
        # Analyze company sizes
        cursor.execute("""
            SELECT 
                COUNT(*) as company_count,
                SUM(CASE WHEN employee_count >= 2 THEN 1 ELSE 0 END) as companies_with_multiple,
                AVG(employee_count)::integer as avg_employees,
                MAX(employee_count) as max_employees
            FROM (
                SELECT company_id, COUNT(DISTINCT person_id) as employee_count
                FROM employment
                WHERE company_id IS NOT NULL
                GROUP BY company_id
            ) company_sizes
        """)
        company_stats = cursor.fetchone()
        logger.info(f"Companies with 2+ employees: {company_stats['companies_with_multiple']:,} / {company_stats['company_count']:,}")
        logger.info(f"Average employees per company: {company_stats['avg_employees']:,}")
        logger.info(f"Largest company: {company_stats['max_employees']:,} employees")
        
        # Estimate potential edges
        estimated_edges = company_stats['companies_with_multiple'] * company_stats['avg_employees'] * (company_stats['avg_employees'] - 1) // 2
        logger.info(f"Estimated edges to create: ~{estimated_edges:,}")
        
        logger.info("Creating person-company aggregates (this may take a minute)...")
        start = datetime.now()
        
        # Create temporary table for person-company pairs with date ranges
        cursor.execute("""
            DROP TABLE IF EXISTS temp_person_company_ranges;
            CREATE TEMP TABLE temp_person_company_ranges AS
            SELECT 
                person_id,
                company_id,
                MIN(start_date) as start_date,
                MAX(end_date) as end_date
            FROM employment
            WHERE company_id IS NOT NULL
            GROUP BY person_id, company_id
        """)
        
        cursor.execute("SELECT COUNT(*) as count FROM temp_person_company_ranges")
        temp_count = cursor.fetchone()['count']
        duration = (datetime.now() - start).total_seconds()
        logger.success(f"Created {temp_count:,} person-company pairs in {duration:.2f}s")
        
        # Create indexes on temp table for faster joins
        logger.info("Creating indexes on temporary table...")
        start = datetime.now()
        cursor.execute("CREATE INDEX idx_temp_company ON temp_person_company_ranges(company_id)")
        cursor.execute("CREATE INDEX idx_temp_person ON temp_person_company_ranges(person_id)")
        duration = (datetime.now() - start).total_seconds()
        logger.success(f"Indexes created in {duration:.2f}s")
        
        logger.info("Analyzing query plan...")
        cursor.execute("""
            EXPLAIN 
            SELECT COUNT(*)
            FROM temp_person_company_ranges e1
            JOIN temp_person_company_ranges e2 ON e1.company_id = e2.company_id
            WHERE e1.person_id < e2.person_id
        """)
        plan = cursor.fetchall()
        logger.info("Query execution plan:")
        for line in plan:
            logger.info(f"  {line['QUERY PLAN']}")
        
        logger.info("Inserting co-employment edges (this is the long step)...")
        logger.info("This will process all company pairs and calculate overlaps")
        logger.info("Depending on dataset size, this may take 1-5 minutes...")
        start_time = datetime.now()
        
        cursor.execute("""
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
            FROM temp_person_company_ranges e1
            JOIN temp_person_company_ranges e2 ON e1.company_id = e2.company_id
            WHERE e1.person_id < e2.person_id  -- Avoid duplicates and self-loops
            ON CONFLICT DO NOTHING
        """)
        
        edges_created = cursor.rowcount
        conn.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.success(f"Edge insertion complete! Created {edges_created:,} edges in {duration:.1f}s")
        logger.info(f"Average rate: {edges_created / duration:.0f} edges/second")
        
        # Verify results
        logger.info("Verifying results...")
        cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
        final_count = cursor.fetchone()['count']
        logger.success(f"Verification: {final_count:,} edges in edge_coemployment table")
        
        # Get statistics about the graph
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
                MIN(connections) as min_connections,
                MAX(connections) as max_connections,
                AVG(connections)::integer as avg_connections,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY connections)::integer as median_connections
            FROM connection_counts
        """)
        stats = cursor.fetchone()
        
        logger.info("Connection Statistics:")
        logger.info(f"  Min connections per person: {stats['min_connections']:,}")
        logger.info(f"  Max connections per person: {stats['max_connections']:,}")
        logger.info(f"  Avg connections per person: {stats['avg_connections']:,}")
        logger.info(f"  Median connections: {stats['median_connections']:,}")
        
        # Get top connected people
        logger.info("Finding most connected people...")
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
        
        # Check overlap statistics
        logger.info("Analyzing employment overlap data...")
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE overlap_months IS NULL) as no_date_info,
                COUNT(*) FILTER (WHERE overlap_months = 0) as no_overlap,
                COUNT(*) FILTER (WHERE overlap_months > 0) as has_overlap,
                AVG(overlap_months) FILTER (WHERE overlap_months > 0)::integer as avg_overlap_months
            FROM edge_coemployment
        """)
        overlap_stats = cursor.fetchone()
        
        logger.info("📅 Employment Overlap Statistics:")
        logger.info(f"  Edges with no date info: {overlap_stats['no_date_info']:,}")
        logger.info(f"  Edges with no overlap (sequential): {overlap_stats['no_overlap']:,}")
        logger.info(f"  Edges with overlap (concurrent): {overlap_stats['has_overlap']:,}")
        if overlap_stats['avg_overlap_months']:
            logger.info(f"  Average overlap duration: {overlap_stats['avg_overlap_months']:,} months")
        
        logger.section("✅ CO-EMPLOYMENT GRAPH POPULATION COMPLETE!")
        logger.success(f"Total time: {(datetime.now() - start_time).total_seconds():.1f}s")
        logger.success(f"Total edges: {final_count:,}")
        
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
    populate_coemployment_graph()

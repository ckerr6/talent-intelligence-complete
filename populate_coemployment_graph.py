#!/usr/bin/env python3
# ABOUTME: Populates edge_coemployment table with co-worker relationships
# ABOUTME: Creates graph edges for people who worked at the same company with overlapping dates

import psycopg2
import psycopg2.extras
import os
from datetime import datetime

def populate_coemployment_graph():
    """Populate edge_coemployment table using SQL for efficiency"""
    
    print("=" * 80)
    print("POPULATING CO-EMPLOYMENT GRAPH (SQL-BASED APPROACH)")
    print("=" * 80)
    print()
    
    # Connect to database
    conn = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # First, clear existing edges
        print("🧹 Clearing existing edges...")
        cursor.execute("DELETE FROM edge_coemployment")
        cleared_count = cursor.rowcount
        print(f"   Cleared {cleared_count:,} existing edges")
        print()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as count FROM employment")
        total_employment = cursor.fetchone()['count']
        print(f"📊 Total employment records: {total_employment:,}")
        
        cursor.execute("SELECT COUNT(DISTINCT company_id) as count FROM employment WHERE company_id IS NOT NULL")
        total_companies = cursor.fetchone()['count']
        print(f"📊 Total companies with employees: {total_companies:,}")
        print()
        
        print("🔗 Creating co-employment edges using SQL...")
        print("   This uses a single SQL query to efficiently find all overlapping employment pairs")
        print()
        
        # Use a single SQL query to create all edges at once
        # This finds all pairs of people who worked at the same company
        # and calculates their overlap
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
            FROM (
                -- Get distinct person-company pairs with their date ranges
                SELECT 
                    person_id,
                    company_id,
                    MIN(start_date) as start_date,
                    MAX(end_date) as end_date
                FROM employment
                WHERE company_id IS NOT NULL
                GROUP BY person_id, company_id
            ) e1
            JOIN (
                SELECT 
                    person_id,
                    company_id,
                    MIN(start_date) as start_date,
                    MAX(end_date) as end_date
                FROM employment
                WHERE company_id IS NOT NULL
                GROUP BY person_id, company_id
            ) e2 ON e1.company_id = e2.company_id
            WHERE e1.person_id < e2.person_id  -- Avoid duplicates and self-loops
            ON CONFLICT DO NOTHING
        """)
        
        edges_created = cursor.rowcount
        conn.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 80)
        print("✅ CO-EMPLOYMENT GRAPH POPULATION COMPLETE")
        print("=" * 80)
        print()
        print(f"📊 Final Statistics:")
        print(f"   Edges created: {edges_created:,}")
        print(f"   Time taken: {duration:.1f} seconds")
        print()
        
        # Verify results
        cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
        final_count = cursor.fetchone()['count']
        print(f"✅ Verification: {final_count:,} edges in edge_coemployment table")
        
        # Get statistics about the graph
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
        
        print()
        print("📊 Connection Statistics:")
        print(f"   Min connections: {stats['min_connections']:,}")
        print(f"   Max connections: {stats['max_connections']:,}")
        print(f"   Avg connections: {stats['avg_connections']:,}")
        print(f"   Median connections: {stats['median_connections']:,}")
        
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
        
        print()
        print("🌟 Top 10 connected people:")
        for i, person in enumerate(top_connected, 1):
            print(f"   {i:2d}. {person['full_name']}: {person['connection_count']:,} connections")
        
        # Check overlap statistics
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE overlap_months IS NULL) as no_date_info,
                COUNT(*) FILTER (WHERE overlap_months = 0) as no_overlap,
                COUNT(*) FILTER (WHERE overlap_months > 0) as has_overlap,
                AVG(overlap_months) FILTER (WHERE overlap_months > 0)::integer as avg_overlap_months
            FROM edge_coemployment
        """)
        overlap_stats = cursor.fetchone()
        
        print()
        print("📅 Overlap Statistics:")
        print(f"   Edges with no date info: {overlap_stats['no_date_info']:,}")
        print(f"   Edges with no overlap: {overlap_stats['no_overlap']:,}")
        print(f"   Edges with overlap: {overlap_stats['has_overlap']:,}")
        if overlap_stats['avg_overlap_months']:
            print(f"   Average overlap: {overlap_stats['avg_overlap_months']:,} months")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    populate_coemployment_graph()

#!/usr/bin/env python3
# ABOUTME: Fix duplicate employment records in the database
# ABOUTME: Consolidates multiple employment records for the same person at the same company

"""
Employment Deduplication Fix

Problem: The same person has multiple employment records for the same company
Solution: Keep only one employment record per person per company (the most complete one)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "talent_intelligence.db"

def log(message):
    print(message)

def deduplicate_employment():
    """Remove duplicate employment records"""
    
    log("=================================================================")
    log("EMPLOYMENT DEDUPLICATION")
    log("=================================================================")
    log("")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get stats before
    cursor.execute("SELECT COUNT(*) FROM employment")
    total_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT person_id) FROM employment")
    unique_people = cursor.fetchone()[0]
    
    log(f"Before deduplication:")
    log(f"  Total employment records: {total_before:,}")
    log(f"  Unique people: {unique_people:,}")
    log(f"  Duplicate records: {total_before - unique_people:,}")
    log("")
    
    # Strategy: For each person + company combination, keep only the best record
    # Best = has company_id, has title, lowest employment_id (first inserted)
    
    log("Creating temporary table with records to keep...")
    
    # Create a temp table with the employment_id of records we want to KEEP
    cursor.execute("""
        CREATE TEMP TABLE keep_records AS
        SELECT 
            person_id,
            COALESCE(company_name, 'Unknown') as company_name,
            is_current,
            MIN(employment_id) as keep_employment_id
        FROM (
            SELECT 
                employment_id,
                person_id,
                company_name,
                is_current,
                ROW_NUMBER() OVER (
                    PARTITION BY person_id, COALESCE(company_name, 'Unknown'), is_current 
                    ORDER BY 
                        CASE WHEN company_id IS NOT NULL THEN 0 ELSE 1 END,
                        CASE WHEN title IS NOT NULL AND title != '' THEN 0 ELSE 1 END,
                        CASE WHEN start_date IS NOT NULL THEN 0 ELSE 1 END,
                        employment_id
                ) as rn
            FROM employment
        )
        WHERE rn = 1
        GROUP BY person_id, company_name, is_current
    """)
    
    records_to_keep = cursor.execute("SELECT COUNT(*) FROM keep_records").fetchone()[0]
    log(f"  Records to keep: {records_to_keep:,}")
    log("")
    
    # Delete all records that are NOT in the keep list
    log("Removing duplicate records...")
    cursor.execute("""
        DELETE FROM employment
        WHERE employment_id NOT IN (
            SELECT keep_employment_id FROM keep_records
        )
    """)
    
    removed_count = cursor.rowcount
    conn.commit()
    
    log(f"  Records removed: {removed_count:,}")
    log("")
    
    # Get stats after
    cursor.execute("SELECT COUNT(*) FROM employment")
    total_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT person_id) FROM employment")
    unique_after = cursor.fetchone()[0]
    
    # Verify no duplicates remain
    cursor.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT person_id, company_name, is_current, COUNT(*) as cnt
            FROM employment
            GROUP BY person_id, company_name, is_current
            HAVING COUNT(*) > 1
        )
    """)
    remaining_duplicates = cursor.fetchone()[0]
    
    log("=================================================================")
    log("FINAL STATISTICS")
    log("=================================================================")
    log(f"Total employment records: {total_after:,}")
    log(f"Unique people: {unique_after:,}")
    log(f"Records removed: {removed_count:,}")
    log(f"Reduction: {(removed_count / total_before * 100):.1f}%")
    log(f"Remaining duplicates: {remaining_duplicates}")
    log("")
    
    if remaining_duplicates == 0:
        log("✅ All duplicates removed!")
    else:
        log(f"⚠️  {remaining_duplicates} duplicate groups still remain")
    
    log("")
    
    # Clean up temp table
    cursor.execute("DROP TABLE keep_records")
    
    conn.close()

if __name__ == "__main__":
    deduplicate_employment()

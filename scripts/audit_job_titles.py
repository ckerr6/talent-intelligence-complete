"""
ABOUTME: Audit current job title coverage across the database
ABOUTME: Identifies gaps and opportunities for title backfilling
"""

import sys
import os
from pathlib import Path
import psycopg2
import psycopg2.extras

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.logging_utils import Logger


def run_audit():
    """Execute comprehensive job title audit"""
    logger = Logger("audit_job_titles", verbose=True)
    logger.header("JOB TITLE COVERAGE AUDIT")
    
    # Connect to database
    db = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 1: Overall Statistics
        # ═══════════════════════════════════════════════════════════════════
        logger.section("📊 Overall Statistics")
        
        # Total people in database
        cursor.execute("SELECT COUNT(*) as count FROM person")
        total_people = cursor.fetchone()['count']
        logger.info(f"Total people in database: {total_people:,}")
        
        # People with employment records
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) as count
            FROM employment
        """)
        people_with_employment = cursor.fetchone()['count']
        logger.info(f"People with employment records: {people_with_employment:,} ({people_with_employment/total_people*100:.1f}%)")
        
        # Total employment records
        cursor.execute("SELECT COUNT(*) as count FROM employment")
        total_employment_records = cursor.fetchone()['count']
        logger.info(f"Total employment records: {total_employment_records:,}")
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 2: Title Coverage Analysis
        # ═══════════════════════════════════════════════════════════════════
        logger.section("🎯 Title Coverage Analysis")
        
        # Employment records with titles
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM employment
            WHERE title IS NOT NULL AND title != ''
        """)
        records_with_titles = cursor.fetchone()['count']
        title_coverage_pct = (records_with_titles / total_employment_records * 100) if total_employment_records > 0 else 0
        logger.info(f"Employment records WITH titles: {records_with_titles:,} ({title_coverage_pct:.1f}%)")
        
        # Employment records without titles
        records_without_titles = total_employment_records - records_with_titles
        logger.warning(f"Employment records WITHOUT titles: {records_without_titles:,} ({100-title_coverage_pct:.1f}%)")
        
        # People with at least one titled position
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) as count
            FROM employment
            WHERE title IS NOT NULL AND title != ''
        """)
        people_with_any_title = cursor.fetchone()['count']
        logger.info(f"People with at least one titled position: {people_with_any_title:,}")
        
        # People with NO titles in any employment record
        cursor.execute("""
            SELECT COUNT(DISTINCT eh.person_id) as count
            FROM employment eh
            WHERE eh.person_id NOT IN (
                SELECT DISTINCT person_id
                FROM employment
                WHERE title IS NOT NULL AND title != ''
            )
        """)
        people_with_no_titles = cursor.fetchone()['count']
        logger.warning(f"People with NO titles in any record: {people_with_no_titles:,}")
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 3: Current Employment Analysis
        # ═══════════════════════════════════════════════════════════════════
        logger.section("💼 Current Employment Analysis")
        
        # Current employment records (end_date IS NULL means current)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM employment
            WHERE end_date IS NULL
        """)
        current_employment_records = cursor.fetchone()['count']
        logger.info(f"Current employment records: {current_employment_records:,}")
        
        # Current employment WITH titles
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM employment
            WHERE end_date IS NULL
            AND title IS NOT NULL AND title != ''
        """)
        current_with_titles = cursor.fetchone()['count']
        current_title_coverage = (current_with_titles / current_employment_records * 100) if current_employment_records > 0 else 0
        logger.info(f"Current positions WITH titles: {current_with_titles:,} ({current_title_coverage:.1f}%)")
        
        # Current employment WITHOUT titles
        current_without_titles = current_employment_records - current_with_titles
        logger.warning(f"Current positions WITHOUT titles: {current_without_titles:,} ({100-current_title_coverage:.1f}%)")
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 4: Headline Analysis (Backfill Opportunity)
        # ═══════════════════════════════════════════════════════════════════
        logger.section("📰 Headline Analysis (Backfill Opportunity)")
        
        # People with headlines
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM person
            WHERE headline IS NOT NULL AND headline != ''
        """)
        people_with_headlines = cursor.fetchone()['count']
        logger.info(f"People with headlines: {people_with_headlines:,} ({people_with_headlines/total_people*100:.1f}%)")
        
        # People with headlines but missing current job title
        cursor.execute("""
            SELECT COUNT(DISTINCT p.person_id) as count
            FROM person p
            WHERE p.headline IS NOT NULL AND p.headline != ''
            AND NOT EXISTS (
                SELECT 1
                FROM employment eh
                WHERE eh.person_id = p.person_id
                AND eh.end_date IS NULL
                AND eh.title IS NOT NULL
                AND eh.title != ''
            )
        """)
        backfill_candidates = cursor.fetchone()['count']
        logger.success(f"🎯 BACKFILL CANDIDATES (have headline, missing current title): {backfill_candidates:,}")
        
        # Sample headlines that could be parsed
        logger.info("\nSample headlines for potential title extraction:")
        cursor.execute("""
            SELECT p.full_name, p.headline
            FROM person p
            WHERE p.headline IS NOT NULL AND p.headline != ''
            AND NOT EXISTS (
                SELECT 1
                FROM employment eh
                WHERE eh.person_id = p.person_id
                AND eh.end_date IS NULL
                AND eh.title IS NOT NULL
                AND eh.title != ''
            )
            LIMIT 20
        """)
        
        samples = cursor.fetchall()
        for i, sample in enumerate(samples, 1):
            print(f"  {i:2d}. {sample['full_name']}: \033[96m{sample['headline']}\033[0m")
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 5: Company Distribution
        # ═══════════════════════════════════════════════════════════════════
        logger.section("🏢 Top Companies by Employment Records")
        
        cursor.execute("""
            SELECT 
                c.company_name,
                COUNT(*) as total_records,
                COUNT(CASE WHEN eh.title IS NOT NULL AND eh.title != '' THEN 1 END) as with_titles,
                COUNT(CASE WHEN eh.title IS NULL OR eh.title = '' THEN 1 END) as without_titles,
                ROUND(COUNT(CASE WHEN eh.title IS NOT NULL AND eh.title != '' THEN 1 END)::numeric / COUNT(*)::numeric * 100, 1) as title_coverage_pct
            FROM employment eh
            JOIN company c ON eh.company_id = c.company_id
            GROUP BY c.company_name
            HAVING COUNT(*) >= 10
            ORDER BY total_records DESC
            LIMIT 20
        """)
        
        companies = cursor.fetchall()
        print(f"\n{'Company':<40} {'Total':<8} {'W/Title':<10} {'Missing':<10} {'Coverage':<10}")
        print("─" * 85)
        for company in companies:
            coverage_color = '\033[92m' if company['title_coverage_pct'] >= 80 else '\033[93m' if company['title_coverage_pct'] >= 50 else '\033[91m'
            print(f"{company['company_name']:<40} {company['total_records']:<8} {company['with_titles']:<10} {company['without_titles']:<10} {coverage_color}{company['title_coverage_pct']}%\033[0m")
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 6: Summary & Recommendations
        # ═══════════════════════════════════════════════════════════════════
        logger.section("📋 Summary & Recommendations")
        
        print("\n\033[1m\033[96mKEY FINDINGS:\033[0m")
        print(f"  1. \033[91m{records_without_titles:,} employment records ({100-title_coverage_pct:.1f}%) are missing job titles\033[0m")
        print(f"  2. \033[93m{current_without_titles:,} current positions ({100-current_title_coverage:.1f}%) lack titles\033[0m")
        print(f"  3. \033[92m{backfill_candidates:,} people have headlines that could be parsed for current titles\033[0m")
        
        print("\n\033[1m\033[96mRECOMMENDATIONS:\033[0m")
        print(f"  → Run backfill_job_titles_from_headline.py to extract {backfill_candidates:,} titles from headlines")
        print(f"  → Review and update import scripts to always capture job titles")
        print(f"  → Consider enrichment for the {people_with_no_titles:,} people with no title data")
        
        # Save metrics for tracking
        metrics = {
            "total_people": total_people,
            "people_with_employment": people_with_employment,
            "total_employment_records": total_employment_records,
            "records_with_titles": records_with_titles,
            "title_coverage_pct": round(title_coverage_pct, 2),
            "current_employment_records": current_employment_records,
            "current_with_titles": current_with_titles,
            "current_title_coverage_pct": round(current_title_coverage, 2),
            "people_with_headlines": people_with_headlines,
            "backfill_candidates": backfill_candidates,
            "people_with_no_titles": people_with_no_titles
        }
        
        logger.success("\n✓ Audit complete!")
        
    except Exception as e:
        logger.error(f"Audit failed: {str(e)}", e)
        raise
    
    finally:
        cursor.close()
        db.close()
    
    logger.summary()
    return metrics


if __name__ == "__main__":
    run_audit()


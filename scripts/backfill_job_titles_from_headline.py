"""
ABOUTME: Backfill current job titles by parsing person.headline field
ABOUTME: Extracts titles and companies from LinkedIn headlines to populate employment records
"""

import sys
import os
import re
import uuid
from pathlib import Path
from typing import Optional
import psycopg2
import psycopg2.extras
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.logging_utils import Logger
from scripts.progress_reporter import ProgressReporter


class HeadlineTitleExtractor:
    """Extract job titles and companies from LinkedIn headlines"""
    
    # Common job title patterns
    TITLE_PATTERNS = [
        # "Title at Company" or "Title @ Company"
        r'^(.+?)\s+(?:at|@)\s+(.+?)(?:\s*\||$)',
        # "Title | Company"
        r'^(.+?)\s*\|\s*(.+?)(?:\s*\||$)',
        # "Title - Company"
        r'^(.+?)\s*-\s*(.+?)(?:\s*\||$)',
        # Just a title (no company)
        r'^([A-Z][a-zA-Z\s&,\-]+(?:Engineer|Developer|Manager|Director|VP|President|CEO|CTO|CFO|COO|Head|Lead|Architect|Designer|Analyst|Specialist|Consultant|Advisor))',
    ]
    
    # Words to ignore (common non-title patterns)
    IGNORE_PATTERNS = [
        r'^GitHub:\s*@',  # "GitHub: @username"
        r'^\d+\s+followers',  # "123 followers"
        r'^@[\w\-]+$',  # Just "@username"
        r'^\s*$',  # Empty
    ]
    
    # Common title keywords to validate
    TITLE_KEYWORDS = {
        'engineer', 'developer', 'manager', 'director', 'vp', 'president',
        'ceo', 'cto', 'cfo', 'coo', 'head', 'lead', 'architect', 'designer',
        'analyst', 'specialist', 'consultant', 'advisor', 'founder', 'co-founder',
        'principal', 'senior', 'staff', 'chief', 'partner', 'associate'
    }
    
    def __init__(self, logger):
        self.logger = logger
        self.stats = {
            'parsed': 0,
            'title_only': 0,
            'title_and_company': 0,
            'failed': 0
        }
    
    def should_ignore(self, headline: str) -> bool:
        """Check if headline should be ignored"""
        for pattern in self.IGNORE_PATTERNS:
            if re.search(pattern, headline, re.IGNORECASE):
                return True
        return False
    
    def extract_title_and_company(self, headline: str) -> tuple:
        """
        Extract title and company from headline
        Returns: (title, company) tuple, both can be None
        """
        if not headline or self.should_ignore(headline):
            return None, None
        
        headline = headline.strip()
        
        # Try each pattern
        for pattern in self.TITLE_PATTERNS:
            match = re.search(pattern, headline, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Has both title and company
                    title = match.group(1).strip()
                    company = match.group(2).strip()
                    
                    # Clean up company (remove follower counts, etc.)
                    company = re.sub(r'\s*\|\s*\d+\s+followers.*$', '', company, flags=re.IGNORECASE)
                    company = re.sub(r'\s*@.*$', '', company)
                    
                    # Validate title contains at least one keyword
                    if self._is_valid_title(title):
                        self.stats['title_and_company'] += 1
                        return title, company if company else None
                else:
                    # Title only
                    title = match.group(1).strip()
                    if self._is_valid_title(title):
                        self.stats['title_only'] += 1
                        return title, None
        
        # If no pattern matched, check if the whole headline looks like a title
        if self._is_valid_title(headline):
            self.stats['title_only'] += 1
            return headline, None
        
        self.stats['failed'] += 1
        return None, None
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if extracted text looks like a valid job title"""
        if not title or len(title) < 3:
            return False
        
        # Must contain at least one title keyword
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in self.TITLE_KEYWORDS)


def run_backfill(dry_run: bool = False, limit: Optional[int] = None):
    """
    Backfill job titles from headlines
    
    Args:
        dry_run: If True, don't actually insert records
        limit: Optional limit on number of records to process
    """
    logger = Logger("backfill_headlines", verbose=True)
    logger.header("BACKFILL JOB TITLES FROM HEADLINES")
    
    # Connect to database
    db = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    db.autocommit = False  # Use transactions
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    extractor = HeadlineTitleExtractor(logger)
    
    try:
        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: Find candidates
        # ═══════════════════════════════════════════════════════════════════
        logger.section("📋 Finding Backfill Candidates")
        
        query = """
            SELECT p.person_id, p.full_name, p.headline
            FROM person p
            WHERE p.headline IS NOT NULL AND p.headline != ''
            AND NOT EXISTS (
                SELECT 1
                FROM employment e
                WHERE e.person_id = p.person_id
                AND e.end_date IS NULL
                AND e.title IS NOT NULL
                AND e.title != ''
            )
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        candidates = cursor.fetchall()
        
        total_candidates = len(candidates)
        logger.info(f"Found {total_candidates:,} candidates for title backfill")
        
        if dry_run:
            logger.warning("DRY RUN MODE - No data will be inserted")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: Process candidates
        # ═══════════════════════════════════════════════════════════════════
        logger.section("⚙️  Processing Headlines")
        
        progress = ProgressReporter(total_candidates, "Extracting Titles")
        
        records_to_insert = []
        successful_extractions = 0
        failed_extractions = 0
        
        for candidate in candidates:
            person_id = candidate['person_id']
            full_name = candidate['full_name']
            headline = candidate['headline']
            
            # Extract title and company
            title, company_name = extractor.extract_title_and_company(headline)
            
            if title:
                successful_extractions += 1
                
                # Prepare employment record
                employment_record = {
                    'employment_id': str(uuid.uuid4()),
                    'person_id': person_id,
                    'title': title,
                    'company_name': company_name,
                    'company_id': None,  # We'll need to match company later
                    'start_date': None,
                    'end_date': None,  # NULL = current
                    'source_text_ref': headline,
                    'source_confidence': 0.7 if company_name else 0.5
                }
                
                records_to_insert.append(employment_record)
                
                progress.update(1, f"{successful_extractions:,} extracted")
            else:
                failed_extractions += 1
                progress.update(1, f"{failed_extractions:,} failed")
        
        progress.finish("Extraction Complete")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 3: Match companies
        # ═══════════════════════════════════════════════════════════════════
        logger.section("🏢 Matching Companies")
        
        company_matches = 0
        company_misses = 0
        
        for record in records_to_insert:
            if record['company_name']:
                # Try to find matching company
                cursor.execute("""
                    SELECT company_id
                    FROM company
                    WHERE LOWER(company_name) = LOWER(%s)
                    LIMIT 1
                """, (record['company_name'],))
                
                result = cursor.fetchone()
                if result:
                    record['company_id'] = result['company_id']
                    company_matches += 1
                else:
                    company_misses += 1
        
        logger.info(f"Company matches: {company_matches:,}")
        logger.info(f"Company misses: {company_misses:,}")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 4: Insert records
        # ═══════════════════════════════════════════════════════════════════
        logger.section("💾 Inserting Employment Records")
        
        if not dry_run:
            inserted_count = 0
            
            insert_progress = ProgressReporter(len(records_to_insert), "Inserting Records")
            
            for record in records_to_insert:
                try:
                    cursor.execute("""
                        INSERT INTO employment (
                            employment_id, person_id, company_id, title,
                            start_date, end_date,
                            source_text_ref, source_confidence
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        record['employment_id'],
                        record['person_id'],
                        record['company_id'],
                        record['title'],
                        record['start_date'],
                        record['end_date'],
                        record['source_text_ref'],
                        record['source_confidence']
                    ))
                    
                    inserted_count += 1
                    insert_progress.update(1)
                    
                except Exception as e:
                    logger.error(f"Failed to insert record for {record['person_id']}: {str(e)}")
                    insert_progress.update(1)
            
            insert_progress.finish("Insertion Complete")
            
            # Commit transaction
            db.commit()
            logger.success(f"✓ Successfully inserted {inserted_count:,} employment records")
        else:
            logger.info(f"[DRY RUN] Would have inserted {len(records_to_insert):,} records")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 5: Summary
        # ═══════════════════════════════════════════════════════════════════
        logger.section("📊 Backfill Summary")
        
        logger.stats({
            "Total Candidates": f"{total_candidates:,}",
            "Successful Extractions": f"{successful_extractions:,} ({successful_extractions/total_candidates*100:.1f}%)",
            "Failed Extractions": f"{failed_extractions:,} ({failed_extractions/total_candidates*100:.1f}%)",
            "Title + Company": f"{extractor.stats['title_and_company']:,}",
            "Title Only": f"{extractor.stats['title_only']:,}",
            "Company Matches": f"{company_matches:,}",
            "Company Misses": f"{company_misses:,}",
            "Records Inserted": f"{len(records_to_insert):,}" if not dry_run else "[DRY RUN]"
        })
        
        # Show sample extractions
        logger.info("\n📝 Sample Extractions:")
        for i, record in enumerate(records_to_insert[:10], 1):
            company_info = f" @ {record['company_name']}" if record['company_name'] else ""
            matched = " ✓" if record['company_id'] else ""
            print(f"  {i:2d}. {record['title']}{company_info}{matched}")
        
        if not dry_run:
            logger.success("\n✓ Backfill completed successfully!")
        else:
            logger.info("\n[DRY RUN] No changes made to database")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Backfill failed: {str(e)}", e)
        raise
    
    finally:
        cursor.close()
        db.close()
    
    logger.summary()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill job titles from headlines")
    parser.add_argument('--dry-run', action='store_true', help='Test without inserting data')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    
    args = parser.parse_args()
    
    run_backfill(dry_run=args.dry_run, limit=args.limit)


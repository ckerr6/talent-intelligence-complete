#!/usr/bin/env python3
"""
Enrich employment table with job titles from person.headline field
Currently only 0.48% of employment records have titles - should be 99%+
"""

import psycopg2
import psycopg2.extras
import os
import re
from datetime import datetime

class JobTitleEnricher:
    def __init__(self, pg_host='localhost', pg_port='5432', pg_db='talent', pg_user=None):
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_db = pg_db
        self.pg_user = pg_user or os.environ.get('USER')
        
        self.stats = {
            'employment_records_processed': 0,
            'titles_extracted_from_headline': 0,
            'titles_already_populated': 0,
            'could_not_extract': 0,
            'errors': 0
        }
    
    def connect(self):
        """Connect to PostgreSQL"""
        print("📡 Connecting to PostgreSQL...")
        
        self.conn = psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_db,
            user=self.pg_user
        )
        self.conn.autocommit = False
        
        print("✅ Connected\n")
    
    def extract_title_from_headline(self, headline, company_name=None):
        """
        Extract job title from LinkedIn headline
        
        Examples:
        - "Principal Site Reliability Engineer at GoDaddy" → "Principal Site Reliability Engineer"
        - "Founder & CEO @ Company" → "Founder & CEO"
        - "Software Engineer | Tech Lead at Google" → "Software Engineer"
        """
        if not headline:
            return None
        
        # Clean up the headline
        headline = headline.strip()
        
        # Common patterns
        patterns = [
            r'^([^@|]+?)\s+(?:at|@)\s+',  # "Title at Company"
            r'^([^@|]+?)\s+\|',            # "Title | Something"
            r'^([^@]+)',                   # Everything before @ or end
        ]
        
        for pattern in patterns:
            match = re.search(pattern, headline, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                
                # Clean up common suffixes
                title = re.sub(r'\s+\|\s*$', '', title)  # Remove trailing |
                title = re.sub(r'\s+@\s*$', '', title)   # Remove trailing @
                
                # If it's too long (>100 chars) or too short (<3 chars), skip
                if len(title) < 3 or len(title) > 100:
                    continue
                
                # If title looks like it contains company info, skip
                # (e.g., "at Google" shouldn't be a title)
                if title.lower().startswith(('at ', 'with ', 'for ')):
                    continue
                
                return title
        
        return None
    
    def enrich_current_jobs(self):
        """Enrich current employment records (end_date IS NULL)"""
        print("📝 Enriching current job titles from person.headline...")
        
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get current employment records without titles
        cursor.execute("""
            SELECT 
                e.employment_id,
                e.person_id,
                e.company_id,
                e.title,
                p.headline,
                p.full_name,
                c.company_name
            FROM employment e
            JOIN person p ON e.person_id = p.person_id
            LEFT JOIN company c ON e.company_id = c.company_id
            WHERE e.end_date IS NULL  -- Current jobs only
            AND (e.title IS NULL OR e.title = '')
            AND p.headline IS NOT NULL
            ORDER BY e.start_date DESC NULLS LAST
        """)
        
        records = cursor.fetchall()
        total = len(records)
        print(f"   Found {total:,} current employment records without titles\n")
        
        update_cursor = self.conn.cursor()
        updated = 0
        
        for i, record in enumerate(records, 1):
            self.stats['employment_records_processed'] += 1
            
            try:
                # Extract title from headline
                title = self.extract_title_from_headline(
                    record['headline'],
                    record['company_name']
                )
                
                if title:
                    # Update employment record
                    update_cursor.execute("""
                        UPDATE employment
                        SET title = %s
                        WHERE employment_id = %s
                    """, (title, record['employment_id']))
                    
                    self.stats['titles_extracted_from_headline'] += 1
                    updated += 1
                    
                    # Commit every 100 records
                    if i % 100 == 0:
                        self.conn.commit()
                        print(f"   Progress: {i:,}/{total:,} ({i/total*100:.1f}%) - Updated: {updated:,}")
                else:
                    self.stats['could_not_extract'] += 1
                    
            except Exception as e:
                print(f"   ❌ Error processing {record.get('full_name', 'Unknown')}: {e}")
                self.stats['errors'] += 1
                self.conn.rollback()
                continue
        
        # Final commit
        self.conn.commit()
        print(f"\n✅ Current jobs enriched: {updated:,} titles extracted")
    
    def enrich_historical_jobs(self):
        """
        Enrich historical employment records
        This is harder since headline only shows current job
        We'll use patterns and heuristics
        """
        print("\n📚 Enriching historical job titles...")
        print("   (Note: This is best-effort since LinkedIn headlines show current role)\n")
        
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Strategy: For people with multiple jobs at same company,
        # if current job has title, we can infer previous titles might be similar
        cursor.execute("""
            SELECT 
                e.employment_id,
                e.person_id,
                e.company_id,
                e.title,
                e.start_date,
                e.end_date,
                p.headline,
                c.company_name,
                current_e.title as current_title
            FROM employment e
            JOIN person p ON e.person_id = p.person_id
            LEFT JOIN company c ON e.company_id = c.company_id
            LEFT JOIN employment current_e ON 
                current_e.person_id = e.person_id AND 
                current_e.company_id = e.company_id AND
                current_e.end_date IS NULL AND
                current_e.title IS NOT NULL
            WHERE e.end_date IS NOT NULL  -- Historical jobs only
            AND (e.title IS NULL OR e.title = '')
            AND current_e.title IS NOT NULL  -- Has current title at same company
            ORDER BY e.person_id, e.start_date DESC
        """)
        
        records = cursor.fetchall()
        print(f"   Found {len(records):,} historical records at same company with known current title")
        
        # For now, we'll mark these but not auto-fill since we don't have
        # reliable historical data. In the future, could use patterns like
        # "Senior Engineer" → "Engineer" for earlier roles
        
        print("   ⚠️  Historical title enrichment requires additional data sources")
        print("   ℹ️  Focus on current jobs for now\n")
    
    def validate_results(self):
        """Validate the enrichment results"""
        print("✅ Validating results...")
        
        cursor = self.conn.cursor()
        
        # Count employment records with/without titles
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as has_title,
                COUNT(CASE WHEN end_date IS NULL THEN 1 END) as current_jobs,
                COUNT(CASE WHEN end_date IS NULL AND title IS NOT NULL AND title != '' THEN 1 END) as current_with_title
            FROM employment
        """)
        
        result = cursor.fetchone()
        total, has_title, current_jobs, current_with_title = result
        
        print(f"\n📊 RESULTS:")
        print(f"   Total employment records:      {total:,}")
        print(f"   Records with title:            {has_title:,} ({has_title/total*100:.2f}%)")
        print(f"   Current jobs:                  {current_jobs:,}")
        print(f"   Current jobs with title:       {current_with_title:,} ({current_with_title/current_jobs*100:.2f}%)")
        print()
    
    def log_results(self):
        """Log enrichment results to migration_log table"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO migration_log (
                migration_name,
                migration_phase,
                status,
                records_processed,
                records_created,
                records_updated,
                records_skipped,
                metadata,
                completed_at
            ) VALUES (
                'job_title_enrichment',
                'data_enrichment',
                'completed',
                %s,
                0,
                %s,
                %s,
                %s::jsonb,
                NOW()
            )
        """, (
            self.stats['employment_records_processed'],
            self.stats['titles_extracted_from_headline'],
            self.stats['could_not_extract'],
            psycopg2.extras.Json({
                'titles_already_populated': self.stats['titles_already_populated'],
                'errors': self.stats['errors']
            })
        ))
        
        self.conn.commit()
    
    def print_summary(self):
        """Print enrichment summary"""
        print("\n" + "="*80)
        print("JOB TITLE ENRICHMENT SUMMARY")
        print("="*80)
        print(f"Employment Records Processed:    {self.stats['employment_records_processed']:,}")
        print(f"Titles Extracted from Headline:  {self.stats['titles_extracted_from_headline']:,}")
        print(f"Already Had Titles:              {self.stats['titles_already_populated']:,}")
        print(f"Could Not Extract:               {self.stats['could_not_extract']:,}")
        print(f"Errors:                          {self.stats['errors']:,}")
        print("="*80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich employment table with job titles')
    parser.add_argument('--pg-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--pg-port', default='5432', help='PostgreSQL port')
    parser.add_argument('--pg-db', default='talent', help='PostgreSQL database name')
    parser.add_argument('--pg-user', default=None, help='PostgreSQL user')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("JOB TITLE ENRICHMENT FOR EMPLOYMENT TABLE")
    print("="*80)
    print(f"PostgreSQL:   {args.pg_user or os.environ.get('USER')}@{args.pg_host}:{args.pg_port}/{args.pg_db}")
    print("="*80 + "\n")
    
    enricher = JobTitleEnricher(
        pg_host=args.pg_host,
        pg_port=args.pg_port,
        pg_db=args.pg_db,
        pg_user=args.pg_user
    )
    
    enricher.connect()
    enricher.enrich_current_jobs()
    enricher.enrich_historical_jobs()
    enricher.validate_results()
    enricher.log_results()
    enricher.print_summary()
    
    print("\n✅ Job title enrichment complete!")

if __name__ == "__main__":
    main()


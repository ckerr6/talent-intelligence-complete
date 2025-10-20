#!/usr/bin/env python3
"""
Import SQLite people and their emails into PostgreSQL talent database
This will boost email coverage from 3.11% to ~45%
"""

import sqlite3
import psycopg2
import psycopg2.extras
import os
import sys
from urllib.parse import unquote
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from migration_scripts.migration_utils import normalize_linkedin_url, log_migration_event

class SQLitePeopleImporter:
    def __init__(self, sqlite_path, pg_host='localhost', pg_port='5432', pg_db='talent', pg_user=None):
        self.sqlite_path = sqlite_path
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_db = pg_db
        self.pg_user = pg_user or os.environ.get('USER')
        
        self.stats = {
            'people_processed': 0,
            'people_created': 0,
            'people_skipped_exists': 0,
            'people_skipped_no_linkedin': 0,
            'emails_created': 0,
            'emails_skipped': 0,
            'errors': 0
        }
    
    def connect(self):
        """Connect to both databases"""
        print("📡 Connecting to databases...")
        
        # SQLite connection
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_db,
            user=self.pg_user
        )
        self.pg_conn.autocommit = False
        
        print("✅ Connected to both databases\n")
    
    def get_existing_linkedin_urls(self):
        """Get all existing normalized LinkedIn URLs from PostgreSQL"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT normalized_linkedin_url
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        return {row[0] for row in cursor.fetchall()}
    
    def import_people(self):
        """Import people from SQLite to PostgreSQL"""
        print("👥 Importing people from SQLite...")
        
        # Get existing LinkedIn URLs to avoid duplicates
        existing_urls = self.get_existing_linkedin_urls()
        print(f"   Found {len(existing_urls):,} existing people in PostgreSQL")
        
        # Get people from SQLite
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute("""
            SELECT 
                p.person_id,
                p.first_name,
                p.last_name,
                p.full_name,
                p.primary_email,
                p.location,
                p.status,
                p.data_quality_score,
                p.notes,
                sp.profile_url as linkedin_url
            FROM people p
            LEFT JOIN social_profiles sp ON p.person_id = sp.person_id AND sp.platform = 'linkedin'
            WHERE sp.profile_url IS NOT NULL
        """)
        
        people = sqlite_cursor.fetchall()
        print(f"   Found {len(people):,} people in SQLite with LinkedIn URLs\n")
        
        pg_cursor = self.pg_conn.cursor()
        
        for i, person in enumerate(people, 1):
            self.stats['people_processed'] += 1
            
            try:
                # Normalize LinkedIn URL
                normalized_url = normalize_linkedin_url(person['linkedin_url'])
                
                if not normalized_url:
                    self.stats['people_skipped_no_linkedin'] += 1
                    continue
                
                # Skip if already exists
                if normalized_url in existing_urls:
                    self.stats['people_skipped_exists'] += 1
                    continue
                
                # Insert person
                pg_cursor.execute("""
                    INSERT INTO person (
                        person_id,
                        full_name,
                        first_name,
                        last_name,
                        linkedin_url,
                        normalized_linkedin_url,
                        location
                    ) VALUES (
                        gen_random_uuid(), %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (linkedin_url) DO NOTHING
                    RETURNING person_id
                """, (
                    person['full_name'] or f"{person['first_name']} {person['last_name']}".strip(),
                    person['first_name'],
                    person['last_name'],
                    person['linkedin_url'],
                    normalized_url,
                    person['location']
                ))
                
                result = pg_cursor.fetchone()
                if result:
                    person_id = result[0]
                    self.stats['people_created'] += 1
                    
                    # Add email if exists
                    if person['primary_email']:
                        self.add_email(pg_cursor, person_id, person['primary_email'])
                    
                    # Commit every 100 records
                    if i % 100 == 0:
                        self.pg_conn.commit()
                        print(f"   Progress: {i:,}/{len(people):,} ({i/len(people)*100:.1f}%) - Created: {self.stats['people_created']:,}")
                
            except Exception as e:
                full_name = person['full_name'] if person['full_name'] else 'Unknown'
                print(f"   ❌ Error importing {full_name}: {e}")
                self.stats['errors'] += 1
                self.pg_conn.rollback()
                continue
        
        # Final commit
        self.pg_conn.commit()
        print(f"\n✅ People import complete!")
    
    def add_email(self, cursor, person_id, email):
        """Add email to person_email table"""
        try:
            cursor.execute("""
                INSERT INTO person_email (
                    person_id,
                    email,
                    email_type,
                    is_primary,
                    source
                ) VALUES (
                    %s, %s, 'primary', true, 'sqlite_import'
                )
                ON CONFLICT (person_id, lower(email)) DO NOTHING
            """, (person_id, email.lower().strip()))
            
            if cursor.rowcount > 0:
                self.stats['emails_created'] += 1
        except Exception as e:
            self.stats['emails_skipped'] += 1
    
    def import_additional_emails(self):
        """Import emails from SQLite emails table"""
        print("\n📧 Importing additional emails from SQLite emails table...")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        
        # Get emails with their person LinkedIn URLs
        sqlite_cursor.execute("""
            SELECT 
                e.email,
                e.is_primary,
                sp.profile_url as linkedin_url
            FROM emails e
            JOIN people p ON e.person_id = p.person_id
            JOIN social_profiles sp ON p.person_id = sp.person_id AND sp.platform = 'linkedin'
            WHERE e.email IS NOT NULL AND e.email != ''
            AND sp.profile_url IS NOT NULL
        """)
        
        emails = sqlite_cursor.fetchall()
        print(f"   Found {len(emails):,} emails in SQLite")
        
        # Build mapping of normalized LinkedIn URL to PostgreSQL person_id
        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute("""
            SELECT person_id, normalized_linkedin_url
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        
        linkedin_to_person = {row[1]: row[0] for row in pg_cursor.fetchall()}
        
        added = 0
        for email_row in emails:
            normalized_url = normalize_linkedin_url(email_row['linkedin_url'])
            person_id = linkedin_to_person.get(normalized_url)
            
            if person_id:
                try:
                    pg_cursor.execute("""
                        INSERT INTO person_email (
                            person_id,
                            email,
                            email_type,
                            is_primary,
                            source
                        ) VALUES (
                            %s, %s, 'primary', %s, 'sqlite_emails_table'
                        )
                        ON CONFLICT (person_id, lower(email)) DO NOTHING
                    """, (person_id, email_row['email'].lower().strip(), email_row['is_primary']))
                    
                    if pg_cursor.rowcount > 0:
                        added += 1
                        
                except Exception as e:
                    continue
        
        self.pg_conn.commit()
        print(f"✅ Added {added:,} additional emails")
    
    def log_results(self):
        """Log migration results to migration_log table"""
        log_migration_event(
            self.pg_conn,  # Pass connection, not cursor
            migration_name='sqlite_people_import',
            phase='data_import',
            status='completed',
            records_processed=self.stats['people_processed'],
            records_created=self.stats['people_created'],
            records_skipped=self.stats['people_skipped_exists'] + self.stats['people_skipped_no_linkedin'],
            metadata={
                'emails_created': self.stats['emails_created'],
                'errors': self.stats['errors']
            }
        )
        
        self.pg_conn.commit()
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "="*80)
        print("IMPORT SUMMARY")
        print("="*80)
        print(f"People Processed:        {self.stats['people_processed']:,}")
        print(f"People Created:          {self.stats['people_created']:,}")
        print(f"People Skipped (exists): {self.stats['people_skipped_exists']:,}")
        print(f"People Skipped (no LI):  {self.stats['people_skipped_no_linkedin']:,}")
        print(f"Emails Created:          {self.stats['emails_created']:,}")
        print(f"Emails Skipped:          {self.stats['emails_skipped']:,}")
        print(f"Errors:                  {self.stats['errors']:,}")
        print("="*80)
        
        # Check new totals
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM person")
        total_people = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM person_email")
        total_emails = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT person_id) FROM person_email")
        people_with_emails = cursor.fetchone()[0]
        
        print(f"\n📊 NEW DATABASE STATE:")
        print(f"   Total People:           {total_people:,}")
        print(f"   Total Emails:           {total_emails:,}")
        print(f"   People with Emails:     {people_with_emails:,} ({people_with_emails/total_people*100:.2f}%)")
        print("="*80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Import SQLite people into PostgreSQL talent database')
    parser.add_argument('--sqlite-db', default='../talent_intelligence.db', help='Path to SQLite database')
    parser.add_argument('--pg-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--pg-port', default='5432', help='PostgreSQL port')
    parser.add_argument('--pg-db', default='talent', help='PostgreSQL database name')
    parser.add_argument('--pg-user', default=None, help='PostgreSQL user')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("SQLITE PEOPLE IMPORT TO POSTGRESQL TALENT")
    print("="*80)
    print(f"SQLite DB:    {args.sqlite_db}")
    print(f"PostgreSQL:   {args.pg_user or os.environ.get('USER')}@{args.pg_host}:{args.pg_port}/{args.pg_db}")
    print("="*80 + "\n")
    
    importer = SQLitePeopleImporter(
        sqlite_path=args.sqlite_db,
        pg_host=args.pg_host,
        pg_port=args.pg_port,
        pg_db=args.pg_db,
        pg_user=args.pg_user
    )
    
    importer.connect()
    importer.import_people()
    importer.import_additional_emails()
    importer.log_results()
    importer.print_summary()
    
    print("\n✅ Import complete!")

if __name__ == "__main__":
    main()


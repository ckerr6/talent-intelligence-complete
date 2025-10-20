#!/usr/bin/env python3
"""
Email Migration Script
Migrates email addresses from SQLite to PostgreSQL talent database
"""

import sys
import os
import sqlite3
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from migration_utils import (
    normalize_linkedin_url,
    normalize_email,
    log_migration_event,
    validate_email,
    infer_email_type,
    print_progress
)

class EmailMigrator:
    def __init__(self, sqlite_db_path: str, pg_conn_params: dict):
        self.sqlite_path = sqlite_db_path
        self.pg_params = pg_conn_params
        self.stats = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'no_match': 0,
            'invalid_email': 0
        }
        
    def connect_databases(self):
        """Establish connections to both databases"""
        print("📡 Connecting to databases...")
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        self.pg_conn = psycopg2.connect(**self.pg_params)
        self.pg_conn.autocommit = False
        
        print("✅ Connections established")
    
    def get_sqlite_emails(self) -> List[Dict]:
        """Extract all emails from SQLite database"""
        print("\n📊 Extracting emails from SQLite...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Get emails from people table (primary_email)
        cursor.execute("""
            SELECT 
                person_id,
                primary_email as email,
                'primary' as email_type,
                1 as is_primary
            FROM people
            WHERE primary_email IS NOT NULL 
            AND primary_email != ''
        """)
        
        emails_from_people = [dict(row) for row in cursor.fetchall()]
        
        # Get emails from emails table
        cursor.execute("""
            SELECT 
                person_id,
                email,
                email_type,
                is_primary
            FROM emails
            WHERE email IS NOT NULL
            AND email != ''
        """)
        
        emails_from_table = [dict(row) for row in cursor.fetchall()]
        
        # Combine and deduplicate
        all_emails = {}
        for email_record in emails_from_people + emails_from_table:
            key = (email_record['person_id'], normalize_email(email_record['email']))
            if key not in all_emails:
                all_emails[key] = email_record
        
        emails_list = list(all_emails.values())
        print(f"   Found {len(emails_list):,} unique email records")
        
        return emails_list
    
    def get_sqlite_linkedin_map(self) -> Dict[str, str]:
        """Get mapping of SQLite person_id to normalized LinkedIn URL"""
        print("\n🔗 Building SQLite LinkedIn URL mapping...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                p.person_id,
                sp.profile_url
            FROM people p
            JOIN social_profiles sp ON p.person_id = sp.person_id
            WHERE sp.platform = 'linkedin'
            AND sp.profile_url IS NOT NULL
            AND sp.profile_url != ''
        """)
        
        linkedin_map = {}
        for row in cursor.fetchall():
            person_id = row['person_id']
            linkedin_url = normalize_linkedin_url(row['profile_url'])
            if linkedin_url:
                linkedin_map[person_id] = linkedin_url
        
        print(f"   Mapped {len(linkedin_map):,} SQLite people to LinkedIn URLs")
        
        return linkedin_map
    
    def get_postgres_person_map(self) -> Dict[str, str]:
        """Get mapping of normalized LinkedIn URL to PostgreSQL person_id"""
        print("\n🔗 Building PostgreSQL person mapping...")
        
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                person_id::text,
                normalized_linkedin_url
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
            AND normalized_linkedin_url != ''
        """)
        
        person_map = {}
        for row in cursor.fetchall():
            pg_person_id = row[0]
            linkedin_url = row[1]
            person_map[linkedin_url] = pg_person_id
        
        print(f"   Mapped {len(person_map):,} PostgreSQL people to LinkedIn URLs")
        
        return person_map
    
    def match_people(self, sqlite_person_id: str, linkedin_map: Dict, person_map: Dict) -> str:
        """
        Match SQLite person to PostgreSQL person via LinkedIn URL
        Returns PostgreSQL person_id or None
        """
        # Get LinkedIn URL for this SQLite person
        linkedin_url = linkedin_map.get(sqlite_person_id)
        if not linkedin_url:
            return None
        
        # Find PostgreSQL person with this LinkedIn URL
        pg_person_id = person_map.get(linkedin_url)
        return pg_person_id
    
    def email_exists(self, person_id: str, email: str) -> bool:
        """Check if email already exists for this person"""
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 1 FROM person_email
            WHERE person_id = %s::uuid
            AND lower(email) = lower(%s)
            LIMIT 1
        """, (person_id, email))
        
        return cursor.fetchone() is not None
    
    def insert_email(self, person_id: str, email: str, email_type: str, is_primary: bool):
        """Insert email into PostgreSQL"""
        cursor = self.pg_conn.cursor()
        
        # Infer email type if not provided or unknown
        if not email_type or email_type == 'unknown':
            email_type = infer_email_type(email)
        
        cursor.execute("""
            INSERT INTO person_email 
            (person_id, email, email_type, is_primary, source, verified)
            VALUES (%s::uuid, %s, %s, %s, 'sqlite_migration', FALSE)
            ON CONFLICT (person_id, lower(email)) DO NOTHING
        """, (person_id, email, email_type, is_primary))
    
    def migrate_emails(self):
        """Main migration process"""
        print("\n" + "=" * 80)
        print("EMAIL MIGRATION: SQLite → PostgreSQL talent")
        print("=" * 80)
        
        # Connect to databases
        self.connect_databases()
        
        # Log migration start
        log_migration_event(
            self.pg_conn,
            'email_migration',
            'email',
            'started',
            metadata={'source': self.sqlite_path}
        )
        
        try:
            # Get data from SQLite
            emails = self.get_sqlite_emails()
            linkedin_map = self.get_sqlite_linkedin_map()
            
            # Get mapping from PostgreSQL
            person_map = self.get_postgres_person_map()
            
            # Process emails
            print(f"\n📧 Migrating {len(emails):,} emails...")
            
            for i, email_record in enumerate(emails, 1):
                self.stats['processed'] += 1
                
                # Validate email
                email = email_record['email']
                if not validate_email(email):
                    self.stats['invalid_email'] += 1
                    self.stats['skipped'] += 1
                    continue
                
                # Match SQLite person to PostgreSQL person
                sqlite_person_id = email_record['person_id']
                pg_person_id = self.match_people(sqlite_person_id, linkedin_map, person_map)
                
                if not pg_person_id:
                    self.stats['no_match'] += 1
                    self.stats['skipped'] += 1
                    continue
                
                # Check if email already exists
                if self.email_exists(pg_person_id, email):
                    self.stats['skipped'] += 1
                    continue
                
                # Insert email
                self.insert_email(
                    pg_person_id,
                    email,
                    email_record.get('email_type', 'unknown'),
                    bool(email_record.get('is_primary', False))
                )
                
                self.stats['created'] += 1
                
                # Progress update
                if i % 100 == 0:
                    print_progress(i, len(emails), 'Migrating emails')
                    self.pg_conn.commit()
            
            # Final commit
            self.pg_conn.commit()
            print_progress(len(emails), len(emails), 'Migrating emails')
            
            # Log success
            log_migration_event(
                self.pg_conn,
                'email_migration',
                'email',
                'completed',
                records_processed=self.stats['processed'],
                records_created=self.stats['created'],
                records_updated=self.stats['updated'],
                records_skipped=self.stats['skipped'],
                metadata=self.stats
            )
            
            self.print_summary()
            
        except Exception as e:
            self.pg_conn.rollback()
            print(f"\n❌ Error during migration: {e}")
            
            log_migration_event(
                self.pg_conn,
                'email_migration',
                'email',
                'failed',
                error_message=str(e),
                metadata=self.stats
            )
            
            raise
        
        finally:
            self.sqlite_conn.close()
            self.pg_conn.close()
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Total emails processed:    {self.stats['processed']:,}")
        print(f"Emails created:            {self.stats['created']:,}")
        print(f"Emails updated:            {self.stats['updated']:,}")
        print(f"Emails skipped:            {self.stats['skipped']:,}")
        print(f"  - No person match:       {self.stats['no_match']:,}")
        print(f"  - Invalid email:         {self.stats['invalid_email']:,}")
        print(f"  - Already exists:        {self.stats['skipped'] - self.stats['no_match'] - self.stats['invalid_email']:,}")
        
        # Calculate success rate
        if self.stats['processed'] > 0:
            success_rate = (self.stats['created'] / self.stats['processed']) * 100
            print(f"\nSuccess rate:              {success_rate:.1f}%")
        
        print("=" * 80)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate emails from SQLite to PostgreSQL')
    parser.add_argument('--sqlite-db', default='../talent_intelligence.db',
                       help='Path to SQLite database')
    parser.add_argument('--pg-host', default='localhost',
                       help='PostgreSQL host')
    parser.add_argument('--pg-port', default='5432',
                       help='PostgreSQL port')
    parser.add_argument('--pg-db', default='talent',
                       help='PostgreSQL database name')
    parser.add_argument('--pg-user', default=os.environ.get('USER'),
                       help='PostgreSQL user')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run without actually inserting data')
    
    args = parser.parse_args()
    
    # PostgreSQL connection parameters
    pg_params = {
        'host': args.pg_host,
        'port': args.pg_port,
        'database': args.pg_db,
        'user': args.pg_user
    }
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be inserted")
    
    # Create migrator and run
    migrator = EmailMigrator(args.sqlite_db, pg_params)
    migrator.migrate_emails()
    
    print("\n✅ Email migration complete!")


if __name__ == '__main__':
    main()


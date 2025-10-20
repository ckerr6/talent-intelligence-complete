#!/usr/bin/env python3
"""
Improve GitHub profile matching to people and extract emails from GitHub profiles
Currently: 0.57% of people have GitHub profiles (189/32,515)
Also: 5,000 GitHub profiles have emails that should be in person_email table
"""

import psycopg2
import psycopg2.extras
import os
from datetime import datetime

class GitHubMatchingEnricher:
    def __init__(self, pg_host='localhost', pg_port='5432', pg_db='talent', pg_user=None):
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_db = pg_db
        self.pg_user = pg_user or os.environ.get('USER')
        
        self.stats = {
            'github_profiles_processed': 0,
            'new_matches_by_email': 0,
            'new_matches_by_name_company': 0,
            'emails_extracted_from_github': 0,
            'emails_skipped': 0,
            'already_matched': 0,
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
    
    def extract_github_emails(self):
        """Extract emails from GitHub profiles and add to person_email table"""
        print("📧 Extracting emails from GitHub profiles...")
        
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get GitHub profiles with emails that are linked to people
        cursor.execute("""
            SELECT 
                gp.github_profile_id,
                gp.person_id,
                gp.github_email,
                gp.github_username,
                p.full_name
            FROM github_profile gp
            JOIN person p ON gp.person_id = p.person_id
            WHERE gp.github_email IS NOT NULL 
            AND gp.github_email != ''
            AND gp.person_id IS NOT NULL
        """)
        
        profiles = cursor.fetchall()
        total = len(profiles)
        print(f"   Found {total:,} GitHub profiles with emails linked to people\n")
        
        added = 0
        update_cursor = self.conn.cursor()
        
        for i, profile in enumerate(profiles, 1):
            try:
                # Add email to person_email table
                update_cursor.execute("""
                    INSERT INTO person_email (
                        person_id,
                        email,
                        email_type,
                        is_primary,
                        source
                    ) VALUES (
                        %s, %s, 'personal', false, 'github_profile'
                    )
                    ON CONFLICT (person_id, lower(email)) DO NOTHING
                """, (profile['person_id'], profile['github_email'].lower().strip()))
                
                if update_cursor.rowcount > 0:
                    self.stats['emails_extracted_from_github'] += 1
                    added += 1
                else:
                    self.stats['emails_skipped'] += 1
                
                # Commit every 100 records
                if i % 100 == 0:
                    self.conn.commit()
                    print(f"   Progress: {i:,}/{total:,} ({i/total*100:.1f}%) - Added: {added:,}")
                    
            except Exception as e:
                self.stats['errors'] += 1
                continue
        
        # Final commit
        self.conn.commit()
        print(f"\n✅ Extracted {added:,} emails from GitHub profiles")
    
    def match_github_by_email(self):
        """Match unlinked GitHub profiles to people using email addresses"""
        print("\n🔗 Matching GitHub profiles to people by email...")
        
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get unlinked GitHub profiles with emails
        cursor.execute("""
            SELECT 
                gp.github_profile_id,
                gp.github_email,
                gp.github_username,
                gp.github_name
            FROM github_profile gp
            WHERE gp.person_id IS NULL
            AND gp.github_email IS NOT NULL
            AND gp.github_email != ''
        """)
        
        unlinked_profiles = cursor.fetchall()
        print(f"   Found {len(unlinked_profiles):,} unlinked GitHub profiles with emails")
        
        # Build email → person_id mapping
        cursor.execute("""
            SELECT person_id, email
            FROM person_email
        """)
        
        email_to_person = {}
        for row in cursor.fetchall():
            email_to_person[row['email'].lower()] = row['person_id']
        
        print(f"   Built mapping of {len(email_to_person):,} emails to people\n")
        
        update_cursor = self.conn.cursor()
        matched = 0
        
        for i, profile in enumerate(unlinked_profiles, 1):
            github_email = profile['github_email'].lower().strip()
            person_id = email_to_person.get(github_email)
            
            if person_id:
                try:
                    # Link GitHub profile to person
                    update_cursor.execute("""
                        UPDATE github_profile
                        SET person_id = %s
                        WHERE github_profile_id = %s
                        AND person_id IS NULL  -- Don't overwrite existing links
                    """, (person_id, profile['github_profile_id']))
                    
                    if update_cursor.rowcount > 0:
                        self.stats['new_matches_by_email'] += 1
                        matched += 1
                        
                        # Also add the GitHub email to person_email if not already there
                        update_cursor.execute("""
                            INSERT INTO person_email (
                                person_id,
                                email,
                                email_type,
                                is_primary,
                                source
                            ) VALUES (
                                %s, %s, 'personal', false, 'github_match'
                            )
                            ON CONFLICT (person_id, lower(email)) DO NOTHING
                        """, (person_id, github_email))
                        
                        # Commit every 100 records
                        if i % 100 == 0:
                            self.conn.commit()
                            print(f"   Progress: {i:,}/{len(unlinked_profiles):,} - Matched: {matched:,}")
                    
                except Exception as e:
                    self.stats['errors'] += 1
                    self.conn.rollback()
                    continue
        
        # Final commit
        self.conn.commit()
        print(f"\n✅ Matched {matched:,} GitHub profiles by email")
    
    def match_github_by_name_company(self):
        """Match GitHub profiles to people by name + company (conservative)"""
        print("\n🔗 Matching GitHub profiles to people by name + company...")
        
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get unlinked GitHub profiles with name and company
        cursor.execute("""
            SELECT 
                gp.github_profile_id,
                gp.github_name,
                gp.github_company,
                gp.github_username
            FROM github_profile gp
            WHERE gp.person_id IS NULL
            AND gp.github_name IS NOT NULL
            AND gp.github_name != ''
            AND gp.github_company IS NOT NULL
            AND gp.github_company != ''
        """)
        
        unlinked_profiles = cursor.fetchall()
        print(f"   Found {len(unlinked_profiles):,} unlinked profiles with name + company")
        
        update_cursor = self.conn.cursor()
        matched = 0
        ambiguous = 0
        
        for i, profile in enumerate(unlinked_profiles, 1):
            try:
                # Try to find matching person by name and current company
                # Be conservative - only match if there's exactly one match
                cursor.execute("""
                    SELECT p.person_id, p.full_name, c.company_name
                    FROM person p
                    JOIN employment e ON p.person_id = e.person_id
                    JOIN company c ON e.company_id = c.company_id
                    WHERE e.end_date IS NULL  -- Current job
                    AND (
                        LOWER(p.full_name) = LOWER(%s)
                        OR LOWER(p.first_name || ' ' || p.last_name) = LOWER(%s)
                    )
                    AND (
                        LOWER(c.company_name) LIKE LOWER(%s)
                        OR LOWER(%s) LIKE LOWER(c.company_name)
                    )
                    LIMIT 2  -- Get up to 2 to check for ambiguity
                """, (
                    profile['github_name'],
                    profile['github_name'],
                    f"%{profile['github_company']}%",
                    f"%{profile['github_company']}%"
                ))
                
                matches = cursor.fetchall()
                
                if len(matches) == 1:
                    # Exactly one match - safe to link
                    person_id = matches[0]['person_id']
                    
                    update_cursor.execute("""
                        UPDATE github_profile
                        SET person_id = %s
                        WHERE github_profile_id = %s
                        AND person_id IS NULL
                    """, (person_id, profile['github_profile_id']))
                    
                    if update_cursor.rowcount > 0:
                        self.stats['new_matches_by_name_company'] += 1
                        matched += 1
                        
                        if i % 50 == 0:
                            self.conn.commit()
                            print(f"   Progress: {i:,}/{len(unlinked_profiles):,} - Matched: {matched:,}, Ambiguous: {ambiguous}")
                
                elif len(matches) > 1:
                    # Multiple matches - ambiguous, skip for accuracy
                    ambiguous += 1
                    
            except Exception as e:
                self.stats['errors'] += 1
                self.conn.rollback()
                continue
        
        # Final commit
        self.conn.commit()
        print(f"\n✅ Matched {matched:,} GitHub profiles by name+company")
        print(f"   ⚠️  Skipped {ambiguous:,} ambiguous matches (multiple candidates)")
    
    def validate_results(self):
        """Validate matching results"""
        print("\n✅ Validating results...")
        
        cursor = self.conn.cursor()
        
        # Count GitHub profiles
        cursor.execute("""
            SELECT 
                COUNT(*) as total_profiles,
                COUNT(person_id) as linked_profiles,
                COUNT(CASE WHEN person_id IS NULL THEN 1 END) as unlinked_profiles
            FROM github_profile
        """)
        
        result = cursor.fetchone()
        total, linked, unlinked = result
        
        # Count people with GitHub
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id)
            FROM github_profile
            WHERE person_id IS NOT NULL
        """)
        
        people_with_github = cursor.fetchone()[0]
        
        # Count total people
        cursor.execute("SELECT COUNT(*) FROM person")
        total_people = cursor.fetchone()[0]
        
        # Count emails
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT person_id) FROM person_email")
        total_emails, people_with_emails = cursor.fetchone()
        
        print(f"\n📊 RESULTS:")
        print(f"   Total GitHub profiles:         {total:,}")
        print(f"   Linked to people:              {linked:,} ({linked/total*100:.2f}%)")
        print(f"   Unlinked:                      {unlinked:,} ({unlinked/total*100:.2f}%)")
        print(f"   People with GitHub:            {people_with_github:,} of {total_people:,} ({people_with_github/total_people*100:.2f}%)")
        print(f"   Total emails:                  {total_emails:,}")
        print(f"   People with emails:            {people_with_emails:,} ({people_with_emails/total_people*100:.2f}%)")
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
                'github_matching_enrichment',
                'data_enrichment',
                'completed',
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                NOW()
            )
        """, (
            self.stats['github_profiles_processed'],
            self.stats['emails_extracted_from_github'],
            self.stats['new_matches_by_email'] + self.stats['new_matches_by_name_company'],
            self.stats['emails_skipped'],
            psycopg2.extras.Json({
                'new_matches_by_email': self.stats['new_matches_by_email'],
                'new_matches_by_name_company': self.stats['new_matches_by_name_company'],
                'errors': self.stats['errors']
            })
        ))
        
        self.conn.commit()
    
    def print_summary(self):
        """Print enrichment summary"""
        print("\n" + "="*80)
        print("GITHUB MATCHING & EMAIL ENRICHMENT SUMMARY")
        print("="*80)
        print(f"New matches by email:            {self.stats['new_matches_by_email']:,}")
        print(f"New matches by name+company:     {self.stats['new_matches_by_name_company']:,}")
        print(f"Emails extracted from GitHub:    {self.stats['emails_extracted_from_github']:,}")
        print(f"Emails skipped (duplicate):      {self.stats['emails_skipped']:,}")
        print(f"Errors:                          {self.stats['errors']:,}")
        print("="*80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Improve GitHub profile matching and extract emails')
    parser.add_argument('--pg-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--pg-port', default='5432', help='PostgreSQL port')
    parser.add_argument('--pg-db', default='talent', help='PostgreSQL database name')
    parser.add_argument('--pg-user', default=None, help='PostgreSQL user')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("GITHUB PROFILE MATCHING & EMAIL ENRICHMENT")
    print("="*80)
    print(f"PostgreSQL:   {args.pg_user or os.environ.get('USER')}@{args.pg_host}:{args.pg_port}/{args.pg_db}")
    print("="*80 + "\n")
    
    enricher = GitHubMatchingEnricher(
        pg_host=args.pg_host,
        pg_port=args.pg_port,
        pg_db=args.pg_db,
        pg_user=args.pg_user
    )
    
    enricher.connect()
    enricher.extract_github_emails()
    enricher.match_github_by_email()
    enricher.match_github_by_name_company()
    enricher.validate_results()
    enricher.log_results()
    enricher.print_summary()
    
    print("\n✅ GitHub matching and email enrichment complete!")

if __name__ == "__main__":
    main()


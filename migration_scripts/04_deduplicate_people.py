#!/usr/bin/env python3
"""
Person Deduplication Script
Identifies and merges duplicate people in PostgreSQL talent database
Uses moderate strategy: merge on LinkedIn URL OR email match
"""

import sys
import os
import psycopg2
from datetime import datetime
from typing import List, Dict, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from migration_utils import (
    normalize_linkedin_url,
    normalize_email,
    log_migration_event,
    print_progress
)

class PersonDeduplicator:
    def __init__(self, pg_conn_params: dict, dry_run: bool = False):
        self.pg_params = pg_conn_params
        self.dry_run = dry_run
        self.stats = {
            'people_analyzed': 0,
            'duplicates_found': 0,
            'people_merged': 0,
            'emails_transferred': 0,
            'github_profiles_transferred': 0,
            'employment_transferred': 0,
            'education_transferred': 0
        }
        self.duplicate_groups = []
        
    def connect_database(self):
        """Establish PostgreSQL connection"""
        print("📡 Connecting to PostgreSQL...")
        self.pg_conn = psycopg2.connect(**self.pg_params)
        self.pg_conn.autocommit = False
        print("✅ Connection established")
    
    def find_duplicates_by_linkedin(self) -> List[List[str]]:
        """Find people with same normalized LinkedIn URL"""
        print("\n🔍 Finding duplicates by LinkedIn URL...")
        
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                normalized_linkedin_url,
                array_agg(person_id::text ORDER BY refreshed_at DESC NULLS LAST) as person_ids
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
            AND normalized_linkedin_url != ''
            GROUP BY normalized_linkedin_url
            HAVING COUNT(*) > 1
        """)
        
        linkedin_dupes = [row[1] for row in cursor.fetchall()]
        print(f"   Found {len(linkedin_dupes):,} groups of LinkedIn duplicates")
        
        return linkedin_dupes
    
    def find_duplicates_by_email(self) -> List[List[str]]:
        """Find people with same email address"""
        print("\n🔍 Finding duplicates by email...")
        
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                lower(email) as email,
                array_agg(DISTINCT person_id::text) as person_ids
            FROM person_email
            WHERE email IS NOT NULL
            AND email != ''
            GROUP BY lower(email)
            HAVING COUNT(DISTINCT person_id) > 1
        """)
        
        email_dupes = [row[1] for row in cursor.fetchall()]
        print(f"   Found {len(email_dupes):,} groups of email duplicates")
        
        return email_dupes
    
    def consolidate_duplicate_groups(self, linkedin_dupes: List, email_dupes: List) -> List[Set[str]]:
        """
        Consolidate duplicate groups that may overlap
        E.g., if A=B by LinkedIn and B=C by email, then A=B=C
        """
        print("\n🔗 Consolidating duplicate groups...")
        
        # Use union-find to merge overlapping groups
        person_to_group = {}
        groups = []
        
        def find_group(person_id):
            if person_id not in person_to_group:
                new_group = {person_id}
                groups.append(new_group)
                person_to_group[person_id] = new_group
                return new_group
            return person_to_group[person_id]
        
        def merge_groups(group1, group2):
            if group1 == group2:
                return group1
            # Merge smaller into larger
            if len(group1) < len(group2):
                group1, group2 = group2, group1
            group1.update(group2)
            for person_id in group2:
                person_to_group[person_id] = group1
            groups.remove(group2)
            return group1
        
        # Process all duplicate groups
        all_dupes = linkedin_dupes + email_dupes
        
        for dupe_group in all_dupes:
            if len(dupe_group) < 2:
                continue
            
            # Find or create groups for all people in this duplicate set
            first_group = find_group(dupe_group[0])
            for person_id in dupe_group[1:]:
                person_group = find_group(person_id)
                first_group = merge_groups(first_group, person_group)
        
        # Filter to only groups with 2+ people
        final_groups = [g for g in groups if len(g) > 1]
        
        print(f"   Consolidated into {len(final_groups):,} unique duplicate groups")
        print(f"   Total people affected: {sum(len(g) for g in final_groups):,}")
        
        return final_groups
    
    def get_person_data(self, person_id: str) -> Dict:
        """Get all data for a person"""
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                person_id::text,
                full_name,
                first_name,
                last_name,
                linkedin_url,
                normalized_linkedin_url,
                location,
                headline,
                description,
                followers_count,
                refreshed_at
            FROM person
            WHERE person_id = %s::uuid
        """, (person_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'person_id': row[0],
            'full_name': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'linkedin_url': row[4],
            'normalized_linkedin_url': row[5],
            'location': row[6],
            'headline': row[7],
            'description': row[8],
            'followers_count': row[9] or 0,
            'refreshed_at': row[10]
        }
    
    def choose_primary_person(self, person_ids: List[str]) -> str:
        """
        Choose which person record to keep as primary
        Criteria:
        1. Most recent refreshed_at
        2. Most complete data (more non-null fields)
        3. Higher follower count
        """
        people_data = [self.get_person_data(pid) for pid in person_ids]
        people_data = [p for p in people_data if p]  # Remove None
        
        if not people_data:
            return person_ids[0]
        
        def score_person(person):
            score = 0
            # Recency (up to 30 points)
            if person['refreshed_at']:
                score += 30
            # Completeness (up to 50 points)
            non_null_fields = sum(1 for v in person.values() if v not in [None, '', 0])
            score += (non_null_fields / len(person)) * 50
            # Followers (up to 20 points, capped at 1000 followers)
            score += min(person['followers_count'] / 1000 * 20, 20)
            return score
        
        # Sort by score descending
        people_data.sort(key=score_person, reverse=True)
        
        return people_data[0]['person_id']
    
    def merge_people(self, person_ids: List[str], primary_id: str):
        """Merge multiple people into primary person"""
        secondary_ids = [pid for pid in person_ids if pid != primary_id]
        
        if not secondary_ids:
            return
        
        cursor = self.pg_conn.cursor()
        
        # Transfer emails
        for secondary_id in secondary_ids:
            cursor.execute("""
                UPDATE person_email
                SET person_id = %s::uuid
                WHERE person_id = %s::uuid
                AND lower(email) NOT IN (
                    SELECT lower(email) FROM person_email WHERE person_id = %s::uuid
                )
            """, (primary_id, secondary_id, primary_id))
            self.stats['emails_transferred'] += cursor.rowcount
        
        # Transfer GitHub profiles
        for secondary_id in secondary_ids:
            cursor.execute("""
                UPDATE github_profile
                SET person_id = %s::uuid
                WHERE person_id = %s::uuid
                AND github_username NOT IN (
                    SELECT github_username FROM github_profile WHERE person_id = %s::uuid
                )
            """, (primary_id, secondary_id, primary_id))
            self.stats['github_profiles_transferred'] += cursor.rowcount
        
        # Transfer employment records
        for secondary_id in secondary_ids:
            cursor.execute("""
                UPDATE employment
                SET person_id = %s::uuid
                WHERE person_id = %s::uuid
                AND NOT EXISTS (
                    SELECT 1 FROM employment e2
                    WHERE e2.person_id = %s::uuid
                    AND e2.company_id = employment.company_id
                    AND e2.title = employment.title
                    AND e2.start_date = employment.start_date
                )
            """, (primary_id, secondary_id, primary_id))
            self.stats['employment_transferred'] += cursor.rowcount
        
        # Transfer education records
        for secondary_id in secondary_ids:
            cursor.execute("""
                UPDATE education
                SET person_id = %s::uuid
                WHERE person_id = %s::uuid
            """, (primary_id, secondary_id))
            self.stats['education_transferred'] += cursor.rowcount
        
        # Delete secondary person records
        for secondary_id in secondary_ids:
            cursor.execute("""
                DELETE FROM person
                WHERE person_id = %s::uuid
            """, (secondary_id,))
        
        self.stats['people_merged'] += len(secondary_ids)
    
    def deduplicate(self):
        """Main deduplication process"""
        print("\n" + "=" * 80)
        print("PERSON DEDUPLICATION - PostgreSQL talent database")
        print("Strategy: Moderate (merge on LinkedIn URL OR email match)")
        print("=" * 80)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        self.connect_database()
        
        log_migration_event(
            self.pg_conn,
            'person_deduplication',
            'deduplication',
            'started'
        )
        
        try:
            # Find duplicates
            linkedin_dupes = self.find_duplicates_by_linkedin()
            email_dupes = self.find_duplicates_by_email()
            
            # Consolidate overlapping groups
            duplicate_groups = self.consolidate_duplicate_groups(linkedin_dupes, email_dupes)
            self.stats['duplicates_found'] = len(duplicate_groups)
            
            if not duplicate_groups:
                print("\n✅ No duplicates found!")
                log_migration_event(
                    self.pg_conn,
                    'person_deduplication',
                    'deduplication',
                    'completed',
                    metadata=self.stats
                )
                return
            
            # Process each duplicate group
            print(f"\n🔄 Processing {len(duplicate_groups):,} duplicate groups...")
            
            for i, group in enumerate(duplicate_groups, 1):
                self.stats['people_analyzed'] += len(group)
                person_ids = list(group)
                
                # Choose primary person
                primary_id = self.choose_primary_person(person_ids)
                
                # Merge duplicates
                if not self.dry_run:
                    self.merge_people(person_ids, primary_id)
                
                # Progress update
                if i % 10 == 0:
                    print_progress(i, len(duplicate_groups), 'Merging')
                    if not self.dry_run:
                        self.pg_conn.commit()
            
            if not self.dry_run:
                self.pg_conn.commit()
            
            print_progress(len(duplicate_groups), len(duplicate_groups), 'Merging')
            
            # Log success
            log_migration_event(
                self.pg_conn,
                'person_deduplication',
                'deduplication',
                'completed',
                records_processed=self.stats['people_analyzed'],
                records_updated=self.stats['people_merged'],
                metadata=self.stats
            )
            
            self.print_summary()
            
        except Exception as e:
            if not self.dry_run:
                self.pg_conn.rollback()
            print(f"\n❌ Error during deduplication: {e}")
            
            log_migration_event(
                self.pg_conn,
                'person_deduplication',
                'deduplication',
                'failed',
                error_message=str(e),
                metadata=self.stats
            )
            
            raise
        
        finally:
            self.pg_conn.close()
    
    def print_summary(self):
        """Print deduplication summary"""
        print("\n" + "=" * 80)
        print("DEDUPLICATION SUMMARY")
        print("=" * 80)
        print(f"People analyzed:           {self.stats['people_analyzed']:,}")
        print(f"Duplicate groups found:    {self.stats['duplicates_found']:,}")
        print(f"People merged (removed):   {self.stats['people_merged']:,}")
        print(f"\nData transferred:")
        print(f"  Emails:                  {self.stats['emails_transferred']:,}")
        print(f"  GitHub profiles:         {self.stats['github_profiles_transferred']:,}")
        print(f"  Employment records:      {self.stats['employment_transferred']:,}")
        print(f"  Education records:       {self.stats['education_transferred']:,}")
        print("=" * 80)
        
        if self.dry_run:
            print("\n🔍 DRY RUN - No actual changes were made")
        else:
            print(f"\n✅ Deduplication complete!")
            print(f"   Net reduction: {self.stats['people_merged']:,} people")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deduplicate people in PostgreSQL talent database')
    parser.add_argument('--pg-host', default='localhost',
                       help='PostgreSQL host')
    parser.add_argument('--pg-port', default='5432',
                       help='PostgreSQL port')
    parser.add_argument('--pg-db', default='talent',
                       help='PostgreSQL database name')
    parser.add_argument('--pg-user', default=os.environ.get('USER'),
                       help='PostgreSQL user')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run without actually merging')
    
    args = parser.parse_args()
    
    pg_params = {
        'host': args.pg_host,
        'port': args.pg_port,
        'database': args.pg_db,
        'user': args.pg_user
    }
    
    deduplicator = PersonDeduplicator(pg_params, dry_run=args.dry_run)
    deduplicator.deduplicate()


if __name__ == '__main__':
    main()


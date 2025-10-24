#!/usr/bin/env python3
"""
Link GitHub Profiles to Person Records

This script creates person records for unlinked GitHub profiles and matches
existing profiles to existing people where possible.

Matching Strategy:
1. Exact email match
2. GitHub username match (if person has github_username field)
3. Name + company match (fuzzy)
4. Create new person if no match found
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProfileLinker:
    """Links GitHub profiles to person records"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        # Stats
        self.stats = {
            'profiles_checked': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'new_persons_created': 0,
            'skipped': 0
        }
    
    def find_matching_person(self, profile: Dict) -> Optional[str]:
        """Find existing person record that matches this profile"""
        
        # Strategy 1: Exact email match via person_email table
        if profile.get('github_email'):
            self.cursor.execute("""
                SELECT person_id FROM person_email
                WHERE email = %s
                LIMIT 1
            """, (profile['github_email'],))
            
            result = self.cursor.fetchone()
            if result:
                logger.info(f"  ✓ Email match: {profile['github_username']}")
                self.stats['exact_matches'] += 1
                return result['person_id']
        
        # Strategy 2: GitHub username collision check
        # Check if this username is already linked to another person
        self.cursor.execute("""
            SELECT p.person_id
            FROM person p
            JOIN github_profile gp ON p.person_id = gp.person_id
            WHERE gp.github_username = %s
              AND gp.github_profile_id != %s
            LIMIT 1
        """, (profile['github_username'], profile['github_profile_id']))
        
        result = self.cursor.fetchone()
        if result:
            logger.info(f"  ✓ Username collision: {profile['github_username']} already linked")
            return None  # Don't link if username is taken
        
        # Strategy 3: Name match (simple)
        if profile.get('github_name'):
            self.cursor.execute("""
                SELECT person_id
                FROM person
                WHERE LOWER(full_name) = LOWER(%s)
                LIMIT 1
            """, (profile['github_name'],))
            
            result = self.cursor.fetchone()
            if result:
                logger.info(f"  ≈ Name match: {profile['github_username']}")
                self.stats['fuzzy_matches'] += 1
                return result['person_id']
        
        # No match found
        return None
    
    def create_person_from_profile(self, profile: Dict) -> str:
        """Create a new person record from GitHub profile"""
        
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would create person for: {profile['github_username']}")
            self.stats['new_persons_created'] += 1
            return "dry-run-person-id"
        
        # Parse full name into first/last if possible
        full_name = profile.get('github_name') or profile['github_username']
        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else full_name
        last_name = name_parts[1] if len(name_parts) > 1 else None
        
        # Build headline from bio or company
        headline = None
        if profile.get('github_company'):
            headline = f"Developer at {profile['github_company']}"
        elif profile.get('bio'):
            # Take first 100 chars of bio
            headline = profile['bio'][:100]
        
        # Create person record with person_id from github_profile
        self.cursor.execute("""
            INSERT INTO person (
                person_id,
                full_name,
                first_name,
                last_name,
                location,
                headline,
                description
            )
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s)
            RETURNING person_id
        """, (
            full_name,
            first_name,
            last_name,
            profile.get('location'),
            headline,
            profile.get('bio')
        ))
        
        person_id = self.cursor.fetchone()['person_id']
        
        # If profile has email, create person_email record
        if profile.get('github_email'):
            try:
                self.cursor.execute("""
                    INSERT INTO person_email (person_id, email, email_type, source)
                    VALUES (%s, %s, 'github', 'github_discovery')
                """, (person_id, profile['github_email']))
            except Exception:
                # Email might already exist for this person, that's okay
                pass
        
        logger.info(f"  ✨ Created person: {profile['github_username']}")
        self.stats['new_persons_created'] += 1
        
        return person_id
    
    def link_profile_to_person(self, profile_id: str, person_id: str):
        """Update github_profile with person_id"""
        
        if self.dry_run:
            return
        
        self.cursor.execute("""
            UPDATE github_profile
            SET person_id = %s,
                updated_at = NOW()
            WHERE github_profile_id = %s
        """, (person_id, profile_id))
    
    def process_unlinked_profiles(self, limit: Optional[int] = None):
        """Process all unlinked GitHub profiles"""
        
        logger.info("="*80)
        logger.info("🔗 LINKING GITHUB PROFILES TO PEOPLE")
        logger.info("="*80)
        
        # Get unlinked profiles
        query = """
            SELECT 
                github_profile_id,
                github_username,
                github_name,
                github_email,
                github_company,
                location,
                bio,
                followers,
                created_at
            FROM github_profile
            WHERE person_id IS NULL
            ORDER BY 
                followers DESC NULLS LAST,
                created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        self.cursor.execute(query)
        profiles = self.cursor.fetchall()
        
        logger.info(f"\nFound {len(profiles)} unlinked profiles to process")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made\n")
        
        # Process each profile
        for i, profile in enumerate(profiles, 1):
            self.stats['profiles_checked'] += 1
            
            if i <= 20 or i % 100 == 0:  # Log first 20, then every 100
                logger.info(f"\n[{i}/{len(profiles)}] Processing: {profile['github_username']}")
            
            try:
                # Try to find matching person
                person_id = self.find_matching_person(profile)
                
                # If no match, create new person
                if not person_id:
                    person_id = self.create_person_from_profile(profile)
                
                # Link profile to person
                if person_id:
                    self.link_profile_to_person(
                        profile['github_profile_id'],
                        person_id
                    )
                
                # Commit every 50 profiles
                if i % 50 == 0 and not self.dry_run:
                    self.conn.commit()
                    logger.info(f"  💾 Committed {i} profiles")
                    
            except Exception as e:
                logger.error(f"  ❌ Error processing {profile['github_username']}: {e}")
                self.stats['skipped'] += 1
                self.conn.rollback()
        
        # Final commit
        if not self.dry_run:
            self.conn.commit()
        
        # Print stats
        logger.info("\n" + "="*80)
        logger.info("📊 LINKING STATISTICS")
        logger.info("="*80)
        logger.info(f"Profiles checked:       {self.stats['profiles_checked']}")
        logger.info(f"Exact matches:          {self.stats['exact_matches']}")
        logger.info(f"Fuzzy matches:          {self.stats['fuzzy_matches']}")
        logger.info(f"New persons created:    {self.stats['new_persons_created']}")
        logger.info(f"Skipped (errors):       {self.stats['skipped']}")
        logger.info("="*80)
        
        if self.dry_run:
            logger.info("\n⚠️  This was a DRY RUN - no changes were made")
            logger.info("Run without --dry-run to apply changes")
    
    def close(self):
        """Clean up database connections"""
        self.cursor.close()
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(
        description='Link GitHub profiles to person records'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of profiles to process (for testing)'
    )
    
    args = parser.parse_args()
    
    linker = ProfileLinker(dry_run=args.dry_run)
    
    try:
        linker.process_unlinked_profiles(limit=args.limit)
    finally:
        linker.close()

if __name__ == '__main__':
    main()


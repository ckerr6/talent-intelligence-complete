#!/usr/bin/env python3
"""
Merge Promoted GitHub Profile Duplicates
=========================================
When we promoted GitHub profiles to people, we created new person records.
However, some of these people already existed in the database (from previous imports).

This script finds duplicate person records where:
- One has a GitHub profile (from promotion)
- One has employment/other data (from previous imports)
- They have the same full_name

Then it merges them by:
1. Moving the GitHub profile link to the existing (richer) person record
2. Deleting the duplicate promoted person record

Author: AI Assistant
Date: October 23, 2025
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import get_db_connection, Config

class GithubDuplicateMerger:
    def __init__(self, dry_run=False):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = False  # Use transactions
        self.cursor = self.conn.cursor()
        self.dry_run = dry_run
        
        self.stats = {
            'duplicates_found': 0,
            'github_profiles_moved': 0,
            'person_records_deleted': 0,
            'errors': [],
            'merged_examples': []
        }
        
        mode = "DRY RUN" if dry_run else "LIVE RUN"
        print(f"\n{'='*80}")
        print(f"MERGE PROMOTED GITHUB PROFILE DUPLICATES ({mode})")
        print(f"{'='*80}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
    
    def find_duplicates(self) -> List[Dict]:
        """
        Find person records that are duplicates:
        - Same full_name
        - One has GitHub profile (from promotion)
        - One has employment/other data
        """
        print("🔍 Finding duplicate person records...\n")
        
        self.cursor.execute("""
            WITH name_counts AS (
                SELECT full_name, COUNT(*) as count
                FROM person
                WHERE full_name IS NOT NULL
                    AND TRIM(full_name) != ''
                GROUP BY full_name
                HAVING COUNT(*) > 1
            ),
            person_enrichment AS (
                SELECT 
                    p.person_id::text,
                    p.full_name,
                    p.linkedin_url,
                    p.headline,
                    p.description,
                    gp.github_profile_id::text,
                    gp.github_username,
                    (SELECT COUNT(*) FROM employment WHERE person_id = p.person_id) as employment_count,
                    (SELECT COUNT(*) FROM person_email WHERE person_id = p.person_id) as email_count,
                    (SELECT COUNT(*) FROM education WHERE person_id = p.person_id) as education_count,
                    (SELECT COUNT(*) FROM twitter_profile WHERE person_id = p.person_id) as twitter_count,
                    -- Score: higher = more data
                    (
                        CASE WHEN p.linkedin_url IS NOT NULL THEN 100 ELSE 0 END +
                        CASE WHEN p.headline IS NOT NULL THEN 10 ELSE 0 END +
                        (SELECT COUNT(*) * 50 FROM employment WHERE person_id = p.person_id) +
                        (SELECT COUNT(*) * 20 FROM person_email WHERE person_id = p.person_id) +
                        (SELECT COUNT(*) * 30 FROM education WHERE person_id = p.person_id) +
                        (SELECT COUNT(*) * 25 FROM twitter_profile WHERE person_id = p.person_id)
                    ) as enrichment_score
                FROM person p
                LEFT JOIN github_profile gp ON p.person_id = gp.person_id
                WHERE p.full_name IN (SELECT full_name FROM name_counts)
            )
            SELECT 
                full_name,
                COUNT(*) as record_count,
                json_agg(
                    json_build_object(
                        'person_id', person_id,
                        'linkedin_url', linkedin_url,
                        'headline', headline,
                        'github_profile_id', github_profile_id,
                        'github_username', github_username,
                        'employment_count', employment_count,
                        'email_count', email_count,
                        'education_count', education_count,
                        'twitter_count', twitter_count,
                        'enrichment_score', enrichment_score
                    ) ORDER BY enrichment_score DESC
                ) as records
            FROM person_enrichment
            GROUP BY full_name
            ORDER BY COUNT(*) DESC, full_name
        """)
        
        duplicate_groups = []
        for row in self.cursor.fetchall():
            full_name = row['full_name']
            records = row['records']
            
            # Check if this is a merge candidate:
            # - At least one record has GitHub profile
            # - At least one record has other data
            has_github = any(r['github_profile_id'] for r in records)
            has_enrichment = any(r['enrichment_score'] > 0 for r in records)
            
            if has_github and len(records) > 1:
                duplicate_groups.append({
                    'full_name': full_name,
                    'records': records
                })
        
        self.stats['duplicates_found'] = len(duplicate_groups)
        print(f"   Found {len(duplicate_groups)} duplicate groups to merge")
        
        return duplicate_groups
    
    def merge_duplicate_group(self, group: Dict) -> bool:
        """
        Merge a group of duplicate person records
        
        Strategy:
        1. Find the "best" record (highest enrichment score)
        2. Move all GitHub profiles to the best record
        3. Delete the other records
        """
        full_name = group['full_name']
        records = group['records']
        
        # Sort by enrichment score (already sorted, but make sure)
        records_sorted = sorted(records, key=lambda x: x['enrichment_score'], reverse=True)
        
        # Best record = highest enrichment score
        keep_record = records_sorted[0]
        delete_records = records_sorted[1:]
        
        try:
            # Move GitHub profiles from delete records to keep record
            for delete_rec in delete_records:
                if delete_rec['github_profile_id']:
                    if not self.dry_run:
                        self.cursor.execute("""
                            UPDATE github_profile
                            SET person_id = %s::uuid
                            WHERE github_profile_id = %s::uuid
                        """, (keep_record['person_id'], delete_rec['github_profile_id']))
                        
                        self.stats['github_profiles_moved'] += 1
                    else:
                        self.stats['github_profiles_moved'] += 1
            
            # Delete the duplicate records
            for delete_rec in delete_records:
                if not self.dry_run:
                    # Check if this record has ANY data we need to preserve
                    if (delete_rec['employment_count'] > 0 or 
                        delete_rec['email_count'] > 0 or
                        delete_rec['education_count'] > 0 or
                        delete_rec['twitter_count'] > 0):
                        print(f"   ⚠️  Skipping delete of {full_name} ({delete_rec['person_id']}) - has additional data")
                        continue
                    
                    self.cursor.execute("""
                        DELETE FROM person
                        WHERE person_id = %s::uuid
                    """, (delete_rec['person_id'],))
                    
                    self.stats['person_records_deleted'] += 1
                else:
                    # In dry run, only count if no additional data
                    if not (delete_rec['employment_count'] > 0 or 
                           delete_rec['email_count'] > 0 or
                           delete_rec['education_count'] > 0 or
                           delete_rec['twitter_count'] > 0):
                        self.stats['person_records_deleted'] += 1
            
            # Track example
            if len(self.stats['merged_examples']) < 20:
                self.stats['merged_examples'].append({
                    'full_name': full_name,
                    'kept_person_id': keep_record['person_id'],
                    'deleted_count': len(delete_records),
                    'github_moved': any(r['github_profile_id'] for r in delete_records)
                })
            
            return True
            
        except Exception as e:
            error_msg = f"Error merging {full_name}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"   ❌ {error_msg}")
            return False
    
    def process_duplicates(self):
        """Main processing loop"""
        duplicate_groups = self.find_duplicates()
        
        if not duplicate_groups:
            print("✅ No duplicates to merge!")
            return
        
        print(f"\n🔄 Merging duplicate records...\n")
        
        batch_count = 0
        batch_size = 50
        
        for group in duplicate_groups:
            success = self.merge_duplicate_group(group)
            
            if success and not self.dry_run:
                batch_count += 1
                if batch_count >= batch_size:
                    self.conn.commit()
                    print(f"   ✅ Committed batch ({self.stats['person_records_deleted']} records deleted so far)")
                    batch_count = 0
        
        # Final commit
        if not self.dry_run and batch_count > 0:
            self.conn.commit()
            print(f"   ✅ Final commit")
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate and display merge report"""
        print(f"\n{'='*80}")
        print(f"MERGE COMPLETE - FINAL REPORT")
        print(f"{'='*80}")
        
        print(f"\n📊 RESULTS:")
        print(f"   Duplicate Groups Found: {self.stats['duplicates_found']}")
        print(f"   GitHub Profiles Moved: {self.stats['github_profiles_moved']}")
        print(f"   Duplicate Person Records Deleted: {self.stats['person_records_deleted']}")
        
        if self.stats['merged_examples']:
            print(f"\n   Examples of merged records:")
            for example in self.stats['merged_examples'][:20]:
                print(f"      • {example['full_name']}")
                print(f"        Kept: {example['kept_person_id']}")
                print(f"        Deleted: {example['deleted_count']} duplicate(s)")
                if example['github_moved']:
                    print(f"        ✓ GitHub profile moved to kept record")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for i, error in enumerate(self.stats['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more errors")
        
        # Database totals
        if not self.dry_run:
            try:
                self.cursor.execute("SELECT COUNT(*) as count FROM person")
                total_people = self.cursor.fetchone()['count']
                
                self.cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM github_profile 
                    WHERE person_id IS NOT NULL
                """)
                linked_github = self.cursor.fetchone()['count']
                
                print(f"\n📈 DATABASE TOTALS:")
                print(f"   Total People: {total_people:,}")
                print(f"   GitHub Profiles Linked to People: {linked_github:,}")
            except Exception as e:
                print(f"   ⚠️  Could not retrieve totals: {e}")
        
        print(f"\n{'='*80}\n")
        
        # Write report to file
        report_filename = f"reports/github_duplicate_merge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = Path(__file__).parent.parent.parent / report_filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"GitHub Duplicate Merge Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE RUN'}\n\n")
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key not in ['errors', 'merged_examples']:
                    f.write(f"  {key}: {value}\n")
            
            if self.stats['merged_examples']:
                f.write(f"\nMerged Records Examples:\n")
                for example in self.stats['merged_examples']:
                    f.write(f"  - {example['full_name']}: kept {example['kept_person_id']}, "
                           f"deleted {example['deleted_count']}\n")
            
            if self.stats['errors']:
                f.write(f"\nErrors:\n")
                for error in self.stats['errors']:
                    f.write(f"  - {error}\n")
        
        print(f"📄 Full report saved to: {report_filename}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            if not self.dry_run:
                self.conn.commit()
            self.conn.close()

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Merge duplicate person records from GitHub promotion'
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--live', action='store_true',
                       help='Actually perform the merge (default is dry-run)')
    
    args = parser.parse_args()
    
    # Default to dry-run unless --live specified
    dry_run = not args.live
    
    if not dry_run:
        print(f"\n⚠️  WARNING: LIVE MODE - Will merge duplicate records!")
        print(f"This will:")
        print(f"  - Move GitHub profiles to the best person record")
        print(f"  - Delete duplicate person records with no additional data")
        print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
        
        response = input(f"\nProceed with LIVE merge? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return 0
    else:
        print(f"\n📋 DRY RUN MODE - No changes will be made")
        print(f"Use --live to actually perform the merge\n")
    
    try:
        merger = GithubDuplicateMerger(dry_run=dry_run)
        merger.process_duplicates()
        merger.generate_report()
        merger.close()
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


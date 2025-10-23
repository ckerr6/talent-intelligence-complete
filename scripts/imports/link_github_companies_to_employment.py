#!/usr/bin/env python3
"""
Link GitHub Companies to Employment Records
============================================
Creates employment records for people based on their GitHub company affiliation.

Strategy:
- Match github_profile.github_company to company.company_name (normalized)
- Create employment records where they don't already exist
- Mark as current employment (no end_date)
- Add source tracking note

Author: AI Assistant
Date: October 23, 2025
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import get_db_connection, Config

class GitHubCompanyLinker:
    def __init__(self, dry_run=False):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = False  # Use transactions
        self.cursor = self.conn.cursor()
        self.dry_run = dry_run
        
        self.stats = {
            'total_github_companies': 0,
            'matched_companies': 0,
            'people_to_link': 0,
            'already_have_employment': 0,
            'new_employment_created': 0,
            'errors': [],
            'top_companies': []
        }
        
        mode = "DRY RUN" if dry_run else "LIVE RUN"
        print(f"\n{'='*80}")
        print(f"LINK GITHUB COMPANIES TO EMPLOYMENT ({mode})")
        print(f"{'='*80}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
    
    def analyze_matches(self):
        """Analyze potential matches before processing"""
        print("🔍 Analyzing GitHub company matches...\n")
        
        self.cursor.execute("""
            WITH github_companies AS (
                SELECT 
                    gp.github_profile_id,
                    gp.person_id,
                    gp.github_username,
                    LOWER(TRIM(gp.github_company)) as normalized_company,
                    gp.github_company as original_company
                FROM github_profile gp
                WHERE gp.github_company IS NOT NULL 
                    AND TRIM(gp.github_company) != ''
                    AND gp.person_id IS NOT NULL
            ),
            company_names AS (
                SELECT 
                    company_id,
                    company_name,
                    LOWER(TRIM(company_name)) as normalized_name
                FROM company
            )
            SELECT 
                cn.company_id::text,
                cn.company_name,
                COUNT(DISTINCT gc.person_id) as people_to_link,
                COUNT(DISTINCT CASE 
                    WHEN e.employment_id IS NOT NULL THEN gc.person_id 
                END) as already_have_employment,
                COUNT(DISTINCT CASE 
                    WHEN e.employment_id IS NULL THEN gc.person_id 
                END) as new_employment_records
            FROM github_companies gc
            JOIN company_names cn ON gc.normalized_company = cn.normalized_name
            LEFT JOIN employment e ON gc.person_id = e.person_id AND cn.company_id = e.company_id
            GROUP BY cn.company_id, cn.company_name
            HAVING COUNT(DISTINCT CASE WHEN e.employment_id IS NULL THEN gc.person_id END) > 0
            ORDER BY new_employment_records DESC
        """)
        
        matches = [dict(row) for row in self.cursor.fetchall()]
        
        self.stats['matched_companies'] = len(matches)
        self.stats['people_to_link'] = sum(m['people_to_link'] for m in matches)
        self.stats['already_have_employment'] = sum(m['already_have_employment'] for m in matches)
        self.stats['new_employment_created'] = sum(m['new_employment_records'] for m in matches)
        
        # Store top 20 for reporting
        self.stats['top_companies'] = matches[:20]
        
        print(f"   Matched Companies: {self.stats['matched_companies']:,}")
        print(f"   People with Matched Companies: {self.stats['people_to_link']:,}")
        print(f"   Already Have Employment: {self.stats['already_have_employment']:,}")
        print(f"   New Employment to Create: {self.stats['new_employment_created']:,}")
        
        return matches
    
    def create_employment_links(self):
        """Create employment records for matched GitHub companies"""
        print(f"\n🔄 Creating employment links...\n")
        
        # Get all matches that need employment records created
        self.cursor.execute("""
            WITH github_companies AS (
                SELECT 
                    gp.github_profile_id::text,
                    gp.person_id::text,
                    gp.github_username,
                    LOWER(TRIM(gp.github_company)) as normalized_company,
                    gp.github_company as original_company
                FROM github_profile gp
                WHERE gp.github_company IS NOT NULL 
                    AND TRIM(gp.github_company) != ''
                    AND gp.person_id IS NOT NULL
            ),
            company_names AS (
                SELECT 
                    company_id::text,
                    company_name,
                    LOWER(TRIM(company_name)) as normalized_name
                FROM company
            )
            SELECT 
                gc.person_id,
                gc.github_username,
                cn.company_id,
                cn.company_name,
                gc.original_company as github_company
            FROM github_companies gc
            JOIN company_names cn ON gc.normalized_company = cn.normalized_name
            LEFT JOIN employment e ON gc.person_id::uuid = e.person_id 
                                   AND cn.company_id::uuid = e.company_id
            WHERE e.employment_id IS NULL
            ORDER BY cn.company_name, gc.github_username
        """)
        
        links = [dict(row) for row in self.cursor.fetchall()]
        
        print(f"   Processing {len(links):,} employment records...")
        
        if not self.dry_run:
            batch_count = 0
            batch_size = 100
            created_count = 0
            
            for link in links:
                try:
                    # Create employment record
                    self.cursor.execute("""
                        INSERT INTO employment (
                            employment_id,
                            person_id,
                            company_id,
                            source_text_ref,
                            date_precision
                        )
                        VALUES (
                            gen_random_uuid(),
                            %s::uuid,
                            %s::uuid,
                            'github_company',
                            'unknown'
                        )
                        RETURNING employment_id
                    """, (link['person_id'], link['company_id']))
                    
                    result = self.cursor.fetchone()
                    if result:
                        created_count += 1
                        batch_count += 1
                        
                        if batch_count >= batch_size:
                            self.conn.commit()
                            print(f"   ✅ Committed batch ({created_count:,} created so far)")
                            batch_count = 0
                    
                except Exception as e:
                    error_msg = f"Error creating employment for {link['github_username']} @ {link['company_name']}: {e}"
                    self.stats['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            # Final commit
            if batch_count > 0:
                self.conn.commit()
                print(f"   ✅ Final commit")
            
            self.stats['new_employment_created'] = created_count
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate and display linking report"""
        print(f"\n{'='*80}")
        print(f"LINKING COMPLETE - FINAL REPORT")
        print(f"{'='*80}")
        
        print(f"\n📊 RESULTS:")
        print(f"   Matched Companies: {self.stats['matched_companies']:,}")
        print(f"   People with Matched Companies: {self.stats['people_to_link']:,}")
        print(f"   Already Had Employment: {self.stats['already_have_employment']:,}")
        print(f"   New Employment Records Created: {self.stats['new_employment_created']:,}")
        
        if self.stats['top_companies']:
            print(f"\n   Top 20 Companies by New Employment Records:")
            for i, company in enumerate(self.stats['top_companies'], 1):
                print(f"      {i:2d}. {company['company_name']:<30s} "
                      f"{company['new_employment_records']:4d} new | "
                      f"{company['already_have_employment']:4d} existing")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for i, error in enumerate(self.stats['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more errors")
        
        # Database totals
        if not self.dry_run:
            try:
                self.cursor.execute("""
                    SELECT COUNT(*) as count FROM employment WHERE source_text_ref = 'github_company'
                """)
                total_github_employment = self.cursor.fetchone()['count']
                
                self.cursor.execute("SELECT COUNT(*) as count FROM employment")
                total_employment = self.cursor.fetchone()['count']
                
                print(f"\n📈 DATABASE TOTALS:")
                print(f"   Total Employment Records: {total_employment:,}")
                print(f"   From GitHub Company: {total_github_employment:,}")
                print(f"   From GitHub Percentage: {100 * total_github_employment / total_employment:.1f}%")
            except Exception as e:
                print(f"   ⚠️  Could not retrieve totals: {e}")
        
        print(f"\n{'='*80}\n")
        
        # Write report to file
        report_filename = f"reports/github_company_employment_link_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = Path(__file__).parent.parent.parent / report_filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"GitHub Company to Employment Linking Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE RUN'}\n\n")
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key not in ['errors', 'top_companies']:
                    f.write(f"  {key}: {value}\n")
            
            if self.stats['top_companies']:
                f.write(f"\nTop Companies:\n")
                for company in self.stats['top_companies']:
                    f.write(f"  - {company['company_name']}: {company['new_employment_records']} new, "
                           f"{company['already_have_employment']} existing\n")
            
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
        description='Link GitHub company affiliations to employment records'
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--live', action='store_true',
                       help='Actually create the employment records (default is dry-run)')
    
    args = parser.parse_args()
    
    # Default to dry-run unless --live specified
    dry_run = not args.live
    
    if not dry_run:
        print(f"\n⚠️  WARNING: LIVE MODE - Will create employment records!")
        print(f"This will:")
        print(f"  - Create employment records for people with matching GitHub companies")
        print(f"  - Link ~5,700 people to companies based on GitHub affiliation")
        print(f"  - Mark employment source as 'github_company'")
        print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
        
        response = input(f"\nProceed with LIVE linking? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return 0
    else:
        print(f"\n📋 DRY RUN MODE - No changes will be made")
        print(f"Use --live to actually create the employment records\n")
    
    try:
        linker = GitHubCompanyLinker(dry_run=dry_run)
        linker.analyze_matches()
        linker.create_employment_links()
        linker.generate_report()
        linker.close()
        
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


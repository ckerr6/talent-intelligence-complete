#!/usr/bin/env python3
"""
Promote GitHub Profiles to People Records
==========================================
Converts orphaned GitHub profiles (person_id = NULL) into person records.

STRATEGY: Three-tier promotion based on confidence level

Tier 1 (Auto-promote - High Confidence):
- Has contributions to ANY tracked company repository
- OR has >100 followers  
- OR has github_name AND (email OR location)

Tier 2 (Auto-promote - Medium Confidence):
- Has github_company matching a tracked company
- OR has >10 public repos
- OR has bio mentioning crypto/Web3 keywords

Tier 3 (Skip - Low Confidence):
- No contributions, no company, low activity
- Likely bots or inactive accounts

RATIONALE:
In crypto/Web3, pseudonymity is common. GitHub username = professional identity.
"0age", "transmissions11", etc. ARE their names in this space.

Author: AI Assistant
Date: October 23, 2025
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import get_db_connection, Config

# Crypto/Web3 keywords for Tier 2 detection
CRYPTO_KEYWORDS = [
    'blockchain', 'crypto', 'ethereum', 'solidity', 'web3', 'defi',
    'smart contract', 'dapp', 'nft', 'dao', 'protocol', 'trustless',
    'decentralized', 'layer 2', 'l2', 'zero knowledge', 'zkp'
]

class GitHubProfilePromoter:
    def __init__(self, dry_run=False):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = False  # Use transactions for safety
        self.cursor = self.conn.cursor()
        self.dry_run = dry_run
        
        # Statistics tracking
        self.stats = {
            'total_orphaned_profiles': 0,
            'tier1_contributors': 0,
            'tier1_high_followers': 0,
            'tier1_has_identity': 0,
            'tier2_company_match': 0,
            'tier2_active_developer': 0,
            'tier2_crypto_bio': 0,
            'tier3_skipped': 0,
            'people_created': 0,
            'profiles_linked': 0,
            'emails_added': 0,
            'errors': [],
            'promoted_samples': []
        }
        
        # Cache of tracked companies
        self.tracked_companies = set()
        self._load_tracked_companies()
        
        mode = "DRY RUN" if dry_run else "LIVE RUN"
        print(f"\n{'='*80}")
        print(f"GITHUB PROFILE PROMOTION TO PEOPLE ({mode})")
        print(f"{'='*80}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
    
    def _load_tracked_companies(self):
        """Load company names we track"""
        self.cursor.execute("""
            SELECT LOWER(TRIM(company_name)) as name
            FROM company
            WHERE company_name IS NOT NULL
        """)
        
        for row in self.cursor.fetchall():
            self.tracked_companies.add(row['name'])
        
        print(f"📦 Loaded {len(self.tracked_companies):,} tracked companies")
    
    def should_promote_to_person(self, profile: Dict, contribution_count: int) -> Tuple[bool, str, str]:
        """
        Determine if GitHub profile should be promoted to person record
        
        Args:
            profile: GitHub profile data
            contribution_count: Number of contributions to tracked repos
            
        Returns:
            (should_promote, tier, reason)
        """
        # Tier 1: High Confidence - Definite people
        if contribution_count > 0:
            return True, "tier1", f"contributor ({contribution_count} contributions)"
        
        if profile.get('followers', 0) > 100:
            return True, "tier1", f"high_followers ({profile['followers']} followers)"
        
        if profile.get('github_name') and (profile.get('github_email') or profile.get('location')):
            return True, "tier1", "has_identity (name + email/location)"
        
        # Tier 2: Medium Confidence - Probably people
        github_company = profile.get('github_company') or ''
        github_company = github_company.lower().strip()
        if github_company and github_company in self.tracked_companies:
            return True, "tier2", f"company_match ({profile['github_company']})"
        
        if profile.get('public_repos', 0) > 10:
            return True, "tier2", f"active_developer ({profile['public_repos']} repos)"
        
        # Check for crypto/Web3 bio
        bio = (profile.get('bio') or '').lower()
        if bio and any(keyword in bio for keyword in CRYPTO_KEYWORDS):
            return True, "tier2", "crypto_bio"
        
        # Tier 3: Low Confidence - Skip
        return False, "tier3", "low_activity"
    
    def get_orphaned_profiles(self) -> List[Dict]:
        """Get all GitHub profiles without person_id"""
        print("\n🔍 Finding orphaned GitHub profiles...\n")
        
        self.cursor.execute("""
            SELECT 
                gp.github_profile_id::text,
                gp.github_username,
                gp.github_name,
                gp.github_email,
                gp.github_company,
                gp.location,
                gp.bio,
                gp.followers,
                gp.following,
                gp.public_repos,
                gp.blog,
                gp.twitter_username,
                gp.hireable,
                COALESCE(COUNT(gc.contribution_id), 0) as contribution_count
            FROM github_profile gp
            LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            WHERE gp.person_id IS NULL
            GROUP BY 
                gp.github_profile_id,
                gp.github_username,
                gp.github_name,
                gp.github_email,
                gp.github_company,
                gp.location,
                gp.bio,
                gp.followers,
                gp.following,
                gp.public_repos,
                gp.blog,
                gp.twitter_username,
                gp.hireable
            ORDER BY contribution_count DESC, gp.followers DESC
        """)
        
        profiles = [dict(row) for row in self.cursor.fetchall()]
        self.stats['total_orphaned_profiles'] = len(profiles)
        
        print(f"   Found {len(profiles):,} orphaned GitHub profiles")
        return profiles
    
    def promote_profile_to_person(self, profile: Dict, tier: str, reason: str) -> Optional[str]:
        """
        Create person record for GitHub profile
        
        Args:
            profile: GitHub profile data
            tier: Promotion tier (tier1, tier2)
            reason: Reason for promotion
            
        Returns:
            New person_id or None on error
        """
        try:
            # Build full name - use GitHub name or username
            github_name = profile.get('github_name')
            github_username = profile['github_username']
            
            if github_name and github_name.strip():
                full_name = github_name.strip()
            else:
                # Use username as name - this is their identity in this space!
                full_name = github_username
            
            # Parse name parts
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else full_name
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            
            # Build headline
            headline_parts = [f"GitHub: @{github_username}"]
            if profile.get('github_company'):
                headline_parts.append(f"@ {profile['github_company']}")
            if profile.get('followers', 0) > 0:
                headline_parts.append(f"{profile['followers']} followers")
            headline = " | ".join(headline_parts)
            
            # Build description
            if profile.get('bio'):
                description = profile['bio']
            else:
                description = f"GitHub contributor - Profile needs enrichment ({tier}: {reason})"
            
            if not self.dry_run:
                # Insert person record
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
                    RETURNING person_id::text
                """, (
                    full_name,
                    first_name,
                    last_name,
                    profile.get('location'),
                    headline,
                    description
                ))
                
                person_id = self.cursor.fetchone()['person_id']
                
                # Add email if we have it
                if profile.get('github_email'):
                    try:
                        self.cursor.execute("""
                            INSERT INTO person_email (person_id, email, email_type, is_primary, source)
                            VALUES (%s::uuid, %s, 'work', TRUE, 'github_promotion')
                            ON CONFLICT (person_id, LOWER(email)) DO NOTHING
                        """, (person_id, profile['github_email']))
                        
                        if self.cursor.rowcount > 0:
                            self.stats['emails_added'] += 1
                    except Exception as e:
                        # Email insert failed, continue anyway
                        pass
                
                # Link GitHub profile to person
                self.cursor.execute("""
                    UPDATE github_profile
                    SET person_id = %s::uuid
                    WHERE github_profile_id = %s::uuid
                """, (person_id, profile['github_profile_id']))
                
                self.stats['profiles_linked'] += 1
                self.stats['people_created'] += 1
                
                # Track sample for reporting
                if len(self.stats['promoted_samples']) < 20:
                    self.stats['promoted_samples'].append({
                        'name': full_name,
                        'username': github_username,
                        'tier': tier,
                        'reason': reason,
                        'contributions': profile.get('contribution_count', 0),
                        'followers': profile.get('followers', 0)
                    })
                
                return person_id
            else:
                # Dry run - just count
                self.stats['people_created'] += 1
                if len(self.stats['promoted_samples']) < 20:
                    self.stats['promoted_samples'].append({
                        'name': full_name,
                        'username': github_username,
                        'tier': tier,
                        'reason': reason,
                        'contributions': profile.get('contribution_count', 0),
                        'followers': profile.get('followers', 0)
                    })
                return "dry_run_id"
                
        except Exception as e:
            error_msg = f"Error promoting {profile['github_username']}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"   ❌ {error_msg}")
            return None
    
    def process_profiles(self):
        """Main processing loop"""
        profiles = self.get_orphaned_profiles()
        
        if not profiles:
            print("✅ No orphaned profiles to process!")
            return
        
        print(f"\n🔄 Evaluating profiles for promotion...\n")
        
        batch_count = 0
        batch_size = 100
        
        for profile in profiles:
            should_promote, tier, reason = self.should_promote_to_person(
                profile,
                profile['contribution_count']
            )
            
            # Track by tier
            tier_stat_key = f"{tier}_{reason.split('(')[0].split()[0]}"
            if should_promote:
                if tier == "tier1":
                    if "contributor" in reason:
                        self.stats['tier1_contributors'] += 1
                    elif "high_followers" in reason:
                        self.stats['tier1_high_followers'] += 1
                    elif "has_identity" in reason:
                        self.stats['tier1_has_identity'] += 1
                elif tier == "tier2":
                    if "company_match" in reason:
                        self.stats['tier2_company_match'] += 1
                    elif "active_developer" in reason:
                        self.stats['tier2_active_developer'] += 1
                    elif "crypto_bio" in reason:
                        self.stats['tier2_crypto_bio'] += 1
                
                # Promote profile
                person_id = self.promote_profile_to_person(profile, tier, reason)
                
                if person_id and not self.dry_run:
                    batch_count += 1
                    if batch_count >= batch_size:
                        self.conn.commit()
                        print(f"   ✅ Committed batch ({self.stats['people_created']:,} people created so far)")
                        batch_count = 0
            else:
                self.stats['tier3_skipped'] += 1
        
        # Final commit
        if not self.dry_run and batch_count > 0:
            self.conn.commit()
            print(f"   ✅ Final commit")
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate and display promotion report"""
        print(f"\n{'='*80}")
        print(f"PROMOTION COMPLETE - FINAL REPORT")
        print(f"{'='*80}")
        
        print(f"\n📊 ORPHANED PROFILES ANALYSIS:")
        print(f"   Total Orphaned Profiles: {self.stats['total_orphaned_profiles']:,}")
        
        print(f"\n✅ TIER 1 - HIGH CONFIDENCE (Auto-promoted):")
        print(f"   Contributors: {self.stats['tier1_contributors']:,}")
        print(f"   High Followers (>100): {self.stats['tier1_high_followers']:,}")
        print(f"   Has Identity (name + email/location): {self.stats['tier1_has_identity']:,}")
        tier1_total = (self.stats['tier1_contributors'] + 
                      self.stats['tier1_high_followers'] + 
                      self.stats['tier1_has_identity'])
        print(f"   Tier 1 Total: {tier1_total:,}")
        
        print(f"\n✅ TIER 2 - MEDIUM CONFIDENCE (Auto-promoted):")
        print(f"   Company Match: {self.stats['tier2_company_match']:,}")
        print(f"   Active Developer (>10 repos): {self.stats['tier2_active_developer']:,}")
        print(f"   Crypto/Web3 Bio: {self.stats['tier2_crypto_bio']:,}")
        tier2_total = (self.stats['tier2_company_match'] + 
                      self.stats['tier2_active_developer'] + 
                      self.stats['tier2_crypto_bio'])
        print(f"   Tier 2 Total: {tier2_total:,}")
        
        print(f"\n⏭️  TIER 3 - LOW CONFIDENCE (Skipped):")
        print(f"   Skipped: {self.stats['tier3_skipped']:,}")
        
        print(f"\n👥 PEOPLE CREATED:")
        print(f"   ✅ New People: {self.stats['people_created']:,}")
        print(f"   ✅ Profiles Linked: {self.stats['profiles_linked']:,}")
        print(f"   ✅ Emails Added: {self.stats['emails_added']:,}")
        
        if self.stats['promoted_samples']:
            print(f"\n   Sample of promoted profiles (first 20):")
            for sample in self.stats['promoted_samples'][:20]:
                print(f"      • {sample['name']} (@{sample['username']})")
                print(f"        {sample['tier']}: {sample['reason']} | "
                      f"{sample['contributions']} contributions | "
                      f"{sample['followers']} followers")
        
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
                    WHERE person_id IS NULL
                """)
                remaining_orphaned = self.cursor.fetchone()['count']
                
                print(f"\n📈 DATABASE TOTALS:")
                print(f"   Total People: {total_people:,}")
                print(f"   Remaining Orphaned GitHub Profiles: {remaining_orphaned:,}")
            except Exception as e:
                print(f"   ⚠️  Could not retrieve totals: {e}")
        
        print(f"\n{'='*80}\n")
        
        # Write report to file
        report_filename = f"reports/github_promotion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = Path(__file__).parent.parent.parent / report_filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"GitHub Profile Promotion Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE RUN'}\n\n")
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key not in ['errors', 'promoted_samples']:
                    f.write(f"  {key}: {value}\n")
            
            if self.stats['promoted_samples']:
                f.write(f"\nPromoted Profiles Sample:\n")
                for sample in self.stats['promoted_samples']:
                    f.write(f"  - {sample['name']} (@{sample['username']}): "
                           f"{sample['tier']} - {sample['reason']}\n")
            
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
        description='Promote orphaned GitHub profiles to person records'
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--live', action='store_true',
                       help='Actually perform the promotion (default is dry-run)')
    
    args = parser.parse_args()
    
    # Default to dry-run unless --live specified
    dry_run = not args.live
    
    if not dry_run:
        print(f"\n⚠️  WARNING: LIVE MODE - Will create person records!")
        print(f"This will:")
        print(f"  - Create person records for eligible GitHub profiles")
        print(f"  - Link GitHub profiles to new person records")
        print(f"  - Add emails where available")
        print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
        
        response = input(f"\nProceed with LIVE promotion? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return 0
    else:
        print(f"\n📋 DRY RUN MODE - No changes will be made")
        print(f"Use --live to actually perform the promotion\n")
    
    try:
        promoter = GitHubProfilePromoter(dry_run=dry_run)
        promoter.process_profiles()
        promoter.generate_report()
        promoter.close()
        
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


#!/usr/bin/env python3
# ABOUTME: Queue all GitHub profiles for enrichment and then match to people
# ABOUTME: Ensures we enrich first, then match with the enriched data

"""
GitHub Profile Enrichment Queue Manager

Workflow:
1. Find ALL GitHub profiles that need enrichment
2. Queue them for enrichment (reset updated_at dates)
3. After enrichment, run matching to link to people
4. Keep unmatched profiles for future matching
"""

import sqlite3
from datetime import datetime
from config import Config, log_message

class GitHubEnrichmentQueue:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        
    def analyze_enrichment_status(self):
        """Check enrichment status of all GitHub profiles"""
        cursor = self.conn.cursor()
        
        print("="*60)
        print("📊 GitHub Profile Enrichment Status")
        print("="*60)
        print()
        
        # Total profiles
        cursor.execute("SELECT COUNT(*) FROM github_profiles")
        total = cursor.fetchone()[0]
        print(f"Total GitHub profiles: {total:,}")
        print()
        
        # Check enrichment status
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN followers IS NOT NULL THEN 1 ELSE 0 END) as has_followers,
                SUM(CASE WHEN github_email IS NOT NULL THEN 1 ELSE 0 END) as has_email,
                SUM(CASE WHEN github_name IS NOT NULL THEN 1 ELSE 0 END) as has_name,
                SUM(CASE WHEN github_company IS NOT NULL THEN 1 ELSE 0 END) as has_company,
                SUM(CASE WHEN public_repos IS NOT NULL THEN 1 ELSE 0 END) as has_repos,
                SUM(CASE WHEN languages_json IS NOT NULL THEN 1 ELSE 0 END) as has_languages
            FROM github_profiles
        """)
        
        result = cursor.fetchone()
        
        print("Enrichment Coverage:")
        print(f"  Has followers data: {result[1]:,} / {result[0]:,} ({result[1]/result[0]*100:.1f}%)")
        print(f"  Has email:          {result[2]:,} / {result[0]:,} ({result[2]/result[0]*100:.1f}%)")
        print(f"  Has name:           {result[3]:,} / {result[0]:,} ({result[3]/result[0]*100:.1f}%)")
        print(f"  Has company:        {result[4]:,} / {result[0]:,} ({result[4]/result[0]*100:.1f}%)")
        print(f"  Has repos count:    {result[5]:,} / {result[0]:,} ({result[5]/result[0]*100:.1f}%)")
        print(f"  Has languages:      {result[6]:,} / {result[0]:,} ({result[6]/result[0]*100:.1f}%)")
        
        # Find profiles needing enrichment
        cursor.execute("""
            SELECT COUNT(*) 
            FROM github_profiles 
            WHERE (
                followers IS NULL 
                OR public_repos IS NULL
                OR github_name IS NULL
                OR languages_json IS NULL
            )
            AND github_username IS NOT NULL
        """)
        
        needs_enrichment = cursor.fetchone()[0]
        print(f"\nProfiles needing enrichment: {needs_enrichment:,}")
        
        # Check person linkage
        cursor.execute("""
            SELECT COUNT(*) 
            FROM github_profiles 
            WHERE person_id IS NOT NULL
        """)
        
        linked = cursor.fetchone()[0]
        print(f"\nProfiles linked to people: {linked:,} / {total:,} ({linked/total*100:.1f}%)")
        
        return needs_enrichment
    
    def queue_for_enrichment(self, limit=None):
        """Queue GitHub profiles for enrichment by resetting their updated_at dates"""
        cursor = self.conn.cursor()
        
        print("\n📝 Queuing profiles for enrichment...")
        
        # Find profiles that need enrichment
        query = """
            UPDATE github_profiles 
            SET updated_at = '2020-01-01'
            WHERE (
                followers IS NULL 
                OR public_repos IS NULL
                OR github_name IS NULL
                OR languages_json IS NULL
                OR github_email IS NULL
            )
            AND github_username IS NOT NULL
            AND updated_at > datetime('now', '-7 days')
        """
        
        if limit:
            # Can't use LIMIT with UPDATE directly in SQLite, so we need a subquery
            query = f"""
                UPDATE github_profiles 
                SET updated_at = '2020-01-01'
                WHERE github_profile_id IN (
                    SELECT github_profile_id 
                    FROM github_profiles 
                    WHERE (
                        followers IS NULL 
                        OR public_repos IS NULL
                        OR github_name IS NULL
                        OR languages_json IS NULL
                        OR github_email IS NULL
                    )
                    AND github_username IS NOT NULL
                    AND updated_at > datetime('now', '-7 days')
                    LIMIT {limit}
                )
            """
        
        cursor.execute(query)
        queued = cursor.rowcount
        self.conn.commit()
        
        print(f"✅ Queued {queued:,} profiles for enrichment")
        
        return queued
    
    def match_enriched_profiles(self):
        """Match enriched GitHub profiles to existing people"""
        cursor = self.conn.cursor()
        
        print("\n🔗 Matching enriched profiles to people...")
        
        matches = {
            'by_email': 0,
            'by_name_company': 0,
            'by_twitter': 0
        }
        
        # 1. Match by email
        print("  Matching by email...")
        cursor.execute("""
            UPDATE github_profiles
            SET person_id = (
                SELECT p.person_id 
                FROM people p 
                WHERE p.primary_email = github_profiles.github_email
                LIMIT 1
            )
            WHERE github_email IS NOT NULL
            AND person_id IS NULL
            AND EXISTS (
                SELECT 1 FROM people p 
                WHERE p.primary_email = github_profiles.github_email
            )
        """)
        matches['by_email'] = cursor.rowcount
        print(f"    ✅ Matched {matches['by_email']:,} by email")
        
        # 2. Match by name + company
        print("  Matching by name + company...")
        cursor.execute("""
            UPDATE github_profiles gp
            SET person_id = (
                SELECT p.person_id
                FROM people p
                JOIN employment e ON p.person_id = e.person_id
                WHERE LOWER(p.first_name || ' ' || p.last_name) = LOWER(gp.github_name)
                AND LOWER(e.company_name) = LOWER(gp.github_company)
                AND e.is_current = 1
                LIMIT 1
            )
            WHERE gp.github_name IS NOT NULL
            AND gp.github_company IS NOT NULL
            AND gp.person_id IS NULL
            AND EXISTS (
                SELECT 1 
                FROM people p
                JOIN employment e ON p.person_id = e.person_id
                WHERE LOWER(p.first_name || ' ' || p.last_name) = LOWER(gp.github_name)
                AND LOWER(e.company_name) = LOWER(gp.github_company)
                AND e.is_current = 1
            )
        """)
        matches['by_name_company'] = cursor.rowcount
        print(f"    ✅ Matched {matches['by_name_company']:,} by name + company")
        
        # 3. Match by Twitter username
        print("  Matching by Twitter username...")
        cursor.execute("""
            UPDATE github_profiles gp
            SET person_id = (
                SELECT sp.person_id
                FROM social_profiles sp
                WHERE sp.platform = 'twitter'
                AND (
                    LOWER(sp.username) = LOWER(gp.twitter_username)
                    OR LOWER(sp.profile_url) LIKE '%' || LOWER(gp.twitter_username)
                )
                LIMIT 1
            )
            WHERE gp.twitter_username IS NOT NULL
            AND gp.person_id IS NULL
            AND EXISTS (
                SELECT 1
                FROM social_profiles sp
                WHERE sp.platform = 'twitter'
                AND (
                    LOWER(sp.username) = LOWER(gp.twitter_username)
                    OR LOWER(sp.profile_url) LIKE '%' || LOWER(gp.twitter_username)
                )
            )
        """)
        matches['by_twitter'] = cursor.rowcount
        print(f"    ✅ Matched {matches['by_twitter']:,} by Twitter username")
        
        self.conn.commit()
        
        total_matched = sum(matches.values())
        print(f"\n✅ Total newly matched: {total_matched:,}")
        
        # Also update social_profiles table for matched records
        print("\n📋 Updating social_profiles for matched GitHub profiles...")
        cursor.execute("""
            INSERT OR REPLACE INTO social_profiles (person_id, platform, profile_url, username)
            SELECT 
                gp.person_id,
                'github' as platform,
                gp.profile_url,
                gp.github_username
            FROM github_profiles gp
            WHERE gp.person_id IS NOT NULL
            AND gp.profile_url IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM social_profiles sp
                WHERE sp.person_id = gp.person_id
                AND sp.platform = 'github'
            )
        """)
        
        social_updated = cursor.rowcount
        self.conn.commit()
        
        print(f"  ✅ Updated {social_updated:,} social_profiles records")
        
        return total_matched
    
    def show_unmatched_sample(self):
        """Show sample of unmatched profiles for review"""
        cursor = self.conn.cursor()
        
        print("\n📊 Sample unmatched profiles (may match future imports):")
        
        cursor.execute("""
            SELECT 
                github_username,
                github_name,
                github_email,
                github_company,
                followers,
                public_repos
            FROM github_profiles
            WHERE person_id IS NULL
            AND github_username IS NOT NULL
            ORDER BY followers DESC NULLS LAST
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"\n{'Username':<20} {'Name':<25} {'Company':<20} {'Followers':<10}")
            print("-"*80)
            for row in results:
                username = row[0] or ''
                name = row[1] or ''
                company = row[3] or ''
                followers = str(row[4]) if row[4] is not None else ''
                print(f"{username:<20} {name:<25} {company:<20} {followers:<10}")
        
        # Count total unmatched
        cursor.execute("""
            SELECT COUNT(*) FROM github_profiles 
            WHERE person_id IS NULL
        """)
        
        unmatched = cursor.fetchone()[0]
        print(f"\nTotal unmatched profiles: {unmatched:,}")
        print("(These will be checked again when new people are imported)")

def main():
    """Main workflow"""
    queue = GitHubEnrichmentQueue()
    
    print("="*60)
    print("🚀 GitHub Profile Enrichment & Matching Workflow")
    print("="*60)
    print()
    
    # Step 1: Analyze current status
    needs_enrichment = queue.analyze_enrichment_status()
    
    if needs_enrichment > 0:
        print("\n" + "="*60)
        print("📋 ENRICHMENT NEEDED")
        print("="*60)
        
        # Queue profiles for enrichment
        queued = queue.queue_for_enrichment()
        
        if queued > 0:
            print(f"\n⚠️  {queued:,} profiles have been queued for enrichment")
            print("\nTo enrich them, run:")
            print(f"  python3 github_enrichment.py --limit 100  # Test batch")
            print(f"  python3 github_enrichment.py              # All profiles")
            
            estimated_time = queued * 3.6 / 60  # ~3.6 seconds per profile
            print(f"\nEstimated time: {estimated_time:.1f} minutes")
    
    # Step 2: Match enriched profiles
    print("\n" + "="*60)
    print("🔗 MATCHING TO PEOPLE")
    print("="*60)
    
    matched = queue.match_enriched_profiles()
    
    # Step 3: Show unmatched for review
    queue.show_unmatched_sample()
    
    print("\n" + "="*60)
    print("✅ WORKFLOW COMPLETE")
    print("="*60)
    
    print("\n📊 Summary:")
    print(f"  • Profiles needing enrichment: {needs_enrichment:,}")
    print(f"  • Profiles matched to people: {matched:,}")
    
    print("\n💡 Next steps:")
    print("1. Run enrichment if profiles are queued")
    print("2. Re-run this script after enrichment to match more profiles")
    print("3. Unmatched profiles will auto-match when new people are imported")

if __name__ == "__main__":
    main()

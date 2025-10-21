#!/usr/bin/env python3
# ABOUTME: Diagnose why GitHub profiles aren't being found for enrichment
# ABOUTME: Check social_profiles, github_profiles tables and fix the connection

"""
GitHub Profile Diagnostic Script

Diagnoses why enrichment isn't finding profiles to process
"""

import sqlite3
from config import Config
from datetime import datetime

def diagnose_github_profiles():
    """Check what's going on with GitHub profiles"""
    
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    print("="*60)
    print("🔍 GitHub Profile Diagnostic")
    print("="*60)
    print()
    
    # 1. Check social_profiles table
    print("📊 1. Checking social_profiles table...")
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN profile_url IS NOT NULL THEN 1 ELSE 0 END) as with_url,
               SUM(CASE WHEN profile_url LIKE '%github%' THEN 1 ELSE 0 END) as github_urls
        FROM social_profiles
        WHERE platform = 'github'
    """)
    
    result = cursor.fetchone()
    if result:
        total, with_url, github_urls = result
        print(f"  Total GitHub entries: {total}")
        print(f"  With profile URL: {with_url}")
        print(f"  Valid GitHub URLs: {github_urls}")
    
    # Show sample GitHub URLs
    cursor.execute("""
        SELECT profile_url 
        FROM social_profiles 
        WHERE platform = 'github' 
        AND profile_url IS NOT NULL 
        LIMIT 5
    """)
    
    print("\n  Sample GitHub URLs from social_profiles:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}")
    
    # 2. Check github_profiles table
    print("\n📊 2. Checking github_profiles table...")
    
    # Check if table exists and its structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github_profiles'")
    if not cursor.fetchone():
        print("  ❌ github_profiles table does not exist!")
        print("\n  Creating github_profiles table now...")
        
        # Create the table
        cursor.execute("""
            CREATE TABLE github_profiles (
                github_profile_id TEXT PRIMARY KEY,
                person_id TEXT,
                github_username TEXT,
                github_name TEXT,
                github_email TEXT,
                github_company TEXT,
                github_location TEXT,
                github_bio TEXT,
                personal_website TEXT,
                twitter_username TEXT,
                public_repos INTEGER,
                public_gists INTEGER,
                followers INTEGER,
                following INTEGER,
                created_at TEXT,
                updated_at TEXT,
                hireable INTEGER,
                languages_json TEXT,
                top_language TEXT,
                profile_url TEXT,
                enrichment_status TEXT DEFAULT 'pending',
                enrichment_attempts INTEGER DEFAULT 0,
                last_enrichment_attempt TEXT,
                FOREIGN KEY (person_id) REFERENCES people(person_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_profiles_person_id ON github_profiles(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_profiles_username ON github_profiles(github_username)")
        
        conn.commit()
        print("  ✅ github_profiles table created")
    else:
        # Table exists, check contents
        cursor.execute("SELECT COUNT(*) FROM github_profiles")
        total_github = cursor.fetchone()[0]
        print(f"  Total records in github_profiles: {total_github}")
        
        cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE updated_at > datetime('now', '-7 days')")
        recent = cursor.fetchone()[0]
        print(f"  Recently updated (last 7 days): {recent}")
    
    # 3. Check the actual query used by enrichment
    print("\n📊 3. Testing enrichment query...")
    
    # This is the exact query from github_enrichment.py
    cursor.execute("""
        SELECT DISTINCT sp.person_id, sp.profile_url
        FROM social_profiles sp
        WHERE sp.platform = 'github'
        AND sp.profile_url IS NOT NULL
        AND sp.profile_url != ''
        AND NOT EXISTS (
            SELECT 1 FROM github_profiles gp 
            WHERE gp.person_id = sp.person_id
            AND gp.updated_at > datetime('now', '-7 days')
        )
        ORDER BY sp.person_id
        LIMIT 10
    """)
    
    profiles_to_enrich = cursor.fetchall()
    print(f"  Profiles found for enrichment: {len(profiles_to_enrich)}")
    
    if profiles_to_enrich:
        print("\n  Sample profiles to enrich:")
        for person_id, url in profiles_to_enrich[:5]:
            print(f"    Person: {person_id[:12]}... URL: {url}")
    
    # 4. Check for the join issue
    print("\n📊 4. Checking person_id connections...")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT sp.person_id)
        FROM social_profiles sp
        WHERE sp.platform = 'github'
        AND sp.profile_url IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM people p 
            WHERE p.person_id = sp.person_id
        )
    """)
    
    valid_person_ids = cursor.fetchone()[0]
    print(f"  GitHub profiles with valid person_id: {valid_person_ids}")
    
    # 5. Let's create the missing link
    print("\n📊 5. Creating missing github_profiles records...")
    
    # Insert records into github_profiles for all GitHub social profiles
    cursor.execute("""
        INSERT OR IGNORE INTO github_profiles (
            github_profile_id, 
            person_id, 
            profile_url, 
            github_username,
            created_at, 
            updated_at,
            enrichment_status
        )
        SELECT 
            'gh_' || substr(hex(randomblob(6)), 1, 12) as github_profile_id,
            sp.person_id,
            sp.profile_url,
            CASE 
                WHEN sp.profile_url LIKE '%github.com/%' THEN 
                    substr(
                        sp.profile_url, 
                        instr(sp.profile_url, 'github.com/') + 11,
                        CASE 
                            WHEN instr(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11), '/') > 0
                            THEN instr(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11), '/') - 1
                            WHEN instr(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11), '?') > 0
                            THEN instr(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11), '?') - 1
                            ELSE length(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11))
                        END
                    )
                ELSE sp.username
            END as github_username,
            datetime('now') as created_at,
            datetime('2020-01-01') as updated_at,  -- Old date so it needs enrichment
            'pending' as enrichment_status
        FROM social_profiles sp
        WHERE sp.platform = 'github'
        AND sp.profile_url IS NOT NULL
        AND sp.profile_url != ''
        AND NOT EXISTS (
            SELECT 1 FROM github_profiles gp 
            WHERE gp.person_id = sp.person_id
        )
    """)
    
    rows_created = cursor.rowcount
    conn.commit()
    
    print(f"  ✅ Created {rows_created} new github_profiles records")
    
    # 6. Now check again
    print("\n📊 6. Re-checking after fix...")
    
    cursor.execute("""
        SELECT COUNT(*) FROM github_profiles
        WHERE updated_at < datetime('now', '-7 days')
    """)
    
    needs_enrichment = cursor.fetchone()[0]
    print(f"  Profiles needing enrichment: {needs_enrichment}")
    
    # 7. Final verification
    cursor.execute("""
        SELECT DISTINCT sp.person_id, sp.profile_url
        FROM social_profiles sp
        WHERE sp.platform = 'github'
        AND sp.profile_url IS NOT NULL
        AND sp.profile_url != ''
        AND NOT EXISTS (
            SELECT 1 FROM github_profiles gp 
            WHERE gp.person_id = sp.person_id
            AND gp.updated_at > datetime('now', '-7 days')
        )
    """)
    
    final_count = len(cursor.fetchall())
    print(f"\n✅ Final count ready for enrichment: {final_count}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("📋 DIAGNOSIS COMPLETE")
    print("="*60)
    
    if final_count > 0:
        print("\n✅ GitHub profiles are now ready for enrichment!")
        print("\nYou can now run:")
        print("  python3 github_enrichment.py --limit 100")
        print("\nOr for all profiles:")
        print("  python3 github_enrichment.py")
    else:
        print("\n⚠️  Still no profiles found. Checking alternative approach...")
        
        # Alternative: Just enrich everything in github_profiles
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE github_profiles 
            SET updated_at = '2020-01-01'
            WHERE followers IS NULL 
            OR public_repos IS NULL
        """)
        
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        if updated > 0:
            print(f"\n✅ Reset {updated} profiles for enrichment")
            print("\nNow run:")
            print("  python3 github_enrichment.py --limit 100")


if __name__ == "__main__":
    diagnose_github_profiles()

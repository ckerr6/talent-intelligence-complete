#!/usr/bin/env python3
# ABOUTME: Fixed version of GitHub matching with proper SQL syntax
# ABOUTME: Matches enriched GitHub profiles to people in database

"""
GitHub Profile Matcher - Fixed Version

Matches GitHub profiles to existing people using multiple strategies
"""

import sqlite3
from config import Config

def match_github_profiles():
    """Match GitHub profiles to people with fixed SQL"""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    print("="*60)
    print("🔗 GitHub Profile Matching")
    print("="*60)
    print()
    
    matches = {
        'by_email': 0,
        'by_name_company': 0,
        'by_twitter': 0,
        'by_linkedin': 0
    }
    
    # 1. Match by email (already worked)
    print("1. Matching by email...")
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
    conn.commit()
    print(f"   ✅ Matched {matches['by_email']:,} by email")
    
    # 2. Match by name + company (FIXED VERSION)
    print("2. Matching by name + company...")
    
    # First, let's do it in a simpler way that SQLite can handle
    cursor.execute("""
        SELECT gp.github_profile_id, gp.github_name, gp.github_company
        FROM github_profiles gp
        WHERE gp.github_name IS NOT NULL
        AND gp.github_company IS NOT NULL
        AND gp.person_id IS NULL
    """)
    
    profiles_to_match = cursor.fetchall()
    matched_count = 0
    
    for profile_id, name, company in profiles_to_match:
        # Try to find matching person
        cursor.execute("""
            SELECT p.person_id
            FROM people p
            JOIN employment e ON p.person_id = e.person_id
            WHERE LOWER(TRIM(p.first_name || ' ' || p.last_name)) = LOWER(TRIM(?))
            AND LOWER(TRIM(e.company_name)) = LOWER(TRIM(?))
            AND e.is_current = 1
            LIMIT 1
        """, (name, company))
        
        result = cursor.fetchone()
        if result:
            person_id = result[0]
            cursor.execute("""
                UPDATE github_profiles
                SET person_id = ?
                WHERE github_profile_id = ?
            """, (person_id, profile_id))
            matched_count += 1
    
    conn.commit()
    matches['by_name_company'] = matched_count
    print(f"   ✅ Matched {matches['by_name_company']:,} by name + company")
    
    # 3. Match by Twitter username
    print("3. Matching by Twitter username...")
    cursor.execute("""
        SELECT gp.github_profile_id, gp.twitter_username
        FROM github_profiles gp
        WHERE gp.twitter_username IS NOT NULL
        AND gp.person_id IS NULL
    """)
    
    twitter_profiles = cursor.fetchall()
    matched_count = 0
    
    for profile_id, twitter_username in twitter_profiles:
        cursor.execute("""
            SELECT sp.person_id
            FROM social_profiles sp
            WHERE sp.platform = 'twitter'
            AND (
                LOWER(sp.username) = LOWER(?)
                OR LOWER(sp.profile_url) LIKE '%' || LOWER(?) || '%'
            )
            LIMIT 1
        """, (twitter_username, twitter_username))
        
        result = cursor.fetchone()
        if result:
            person_id = result[0]
            cursor.execute("""
                UPDATE github_profiles
                SET person_id = ?
                WHERE github_profile_id = ?
            """, (person_id, profile_id))
            matched_count += 1
    
    conn.commit()
    matches['by_twitter'] = matched_count
    print(f"   ✅ Matched {matches['by_twitter']:,} by Twitter")
    
    # 4. Match by fuzzy name matching (same name, different company)
    print("4. Matching by name only (fuzzy)...")
    cursor.execute("""
        SELECT gp.github_profile_id, gp.github_name
        FROM github_profiles gp
        WHERE gp.github_name IS NOT NULL
        AND gp.person_id IS NULL
    """)
    
    name_profiles = cursor.fetchall()
    matched_count = 0
    
    for profile_id, name in name_profiles:
        # Split name for better matching
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            
            cursor.execute("""
                SELECT p.person_id, p.first_name, p.last_name
                FROM people p
                WHERE LOWER(TRIM(p.first_name)) = LOWER(TRIM(?))
                AND LOWER(TRIM(p.last_name)) = LOWER(TRIM(?))
                LIMIT 1
            """, (first_name, last_name))
            
            result = cursor.fetchone()
            if result:
                person_id = result[0]
                cursor.execute("""
                    UPDATE github_profiles
                    SET person_id = ?
                    WHERE github_profile_id = ?
                """, (person_id, profile_id))
                matched_count += 1
    
    conn.commit()
    matches['by_linkedin'] = matched_count  # Using this key for name matching
    print(f"   ✅ Matched {matched_count:,} by name only")
    
    # Update social_profiles table
    print("\n5. Updating social_profiles table...")
    cursor.execute("""
        INSERT OR IGNORE INTO social_profiles (person_id, platform, profile_url, username)
        SELECT 
            gp.person_id,
            'github' as platform,
            gp.profile_url,
            gp.github_username
        FROM github_profiles gp
        WHERE gp.person_id IS NOT NULL
        AND gp.profile_url IS NOT NULL
    """)
    
    social_updated = cursor.rowcount
    conn.commit()
    print(f"   ✅ Updated {social_updated:,} social_profiles records")
    
    # Summary
    total_matched = sum(matches.values())
    
    print("\n" + "="*60)
    print("📊 MATCHING SUMMARY")
    print("="*60)
    print(f"Total newly matched: {total_matched:,}")
    print(f"  By email:          {matches['by_email']:,}")
    print(f"  By name+company:   {matches['by_name_company']:,}")
    print(f"  By Twitter:        {matches['by_twitter']:,}")
    print(f"  By name only:      {matches['by_linkedin']:,}")
    
    # Check remaining unmatched
    cursor.execute("""
        SELECT COUNT(*) FROM github_profiles WHERE person_id IS NULL
    """)
    unmatched = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM github_profiles WHERE person_id IS NOT NULL
    """)
    matched_total = cursor.fetchone()[0]
    
    print(f"\nTotal matched:       {matched_total:,} / 18,029 ({matched_total/18029*100:.1f}%)")
    print(f"Still unmatched:     {unmatched:,}")
    
    # Show top unmatched
    print("\n📋 Top unmatched profiles by followers:")
    cursor.execute("""
        SELECT github_username, github_name, followers, github_company, github_email
        FROM github_profiles
        WHERE person_id IS NULL
        AND followers > 1000
        ORDER BY followers DESC
        LIMIT 10
    """)
    
    for username, name, followers, company, email in cursor.fetchall():
        email_str = f" ({email})" if email else ""
        print(f"  @{username}: {name} - {followers:,} followers - {company or 'No company'}{email_str}")
    
    conn.close()

if __name__ == "__main__":
    match_github_profiles()

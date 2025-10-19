#!/usr/bin/env python3
# ABOUTME: Import GitHub org data from CSV and update company records
# ABOUTME: Populates github_org, twitter, and social profiles for companies

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

def wait_for_database(db_path, max_wait=10):
    """Wait for database to be available"""
    print("⏳ Waiting for database to be available...")
    
    for i in range(max_wait):
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            print("✅ Database available")
            return True
        except sqlite3.OperationalError:
            print(f"  Waiting... ({i+1}/{max_wait})")
            time.sleep(2)
    
    return False

def import_github_orgs(db_path, csv_path):
    """Import GitHub org data from CSV"""
    
    print("📥 Importing GitHub Organization Data")
    print("=" * 60)
    
    # Wait for database
    if not wait_for_database(db_path):
        print("❌ Database is locked by another process")
        print("   The profile enrichment is probably running.")
        print("   This script will wait and retry...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    print(f"📊 Found {len(df)} companies in CSV\n")
    
    # Connect to database with longer timeout
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()
    
    # Track statistics
    stats = {
        'companies_matched': 0,
        'companies_created': 0,
        'github_orgs_added': 0,
        'twitter_added': 0,
        'social_profiles_added': 0,
        'rows_processed': 0
    }
    
    print("Processing companies...")
    print("-" * 60)
    
    for idx, row in df.iterrows():
        company_name = row.get('Portfolio_Company')
        website = row.get('Company_Website')
        github_url = row.get('Github (2)')  # Full GitHub URL
        github_path = row.get('GitHub Path')  # Just the org name
        twitter_username = row.get('Twitter Username')
        followers = row.get('Followers - Data')
        following = row.get('Following - Data')
        public_repos = row.get('Public Repos - Data')
        
        if not company_name or pd.isna(company_name):
            continue
        
        stats['rows_processed'] += 1
        
        # Extract GitHub org name (use GitHub Path if available, otherwise parse URL)
        github_org = None
        if github_path and not pd.isna(github_path):
            github_org = str(github_path).strip()
        elif github_url and not pd.isna(github_url):
            # Parse from URL: https://github.com/orgname -> orgname
            github_org = str(github_url).strip().replace('https://github.com/', '').replace('http://github.com/', '').split('/')[0]
        
        if not github_org:
            continue  # Skip if no GitHub org
        
        # Clean website URL
        clean_website = None
        if website and not pd.isna(website):
            clean_website = str(website).strip()
            if not clean_website.startswith('http'):
                clean_website = f"https://{clean_website}"
        
        try:
            # Try to find existing company by name or website
            cursor.execute("""
                SELECT company_id FROM companies 
                WHERE LOWER(name) = LOWER(?) 
                   OR (website IS NOT NULL AND website LIKE ?)
                LIMIT 1
            """, (company_name, f"%{clean_website}%" if clean_website else '%NOMATCH%'))
            
            result = cursor.fetchone()
            
            if result:
                company_id = result[0]
                stats['companies_matched'] += 1
                
                # Update GitHub org
                cursor.execute("""
                    UPDATE companies 
                    SET github_org = ?, updated_at = ?
                    WHERE company_id = ?
                """, (github_org, datetime.now().isoformat(), company_id))
                stats['github_orgs_added'] += 1
                
                # Add GitHub social profile
                cursor.execute("""
                    INSERT OR REPLACE INTO company_social_profiles 
                    (company_id, platform, username, profile_url)
                    VALUES (?, 'github', ?, ?)
                """, (company_id, github_org, f"github.com/{github_org}"))
                stats['social_profiles_added'] += 1
                
                # Update Twitter if available
                if twitter_username and not pd.isna(twitter_username):
                    clean_twitter = str(twitter_username).strip().replace('@', '')
                    cursor.execute("""
                        INSERT OR REPLACE INTO company_social_profiles 
                        (company_id, platform, username, profile_url)
                        VALUES (?, 'twitter', ?, ?)
                    """, (company_id, clean_twitter, f"x.com/{clean_twitter}"))
                    stats['twitter_added'] += 1
                    stats['social_profiles_added'] += 1
                
                print(f"✅ Updated: {company_name:30s} → {github_org}")
            
            else:
                # Create new company
                import hashlib
                company_id = 'comp_' + hashlib.md5(company_name.encode()).hexdigest()[:12]
                
                cursor.execute("""
                    INSERT OR IGNORE INTO companies 
                    (company_id, name, website, github_org, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    company_id,
                    company_name,
                    clean_website,
                    github_org,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    stats['companies_created'] += 1
                    
                    # Add GitHub social profile
                    cursor.execute("""
                        INSERT INTO company_social_profiles 
                        (company_id, platform, username, profile_url)
                        VALUES (?, 'github', ?, ?)
                    """, (company_id, github_org, f"github.com/{github_org}"))
                    stats['social_profiles_added'] += 1
                    
                    # Add Twitter if available
                    if twitter_username and not pd.isna(twitter_username):
                        clean_twitter = str(twitter_username).strip().replace('@', '')
                        cursor.execute("""
                            INSERT INTO company_social_profiles 
                            (company_id, platform, username, profile_url)
                            VALUES (?, 'twitter', ?, ?)
                        """, (company_id, clean_twitter, f"x.com/{clean_twitter}"))
                        stats['twitter_added'] += 1
                        stats['social_profiles_added'] += 1
                    
                    print(f"➕ Created: {company_name:30s} → {github_org}")
            
            # Commit every 10 companies
            if stats['rows_processed'] % 10 == 0:
                conn.commit()
        
        except sqlite3.OperationalError as e:
            print(f"⚠️  Skipped {company_name}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ IMPORT COMPLETE")
    print("=" * 60)
    print(f"Rows Processed:         {stats['rows_processed']:,}")
    print(f"Companies Matched:      {stats['companies_matched']:,}")
    print(f"Companies Created:      {stats['companies_created']:,}")
    print(f"GitHub Orgs Added:      {stats['github_orgs_added']:,}")
    print(f"Twitter Handles Added:  {stats['twitter_added']:,}")
    print(f"Social Profiles Added:  {stats['social_profiles_added']:,}")
    
    return stats

def main():
    db_path = "talent_intelligence.db"
    csv_path = "GitHub_Org-Default-view-export-1760738884784.csv"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    if not Path(csv_path).exists():
        print(f"❌ CSV not found: {csv_path}")
        return
    
    import_github_orgs(db_path, csv_path)
    
    print("\n🚀 Next step: Run company discovery prep")
    print("   python3 prep_company_discovery.py")

if __name__ == "__main__":
    main()

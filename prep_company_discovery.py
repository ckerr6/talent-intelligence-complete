#!/usr/bin/env python3
# ABOUTME: Identify companies that need GitHub discovery
# ABOUTME: Creates prioritized list of companies to enrich next

"""
Company GitHub Discovery Prep

This script:
1. Finds all companies in database
2. Checks which have GitHub orgs identified
3. Checks which have already been discovered (have repos in company_repositories)
4. Prioritizes companies by:
   - Employee count in our DB
   - Recent activity
   - Strategic importance
5. Generates discovery queue

Output: companies_to_discover.csv - Run these next!
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

def normalize_github_org(text):
    """Extract GitHub org from various formats"""
    if not text or pd.isna(text):
        return None
    
    text = str(text).lower().strip()
    
    # Pattern 1: github.com/orgname
    match = re.search(r'github\.com/([^/\s]+)', text)
    if match:
        org = match.group(1)
        # Skip user profiles (have more path segments)
        if '/' not in org:
            return org
    
    # Pattern 2: Just org name (no URL)
    # Heuristic: if it's short and has no spaces, might be an org
    if len(text) < 50 and ' ' not in text and '.' not in text:
        return text
    
    return None

def find_companies_to_discover(db_path):
    """Find all companies that need GitHub discovery"""
    
    print("🔍 Analyzing companies in database...")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    
    # Get all companies with potential GitHub presence
    query = """
    SELECT 
        c.company_id,
        c.name,
        c.github_org,
        c.website,
        c.linkedin_url,
        COUNT(DISTINCT e.person_id) as employees_in_db,
        csp.profile_url as github_url,
        csp.username as github_username
    FROM companies c
    LEFT JOIN employment e ON c.company_id = e.company_id
    LEFT JOIN company_social_profiles csp 
        ON c.company_id = csp.company_id 
        AND csp.platform = 'github'
    GROUP BY c.company_id
    """
    
    companies = pd.read_sql(query, conn)
    
    print(f"📊 Total companies in database: {len(companies):,}")
    
    # Check which companies already have repos discovered
    discovered_query = """
    SELECT DISTINCT company_id
    FROM company_repositories
    """
    
    try:
        discovered = pd.read_sql(discovered_query, conn)
        discovered_set = set(discovered['company_id'])
    except:
        # Table might not exist yet
        discovered_set = set()
    
    companies['already_discovered'] = companies['company_id'].isin(discovered_set)
    
    print(f"✅ Already discovered: {companies['already_discovered'].sum():,}")
    print(f"⏳ Need discovery: {(~companies['already_discovered']).sum():,}")
    
    # Extract GitHub org from various sources
    companies['github_org_normalized'] = None
    
    for idx, row in companies.iterrows():
        # Try github_org column first
        org = normalize_github_org(row['github_org'])
        
        # Try github social profile
        if not org:
            org = normalize_github_org(row['github_url'])
        
        # Try github username
        if not org:
            org = normalize_github_org(row['github_username'])
        
        companies.at[idx, 'github_org_normalized'] = org
    
    # Filter to companies that:
    # 1. Have a GitHub org identified
    # 2. Haven't been discovered yet
    
    needs_discovery = companies[
        (~companies['already_discovered']) & 
        (companies['github_org_normalized'].notna())
    ].copy()
    
    print(f"\n🎯 Companies ready for discovery: {len(needs_discovery):,}")
    
    # Calculate priority score
    # Higher score = higher priority
    needs_discovery['priority_score'] = (
        needs_discovery['employees_in_db'] * 10  # More employees = higher priority
    )
    
    # Sort by priority
    needs_discovery = needs_discovery.sort_values('priority_score', ascending=False)
    
    # Display summary
    print("\n" + "=" * 60)
    print("📋 DISCOVERY QUEUE - TOP 20")
    print("=" * 60)
    
    for idx, row in needs_discovery.head(20).iterrows():
        emp_count = int(row['employees_in_db']) if row['employees_in_db'] else 0
        print(f"{row['name']:30s} | {row['github_org_normalized']:20s} | {emp_count} employees")
    
    # Save to CSV
    output_file = Path(db_path).parent / "companies_to_discover.csv"
    
    needs_discovery[[
        'company_id', 'name', 'github_org_normalized', 
        'employees_in_db', 'priority_score', 'website'
    ]].to_csv(output_file, index=False)
    
    print("\n" + "=" * 60)
    print(f"✅ Saved discovery queue to: {output_file}")
    print("=" * 60)
    
    # Generate commands
    print("\n🚀 READY-TO-RUN COMMANDS:")
    print("=" * 60)
    print("Copy and paste these to start discovering companies:\n")
    
    for idx, row in needs_discovery.head(10).iterrows():
        org = row['github_org_normalized']
        name = row['name'].replace('"', '\\"')  # Escape quotes
        print(f"python3 github_api_enrichment.py discover-company talent_intelligence.db {org} \"{name}\"")
    
    print("\n" + "=" * 60)
    
    # Statistics
    print("\n📊 STATISTICS:")
    print("=" * 60)
    print(f"Total companies: {len(companies):,}")
    print(f"With GitHub org identified: {companies['github_org_normalized'].notna().sum():,}")
    print(f"Already discovered: {companies['already_discovered'].sum():,}")
    print(f"Ready to discover: {len(needs_discovery):,}")
    print(f"Missing GitHub org: {(companies['github_org_normalized'].isna()).sum():,}")
    
    # Breakdown by employees
    print("\n📈 BY EMPLOYEE COUNT:")
    print("-" * 60)
    for threshold in [50, 20, 10, 5, 1]:
        count = len(needs_discovery[needs_discovery['employees_in_db'] >= threshold])
        print(f"Companies with {threshold}+ employees in DB: {count:,}")
    
    conn.close()
    
    return needs_discovery

def find_missing_github_orgs(db_path):
    """Find companies that need GitHub org identification"""
    
    print("\n\n🔎 COMPANIES MISSING GITHUB ORG:")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        c.company_id,
        c.name,
        c.website,
        COUNT(DISTINCT e.person_id) as employees_in_db
    FROM companies c
    LEFT JOIN employment e ON c.company_id = e.company_id
    LEFT JOIN company_social_profiles csp 
        ON c.company_id = csp.company_id 
        AND csp.platform = 'github'
    WHERE c.github_org IS NULL 
      AND csp.profile_url IS NULL
    GROUP BY c.company_id
    HAVING employees_in_db > 0
    ORDER BY employees_in_db DESC
    LIMIT 50
    """
    
    missing = pd.read_sql(query, conn)
    
    print(f"Found {len(missing)} companies with employees but no GitHub org\n")
    print("Top 20 by employee count:")
    print("-" * 60)
    
    for idx, row in missing.head(20).iterrows():
        emp_count = int(row['employees_in_db']) if row['employees_in_db'] else 0
        website = row['website'] if row['website'] and not pd.isna(row['website']) else 'No website'
        print(f"{row['name']:30s} | {emp_count} employees | {website}")
    
    # Save to CSV
    output_file = Path(db_path).parent / "companies_need_github_org.csv"
    missing.to_csv(output_file, index=False)
    
    print("\n" + "=" * 60)
    print(f"✅ Saved list to: {output_file}")
    print("=" * 60)
    print("\nNext step: Manually research GitHub orgs for these companies")
    print("Then update database with: UPDATE companies SET github_org='org-name' WHERE company_id='...'")
    
    conn.close()

def main():
    db_path = "talent_intelligence.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🏢 Company GitHub Discovery Prep")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    # Find companies ready to discover
    needs_discovery = find_companies_to_discover(db_path)
    
    # Find companies missing GitHub org
    find_missing_github_orgs(db_path)
    
    print("\n\n✅ ANALYSIS COMPLETE!")
    print("=" * 60)
    print("\nFiles created:")
    print("1. companies_to_discover.csv - Ready to enrich")
    print("2. companies_need_github_org.csv - Need manual research")
    print("\nNext steps:")
    print("1. Copy commands above to discover top companies")
    print("2. Research GitHub orgs for companies missing them")
    print("3. Run discovery in batches while profile enrichment continues")

if __name__ == "__main__":
    main()

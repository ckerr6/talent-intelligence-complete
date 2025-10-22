#!/usr/bin/env python3
"""
Diagnostic script to compare CSV data vs database data
"""
from config import get_db_connection
import csv

conn = get_db_connection(use_pool=False)
cursor = conn.cursor()

# Read first 20 companies from CSV
csv_path = '/Users/charlie.kerr/Downloads/Portfolios-vc_portfolio_companies-Default-view-export-1761086233689.csv'

print("COMPANY DATA COMPARISON - CSV vs DATABASE")
print("="*100)

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    
    for i, row in enumerate(reader):
        if i >= 20:  # Check first 20
            break
        
        company_name = row['Company']
        csv_website = row.get('Website', '').strip()
        csv_linkedin = row.get('Linkedin', '').strip()
        csv_github = row.get('Github', '').strip()
        
        # Check database
        cursor.execute('''
            SELECT 
                company_name,
                website_url,
                linkedin_url,
                size_bucket,
                (SELECT COUNT(*) FROM github_repository WHERE company_id = c.company_id) as github_count
            FROM company c
            WHERE LOWER(company_name) = LOWER(%s)
            LIMIT 1
        ''', (company_name,))
        
        result = cursor.fetchone()
        
        print(f"\n{i+1}. {company_name}")
        
        if result:
            print(f"   DATABASE:")
            print(f"      Website: {'✓ ' + result['website_url'][:50] if result['website_url'] else '❌ EMPTY'}")
            print(f"      LinkedIn: {'✓ ' + result['linkedin_url'][:50] if result['linkedin_url'] else '❌ EMPTY'}")
            print(f"      Size: {'✓ ' + result['size_bucket'] if result['size_bucket'] else '❌ EMPTY'}")
            print(f"      GitHub: {result['github_count']} repos")
            
            print(f"   CSV WOULD ADD:")
            would_add = []
            if csv_website and not result['website_url']:
                would_add.append(f"Website: {csv_website[:50]}")
            if csv_linkedin and not result['linkedin_url']:
                would_add.append(f"LinkedIn: {csv_linkedin[:50]}")
            if csv_github and 'github.com/' in csv_github and 'No Organization' not in csv_github:
                would_add.append(f"GitHub: {csv_github[:50]}")
            
            if would_add:
                for item in would_add:
                    print(f"      ✨ {item}")
            else:
                print(f"      ⚠️  NOTHING (company already complete)")
        else:
            print(f"   ❌ NOT IN DATABASE - would create new company")

cursor.close()
conn.close()


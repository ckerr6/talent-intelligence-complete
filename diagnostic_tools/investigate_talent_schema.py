#!/usr/bin/env python3
"""
Deep investigation of PostgreSQL talent database schema
"""

import psycopg2
import os
from urllib.parse import unquote, urlparse

def normalize_linkedin_url(url):
    """Normalize LinkedIn URL for comparison"""
    if not url:
        return None
    
    url = url.lower().strip()
    
    # URL decode
    url = unquote(url)
    
    # Remove protocol
    url = url.replace('https://', '').replace('http://', '')
    
    # Remove www.
    url = url.replace('www.', '')
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Extract just the slug
    if 'linkedin.com/in/' in url:
        parts = url.split('linkedin.com/in/')
        if len(parts) > 1:
            return 'linkedin.com/in/' + parts[1].split('?')[0].split('/')[0]
    
    return url

def investigate_talent_db():
    """Investigate PostgreSQL talent database in detail"""
    
    print("=" * 80)
    print("POSTGRESQL TALENT DATABASE - DEEP INVESTIGATION")
    print("=" * 80)
    
    conn = psycopg2.connect(
        dbname='talent',
        user=os.environ.get('PGUSER', os.environ.get('USER')),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check person table details
    print("\n📊 PERSON TABLE ANALYSIS")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM person")
    total = cursor.fetchone()[0]
    print(f"Total people: {total:,}")
    
    cursor.execute("SELECT COUNT(*) FROM person WHERE linkedin_url IS NOT NULL")
    with_linkedin = cursor.fetchone()[0]
    print(f"With LinkedIn URL: {with_linkedin:,} ({with_linkedin/total*100:.1f}%)")
    
    cursor.execute("SELECT COUNT(*) FROM person WHERE headline IS NOT NULL")
    with_headline = cursor.fetchone()[0]
    print(f"With headline: {with_headline:,} ({with_headline/total*100:.1f}%)")
    
    cursor.execute("SELECT COUNT(*) FROM person WHERE followers_count > 0")
    with_followers = cursor.fetchone()[0]
    print(f"With follower count: {with_followers:,} ({with_followers/total*100:.1f}%)")
    
    # Check for email presence anywhere
    print("\n🔍 CHECKING FOR EMAILS")
    print("-" * 80)
    
    # Check if there are any email-related columns
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'person'
        AND column_name LIKE '%email%'
    """)
    email_columns = cursor.fetchall()
    if email_columns:
        print("Email columns found in person table:")
        for col in email_columns:
            print(f"  - {col[0]}")
    else:
        print("❌ No email columns in person table")
    
    # Check other tables for emails
    cursor.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND column_name LIKE '%email%'
        ORDER BY table_name
    """)
    email_in_other_tables = cursor.fetchall()
    if email_in_other_tables:
        print("\nEmail columns in other tables:")
        for table, col in email_in_other_tables:
            print(f"  - {table}.{col}")
    
    # Check employment table
    print("\n📊 EMPLOYMENT TABLE ANALYSIS")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM employment")
    total_emp = cursor.fetchone()[0]
    print(f"Total employment records: {total_emp:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT person_id) FROM employment")
    unique_people_emp = cursor.fetchone()[0]
    print(f"Unique people with employment: {unique_people_emp:,}")
    print(f"Avg employment records per person: {total_emp/unique_people_emp:.1f}")
    
    # Check employment schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'employment'
        ORDER BY ordinal_position
    """)
    emp_columns = cursor.fetchall()
    print("\nEmployment table columns:")
    for col, dtype in emp_columns:
        print(f"  - {col}: {dtype}")
    
    # Check company table
    print("\n📊 COMPANY TABLE ANALYSIS")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM company")
    total_companies = cursor.fetchone()[0]
    print(f"Total companies: {total_companies:,}")
    
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'company'
        ORDER BY ordinal_position
    """)
    company_columns = cursor.fetchall()
    print("\nCompany table columns:")
    for col, dtype in company_columns:
        print(f"  - {col}: {dtype}")
    
    # Sample some companies
    cursor.execute("SELECT company_name, linkedin_url FROM company WHERE linkedin_url IS NOT NULL LIMIT 5")
    print("\nSample companies:")
    for name, url in cursor.fetchall():
        print(f"  - {name}: {url}")
    
    # Check education table
    print("\n📊 EDUCATION TABLE ANALYSIS")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM education")
    total_edu = cursor.fetchone()[0]
    print(f"Total education records: {total_edu:,}")
    
    if total_edu > 0:
        cursor.execute("SELECT COUNT(DISTINCT person_id) FROM education")
        unique_people_edu = cursor.fetchone()[0]
        print(f"Unique people with education: {unique_people_edu:,}")
    
    # Check edge_coemployment
    print("\n📊 EDGE_COEMPLOYMENT TABLE (Graph Relationships)")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM edge_coemployment")
    total_edges = cursor.fetchone()[0]
    print(f"Total co-employment edges: {total_edges:,}")
    
    if total_edges > 0:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'edge_coemployment'
            ORDER BY ordinal_position
        """)
        edge_columns = cursor.fetchall()
        print("\nEdge_coemployment columns:")
        for col, dtype in edge_columns:
            print(f"  - {col}: {dtype}")
    
    # Sample LinkedIn URL formats
    print("\n🔍 LINKEDIN URL FORMAT ANALYSIS")
    print("-" * 80)
    
    cursor.execute("SELECT linkedin_url FROM person WHERE linkedin_url IS NOT NULL LIMIT 10")
    print("\nSample LinkedIn URLs from talent database:")
    talent_urls = []
    for row in cursor.fetchall():
        url = row[0]
        normalized = normalize_linkedin_url(url)
        talent_urls.append(normalized)
        print(f"  Original: {url}")
        print(f"  Normalized: {normalized}\n")
    
    conn.close()
    
    # Now check SQLite for comparison
    print("\n🔍 COMPARING WITH SQLITE")
    print("-" * 80)
    
    import sqlite3
    sqlite_conn = sqlite3.connect("talent_intelligence.db")
    sqlite_cursor = sqlite_conn.cursor()
    
    sqlite_cursor.execute("""
        SELECT profile_url FROM social_profiles 
        WHERE platform='linkedin' 
        AND profile_url IS NOT NULL 
        LIMIT 10
    """)
    
    print("\nSample LinkedIn URLs from SQLite database:")
    sqlite_urls = []
    for row in sqlite_cursor.fetchall():
        url = row[0]
        normalized = normalize_linkedin_url(url)
        sqlite_urls.append(normalized)
        print(f"  Original: {url}")
        print(f"  Normalized: {normalized}\n")
    
    sqlite_conn.close()
    
    # Check for overlap with normalized URLs
    print("\n📊 OVERLAP WITH NORMALIZED URLS")
    print("-" * 80)
    
    overlap = set(talent_urls) & set(sqlite_urls)
    print(f"URLs in sample that appear in both: {len(overlap)}")
    print(f"Sample size - Talent: {len(talent_urls)}, SQLite: {len(sqlite_urls)}")
    
    if overlap:
        print("\nOverlapping URLs (normalized):")
        for url in overlap:
            print(f"  - {url}")
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    investigate_talent_db()


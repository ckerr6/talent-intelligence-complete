#!/usr/bin/env python3
# ABOUTME: Secure interactive database query tool with parameterized queries
# ABOUTME: Replaces vulnerable bash script with SQL injection protection

"""
Secure Talent Intelligence Database Query Tool

This replaces the vulnerable bash script with proper parameterized queries
to prevent SQL injection attacks.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import csv

DB_PATH = Path(__file__).parent / "talent_intelligence.db"

def connect_db():
    """Connect to database with safety checks"""
    if not DB_PATH.exists():
        print("❌ Database not found: talent_intelligence.db")
        print("Run ./RUN_ME.sh first to build the database")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def show_statistics():
    """Show database statistics"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n=== DATABASE STATISTICS ===")
    
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM people) as total_people,
            (SELECT COUNT(*) FROM people WHERE primary_email IS NOT NULL) as with_email,
            (SELECT COUNT(*) FROM social_profiles WHERE platform='linkedin') as with_linkedin,
            (SELECT COUNT(*) FROM social_profiles WHERE platform='github') as with_github,
            (SELECT COUNT(*) FROM employment WHERE is_current=1) as with_current_job,
            (SELECT ROUND(AVG(data_quality_score), 2) FROM people) as avg_quality_score
    """)
    
    stats = cursor.fetchone()
    labels = ['Total People', 'With Email', 'With LinkedIn', 'With GitHub', 'With Current Job', 'Avg Quality Score']
    
    for label, value in zip(labels, stats):
        print(f"{label}: {value}")
    
    conn.close()

def find_by_company():
    """Find candidates by company name (SQL injection safe)"""
    company = input("\nEnter company name (or part of it): ").strip()
    
    if not company:
        print("No company name provided")
        return
    
    conn = connect_db()
    cursor = conn.cursor()
    
    print(f"\n=== CANDIDATES AT companies matching '{company}' ===")
    
    # Using parameterized query to prevent SQL injection
    cursor.execute("""
        SELECT 
            p.first_name,
            p.last_name,
            p.primary_email,
            e.title
        FROM people p
        JOIN employment e ON p.person_id = e.person_id
        WHERE LOWER(e.company_name) LIKE LOWER(?)
        AND e.is_current = 1
        LIMIT 50
    """, (f'%{company}%',))
    
    results = cursor.fetchall()
    
    if not results:
        print("No candidates found")
    else:
        print(f"\n{'First Name':<15} {'Last Name':<15} {'Email':<30} {'Title':<25}")
        print("-" * 85)
        for row in results:
            first, last, email, title = row
            print(f"{(first or ''):<15} {(last or ''):<15} {(email or ''):<30} {(title or ''):<25}")
    
    conn.close()

def find_by_email_domain():
    """Find candidates by email domain (SQL injection safe)"""
    domain = input("\nEnter email domain (e.g., uniswap.org): ").strip()
    
    if not domain:
        print("No domain provided")
        return
    
    conn = connect_db()
    cursor = conn.cursor()
    
    print(f"\n=== CANDIDATES WITH @{domain} EMAILS ===")
    
    cursor.execute("""
        SELECT 
            first_name,
            last_name,
            primary_email
        FROM people
        WHERE primary_email LIKE ?
        LIMIT 50
    """, (f'%@{domain}',))
    
    results = cursor.fetchall()
    
    if not results:
        print("No candidates found")
    else:
        print(f"\n{'First Name':<15} {'Last Name':<15} {'Email':<30}")
        print("-" * 60)
        for row in results:
            first, last, email = row
            print(f"{(first or ''):<15} {(last or ''):<15} {(email or ''):<30}")
    
    conn.close()

def show_high_quality():
    """Show high-quality candidates"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n=== HIGH-QUALITY CANDIDATES (Score > 0.7) ===")
    
    cursor.execute("""
        SELECT 
            first_name,
            last_name,
            primary_email,
            data_quality_score as quality
        FROM people
        WHERE data_quality_score > 0.7
        ORDER BY data_quality_score DESC
        LIMIT 50
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No high-quality candidates found")
    else:
        print(f"\n{'First Name':<15} {'Last Name':<15} {'Email':<30} {'Quality':<8}")
        print("-" * 68)
        for row in results:
            first, last, email, quality = row
            print(f"{(first or ''):<15} {(last or ''):<15} {(email or ''):<30} {quality:<8.2f}")
    
    conn.close()

def get_profile_by_email():
    """Get complete profile by email (SQL injection safe)"""
    email = input("\nEnter email address: ").strip()
    
    if not email:
        print("No email provided")
        return
    
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n=== COMPLETE PROFILE ===")
    
    cursor.execute("""
        SELECT 
            p.first_name || ' ' || p.last_name as name,
            p.primary_email,
            p.location,
            e.company_name as current_company,
            e.title as current_title,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='linkedin') as linkedin,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='github') as github,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='twitter') as twitter,
            p.data_quality_score,
            p.created_at
        FROM people p
        LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
        WHERE p.primary_email = ?
    """, (email,))
    
    result = cursor.fetchone()
    
    if not result:
        print("No profile found for that email")
    else:
        labels = ['Name', 'Email', 'Location', 'Current Company', 'Current Title', 
                 'LinkedIn', 'GitHub', 'Twitter', 'Quality Score', 'Created']
        
        for label, value in zip(labels, result):
            if value:
                print(f"{label}: {value}")
    
    conn.close()

def search_by_name():
    """Search by name (SQL injection safe)"""
    first = input("\nEnter first name: ").strip()
    last = input("Enter last name: ").strip()
    
    if not first and not last:
        print("No name provided")
        return
    
    conn = connect_db()
    cursor = conn.cursor()
    
    print(f"\n=== SEARCH RESULTS ===")
    
    cursor.execute("""
        SELECT 
            p.first_name,
            p.last_name,
            p.primary_email,
            e.company_name
        FROM people p
        LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
        WHERE LOWER(p.first_name) LIKE LOWER(?)
        AND LOWER(p.last_name) LIKE LOWER(?)
        LIMIT 50
    """, (f'%{first}%', f'%{last}%'))
    
    results = cursor.fetchall()
    
    if not results:
        print("No candidates found")
    else:
        print(f"\n{'First Name':<15} {'Last Name':<15} {'Email':<30} {'Company':<25}")
        print("-" * 85)
        for row in results:
            first, last, email, company = row
            print(f"{(first or ''):<15} {(last or ''):<15} {(email or ''):<30} {(company or ''):<25}")
    
    conn.close()

def show_linkedin_profiles():
    """Show all LinkedIn profiles"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n=== ALL LINKEDIN PROFILES ===")
    
    cursor.execute("""
        SELECT 
            p.first_name,
            p.last_name,
            sp.profile_url
        FROM people p
        JOIN social_profiles sp ON p.person_id = sp.person_id
        WHERE sp.platform = 'linkedin'
        LIMIT 100
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No LinkedIn profiles found")
    else:
        print(f"\n{'First Name':<15} {'Last Name':<15} {'LinkedIn URL':<50}")
        print("-" * 80)
        for row in results:
            first, last, url = row
            print(f"{(first or ''):<15} {(last or ''):<15} {(url or ''):<50}")
    
    conn.close()

def export_to_csv():
    """Export candidates to CSV (SQL injection safe)"""
    filename = input("\nEnter output filename (e.g., candidates.csv): ").strip()
    
    if not filename:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    conn = connect_db()
    cursor = conn.cursor()
    
    print(f"\nExporting to {filename}...")
    
    cursor.execute("""
        SELECT 
            p.first_name,
            p.last_name,
            p.primary_email,
            p.location,
            e.company_name as current_company,
            e.title as current_title,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='linkedin') as linkedin_url,
            (SELECT profile_url FROM social_profiles WHERE person_id=p.person_id AND platform='github') as github_url,
            p.data_quality_score
        FROM people p
        LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
    """)
    
    results = cursor.fetchall()
    headers = ['first_name', 'last_name', 'email', 'location', 'current_company', 
               'current_title', 'linkedin_url', 'github_url', 'quality_score']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(results)
    
    print(f"✅ Exported {len(results)} records to {filename}")
    
    conn.close()

def main():
    """Main menu loop"""
    print("=" * 60)
    print("🔍 Talent Intelligence Database Explorer (Secure Version)")
    print("=" * 60)
    
    menu_options = [
        ("1", "Show database statistics", show_statistics),
        ("2", "Find candidates by company", find_by_company),
        ("3", "Find candidates by email domain", find_by_email_domain),
        ("4", "Show high-quality candidates", show_high_quality),
        ("5", "Get complete profile by email", get_profile_by_email),
        ("6", "Search by name", search_by_name),
        ("7", "Show all LinkedIn profiles", show_linkedin_profiles),
        ("8", "Export candidates to CSV", export_to_csv),
        ("9", "Open SQLite shell", lambda: sys.exit(sqlite3.main([str(DB_PATH)]))),
        ("0", "Exit", lambda: sys.exit(0))
    ]
    
    while True:
        print("\nWhat would you like to do?")
        print()
        
        for option, description, _ in menu_options:
            print(f"{option}. {description}")
        
        print()
        choice = input("Enter choice (0-9): ").strip()
        
        # Find and execute the chosen option
        for option, _, func in menu_options:
            if choice == option:
                try:
                    func()
                except KeyboardInterrupt:
                    print("\n\nOperation cancelled")
                except Exception as e:
                    print(f"\nError: {e}")
                break
        else:
            print("Invalid choice. Please try again.")
        
        if choice not in ["0", "9"]:
            print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)

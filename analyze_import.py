#!/usr/bin/env python3
"""
Analyze skipped records with LinkedIn/GitHub URLs and spot-check enrichment
"""

import csv
import psycopg2
import psycopg2.extras
from config import get_db_connection
from migration_scripts.migration_utils import normalize_linkedin_url

def analyze_skipped_with_urls(csv_path):
    """Find records with LinkedIn/GitHub URLs that were skipped"""
    print("\n" + "="*80)
    print("SKIPPED RECORDS WITH LINKEDIN/GITHUB URLS")
    print("="*80)
    
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    skipped_with_urls = []
    total_with_linkedin = 0
    total_with_github = 0
    successfully_processed = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            linkedin_url = row.get('LinkedIn URL', '').strip()
            github_url = row.get('GitHub URL', '').strip()
            
            if not linkedin_url and not github_url:
                continue
            
            if linkedin_url:
                total_with_linkedin += 1
            if github_url:
                total_with_github += 1
            
            # Check if this person exists in database
            normalized_linkedin = normalize_linkedin_url(linkedin_url) if linkedin_url else None
            
            if normalized_linkedin:
                cursor.execute("""
                    SELECT person_id::text, full_name
                    FROM person
                    WHERE normalized_linkedin_url = %s
                """, (normalized_linkedin,))
                
                result = cursor.fetchone()
                if result and result['person_id']:
                    successfully_processed += 1
                    continue
            
            # If we get here, record was skipped
            skip_reason = []
            if not row.get('Full Name', '').strip():
                skip_reason.append("no name")
            if not linkedin_url:
                skip_reason.append("no LinkedIn URL")
            elif not normalized_linkedin:
                skip_reason.append("invalid LinkedIn URL format")
            
            if not skip_reason:
                skip_reason.append("unknown - possibly duplicate")
            
            skipped_with_urls.append({
                'name': row.get('Full Name', '(no name)'),
                'company': row.get('Company', '(no company)'),
                'location': row.get('Location', ''),
                'linkedin': linkedin_url,
                'github': github_url,
                'reason': ', '.join(skip_reason)
            })
    
    cursor.close()
    conn.close()
    
    print(f"\n📊 Summary:")
    print(f"  • Total records with LinkedIn URL: {total_with_linkedin:,}")
    print(f"  • Total records with GitHub URL: {total_with_github:,}")
    print(f"  • Successfully processed: {successfully_processed:,}")
    print(f"  • Skipped (with URLs): {len(skipped_with_urls):,}")
    
    if skipped_with_urls:
        print(f"\n⚠️  First 20 skipped records with LinkedIn/GitHub URLs:")
        print()
        for i, record in enumerate(skipped_with_urls[:20], 1):
            print(f"{i}. {record['name']} @ {record['company']}")
            if record['location']:
                print(f"   Location: {record['location']}")
            if record['linkedin']:
                print(f"   LinkedIn: {record['linkedin']}")
            if record['github']:
                print(f"   GitHub: {record['github']}")
            print(f"   ❌ Skip reason: {record['reason']}")
            print()
    
    return len(skipped_with_urls)

def spot_check_enrichment():
    """Spot check enriched profiles"""
    print("\n" + "="*80)
    print("ENRICHMENT SPOT CHECK - PROFILES WITH NEW DATA")
    print("="*80)
    
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    # Find profiles that were enriched in the last 2 hours
    print("\n🔍 Finding profiles enriched in the last 2 hours...\n")
    
    cursor.execute("""
        SELECT 
            p.person_id::text,
            p.full_name,
            p.first_name,
            p.last_name,
            p.location,
            p.headline,
            p.linkedin_url,
            p.normalized_linkedin_url,
            p.refreshed_at,
            (SELECT COUNT(*) FROM person_email WHERE person_id = p.person_id) as email_count,
            (SELECT COUNT(*) FROM employment WHERE person_id = p.person_id) as employment_count,
            (SELECT COUNT(*) FROM github_profile WHERE person_id = p.person_id) as github_count
        FROM person p
        WHERE p.refreshed_at >= NOW() - INTERVAL '2 hours'
        ORDER BY p.refreshed_at DESC
        LIMIT 15
    """)
    
    enriched_profiles = cursor.fetchall()
    
    if not enriched_profiles:
        print("⚠️  No profiles enriched in the last 2 hours")
        conn.close()
        return
    
    print(f"✅ Found {len(enriched_profiles)} recently enriched profiles\n")
    print("="*80)
    
    for i, profile in enumerate(enriched_profiles, 1):
        person_id = profile['person_id']
        full_name = profile['full_name']
        first_name = profile['first_name']
        last_name = profile['last_name']
        location = profile['location']
        headline = profile['headline']
        linkedin_url = profile['linkedin_url']
        normalized_linkedin = profile['normalized_linkedin_url']
        refreshed_at = profile['refreshed_at']
        email_count = profile['email_count']
        employment_count = profile['employment_count']
        github_count = profile['github_count']
        
        print(f"\n{i}. {full_name or '(no name)'}")
        print(f"   {'─'*70}")
        print(f"   Person ID: {person_id}")
        print(f"   Name fields: First='{first_name}' | Last='{last_name}'")
        print(f"   Location: {location or '(empty)'}")
        print(f"   Headline: {headline or '(empty)'}")
        print(f"   LinkedIn: {linkedin_url or '(none)'}")
        print(f"   Last Refreshed: {refreshed_at}")
        print(f"   Data counts: {email_count} emails | {employment_count} jobs | {github_count} GitHub")
        
        # Get employment details
        cursor.execute("""
            SELECT 
                c.company_name,
                c.company_domain,
                e.title,
                e.start_date,
                e.end_date
            FROM employment e
            JOIN company c ON e.company_id = c.company_id
            WHERE e.person_id = %s::uuid
            ORDER BY e.start_date DESC NULLS LAST
            LIMIT 5
        """, (person_id,))
        
        jobs = cursor.fetchall()
        if jobs:
            print(f"\n   📋 Employment history ({len(jobs)} records):")
            for job in jobs:
                company_name = job['company_name']
                company_domain = job['company_domain']
                title = job['title']
                start_date = job['start_date']
                end_date = job['end_date']
                date_range = ""
                if start_date or end_date:
                    date_range = f" ({start_date or 'unknown'} - {end_date or 'present'})"
                print(f"      • {title or '(no title)'} at {company_name}{date_range}")
                print(f"        Domain: {company_domain}")
        
        # Get GitHub info
        cursor.execute("""
            SELECT 
                github_username,
                source
            FROM github_profile
            WHERE person_id = %s::uuid
        """, (person_id,))
        
        github = cursor.fetchall()
        if github:
            print(f"\n   🐙 GitHub profiles:")
            for gh in github:
                username = gh['github_username']
                source = gh['source']
                print(f"      • @{username}")
                print(f"        URL: https://github.com/{username}")
                print(f"        Source: {source}")
        
        # Get email info
        cursor.execute("""
            SELECT 
                email,
                email_type,
                is_primary,
                source
            FROM person_email
            WHERE person_id = %s::uuid
            ORDER BY is_primary DESC
            LIMIT 5
        """, (person_id,))
        
        emails = cursor.fetchall()
        if emails:
            print(f"\n   📧 Email addresses ({len(emails)}):")
            for email_data in emails:
                email = email_data['email']
                email_type = email_data['email_type']
                is_primary = email_data['is_primary']
                source = email_data['source']
                primary_flag = " ⭐ PRIMARY" if is_primary else ""
                print(f"      • {email} ({email_type}){primary_flag}")
                print(f"        Source: {source}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)

def main():
    CSV_PATH = "/Users/charlie.kerr/DataBlend1021/dedupe_PB_test.csv"
    
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "CSV IMPORT ANALYSIS REPORT" + " "*32 + "║")
    print("╚" + "═"*78 + "╝")
    
    # 1. Analyze skipped records with URLs
    num_skipped = analyze_skipped_with_urls(CSV_PATH)
    
    # 2. Spot check enrichment
    spot_check_enrichment()
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n✓ Found {num_skipped:,} skipped records that had LinkedIn/GitHub URLs")
    print(f"✓ Displayed enrichment details for recently updated profiles")
    print()

if __name__ == "__main__":
    main()


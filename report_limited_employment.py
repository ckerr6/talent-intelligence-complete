#!/usr/bin/env python3
"""
Generate a report of people profiles with LinkedIn URLs but limited employment history.
Outputs a CSV of profiles needing enrichment.
"""

import csv
from datetime import datetime
from config import get_db_connection, Config

def generate_limited_employment_report():
    """Find people with LinkedIn but limited employment history"""
    
    print("=" * 80)
    print("LINKEDIN PROFILES NEEDING EMPLOYMENT ENRICHMENT")
    print("=" * 80)
    print()
    
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    # Query to find people with LinkedIn URLs but 0 or 1 employment records
    query = """
    WITH employment_counts AS (
        SELECT 
            p.person_id,
            p.full_name,
            p.first_name,
            p.last_name,
            p.linkedin_url,
            p.location,
            p.headline,
            COUNT(e.employment_id) as employment_count
        FROM person p
        LEFT JOIN employment e ON p.person_id = e.person_id
        WHERE p.linkedin_url IS NOT NULL 
          AND p.linkedin_url != ''
        GROUP BY p.person_id, p.full_name, p.first_name, p.last_name, 
                 p.linkedin_url, p.location, p.headline
    )
    SELECT 
        person_id,
        full_name,
        first_name,
        last_name,
        linkedin_url,
        location,
        headline,
        employment_count
    FROM employment_counts
    WHERE employment_count <= 1
    ORDER BY employment_count ASC, full_name ASC
    """
    
    print("🔍 Querying database for profiles with LinkedIn but limited employment history...")
    print()
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Separate into two groups
    no_employment = [r for r in results if r['employment_count'] == 0]
    one_employment = [r for r in results if r['employment_count'] == 1]
    
    print(f"📊 SUMMARY")
    print("-" * 80)
    print(f"  Total profiles needing enrichment: {len(results):,}")
    print(f"    • Profiles with NO employment records: {len(no_employment):,}")
    print(f"    • Profiles with ONLY ONE employment record: {len(one_employment):,}")
    print()
    
    # Generate CSV output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = Config.EXPORT_DIR / f"profiles_need_employment_enrichment_{timestamp}.csv"
    
    print(f"📝 Generating CSV export: {csv_filename}")
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'person_id', 'full_name', 'first_name', 'last_name', 
            'linkedin_url', 'location', 'headline', 'employment_count'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for row in results:
            writer.writerow({
                'person_id': row['person_id'],
                'full_name': row['full_name'] or '',
                'first_name': row['first_name'] or '',
                'last_name': row['last_name'] or '',
                'linkedin_url': row['linkedin_url'],
                'location': row['location'] or '',
                'headline': row['headline'] or '',
                'employment_count': row['employment_count']
            })
    
    print(f"✅ CSV exported successfully!")
    print()
    
    # Show sample of profiles (first 10 with no employment)
    print("📋 SAMPLE OF PROFILES WITH NO EMPLOYMENT (First 10):")
    print("-" * 80)
    for i, profile in enumerate(no_employment[:10], 1):
        print(f"{i}. {profile['full_name'] or 'N/A'}")
        print(f"   LinkedIn: {profile['linkedin_url']}")
        print(f"   Location: {profile['location'] or 'N/A'}")
        print(f"   Headline: {profile['headline'] or 'N/A'}")
        print()
    
    if len(no_employment) > 10:
        print(f"   ... and {len(no_employment) - 10:,} more with no employment")
        print()
    
    # Additional statistics
    print("📈 ADDITIONAL STATISTICS")
    print("-" * 80)
    
    # Count profiles with location data
    with_location = sum(1 for r in results if r['location'])
    print(f"  Profiles with location data: {with_location:,} ({with_location/len(results)*100:.1f}%)")
    
    # Count profiles with headline
    with_headline = sum(1 for r in results if r['headline'])
    print(f"  Profiles with headline data: {with_headline:,} ({with_headline/len(results)*100:.1f}%)")
    
    print()
    print("=" * 80)
    print(f"✅ REPORT COMPLETE")
    print(f"   Total individuals needing enrichment: {len(results):,}")
    print(f"   CSV exported to: {csv_filename}")
    print("=" * 80)
    
    # Clean up
    cursor.close()
    if Config.DB_TYPE == 'postgresql':
        Config.return_connection(conn)
    else:
        conn.close()
    
    return {
        'total': len(results),
        'no_employment': len(no_employment),
        'one_employment': len(one_employment),
        'csv_file': str(csv_filename)
    }


if __name__ == "__main__":
    try:
        results = generate_limited_employment_report()
        print()
        print("🎯 NEXT STEPS:")
        print(f"   1. Review the CSV file: {results['csv_file']}")
        print(f"   2. Begin enrichment for {results['total']:,} profiles")
        print("   3. Use LinkedIn URLs to gather full employment histories")
        print()
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()


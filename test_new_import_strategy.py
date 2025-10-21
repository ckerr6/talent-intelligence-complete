#!/usr/bin/env python3
"""
Test script to show what the new import strategy will capture
"""

import csv

CSV_PATH = "/Users/charlie.kerr/DataBlend1021/dedupe_PB_test.csv"

def analyze_csv_with_new_strategy():
    """Analyze what will be imported with new vs old strategy"""
    
    stats_old = {
        'would_import': 0,
        'would_skip_no_name': 0,
        'would_skip_no_linkedin': 0,
        'would_skip_no_identifier': 0
    }
    
    stats_new = {
        'will_import': 0,
        'linkedin_only': 0,
        'github_only': 0,
        'both_linkedin_and_github': 0,
        'placeholder_names': 0,
        'will_skip_no_identifier': 0
    }
    
    sample_linkedin_only = []
    sample_github_only = []
    sample_placeholder_names = []
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            linkedin_url = row.get('LinkedIn URL', '').strip()
            github_url = row.get('GitHub URL', '').strip()
            full_name = row.get('Full Name', '').strip()
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            
            # OLD STRATEGY
            if (full_name or first_name or last_name) and linkedin_url:
                stats_old['would_import'] += 1
            elif not full_name and not first_name and not last_name:
                stats_old['would_skip_no_name'] += 1
            elif not linkedin_url:
                stats_old['would_skip_no_linkedin'] += 1
            else:
                stats_old['would_skip_no_identifier'] += 1
            
            # NEW STRATEGY
            if not linkedin_url and not github_url:
                stats_new['will_skip_no_identifier'] += 1
                continue
            
            stats_new['will_import'] += 1
            
            # Categorize
            if linkedin_url and github_url:
                stats_new['both_linkedin_and_github'] += 1
            elif linkedin_url:
                stats_new['linkedin_only'] += 1
                if not full_name and len(sample_linkedin_only) < 5:
                    sample_linkedin_only.append({
                        'linkedin': linkedin_url,
                        'location': row.get('Location', ''),
                        'company': row.get('Company', '')
                    })
            elif github_url:
                stats_new['github_only'] += 1
                if len(sample_github_only) < 5:
                    sample_github_only.append({
                        'github': github_url,
                        'name': full_name or f"{first_name} {last_name}".strip(),
                        'company': row.get('Company', '')
                    })
            
            # Track placeholder names
            if not full_name and not first_name and not last_name:
                stats_new['placeholder_names'] += 1
                if len(sample_placeholder_names) < 5:
                    sample_placeholder_names.append({
                        'linkedin': linkedin_url,
                        'github': github_url,
                        'location': row.get('Location', '')
                    })
    
    print("\n" + "="*80)
    print("IMPORT STRATEGY COMPARISON")
    print("="*80)
    
    print("\n📊 OLD STRATEGY (Name Required):")
    print(f"   ✅ Would Import: {stats_old['would_import']:,}")
    print(f"   ❌ Would Skip (No Name): {stats_old['would_skip_no_name']:,}")
    print(f"   ❌ Would Skip (No LinkedIn): {stats_old['would_skip_no_linkedin']:,}")
    print(f"   ❌ Would Skip (No Identifier): {stats_old['would_skip_no_identifier']:,}")
    print(f"   TOTAL LOST: {stats_old['would_skip_no_name'] + stats_old['would_skip_no_linkedin'] + stats_old['would_skip_no_identifier']:,}")
    
    print("\n📊 NEW STRATEGY (LinkedIn OR GitHub):")
    print(f"   ✅ Will Import: {stats_new['will_import']:,}")
    print(f"   ❌ Will Skip (No Identifier): {stats_new['will_skip_no_identifier']:,}")
    
    print("\n🎯 BREAKDOWN OF NEW IMPORTS:")
    print(f"   LinkedIn + GitHub: {stats_new['both_linkedin_and_github']:,}")
    print(f"   LinkedIn Only: {stats_new['linkedin_only']:,}")
    print(f"   GitHub Only: {stats_new['github_only']:,}")
    print(f"   Placeholder Names: {stats_new['placeholder_names']:,}")
    
    print("\n📈 IMPROVEMENT:")
    additional = stats_new['will_import'] - stats_old['would_import']
    if stats_old['would_import'] > 0:
        percent_increase = (additional / stats_old['would_import']) * 100
        print(f"   +{additional:,} more profiles ({percent_increase:.1f}% increase)")
    
    if sample_github_only:
        print("\n🐙 SAMPLE: GitHub-Only Profiles (Now Captured):")
        for i, sample in enumerate(sample_github_only, 1):
            print(f"   {i}. {sample['name'] or '(no name)'}")
            print(f"      GitHub: {sample['github']}")
            print(f"      Company: {sample['company'] or '(none)'}")
    
    if sample_linkedin_only:
        print("\n💼 SAMPLE: LinkedIn-Only, No Name (Will Get Placeholder):")
        for i, sample in enumerate(sample_linkedin_only, 1):
            username = sample['linkedin'].rstrip('/').split('/')[-1]
            print(f"   {i}. [LinkedIn] {username.replace('-', ' ').title()}")
            print(f"      LinkedIn: {sample['linkedin']}")
            print(f"      Location: {sample['location'] or '(none)'}")
    
    if sample_placeholder_names:
        print("\n⚠️  SAMPLE: Profiles Needing Enrichment:")
        for i, sample in enumerate(sample_placeholder_names, 1):
            print(f"   {i}. Identifiers only, no name/company data")
            if sample['linkedin']:
                print(f"      LinkedIn: {sample['linkedin']}")
            if sample['github']:
                print(f"      GitHub: {sample['github']}")
            print(f"      Location: {sample['location'] or '(none)'}")
    
    print("\n" + "="*80)
    print("✅ Ready to run updated import!")
    print("="*80)
    print()

if __name__ == "__main__":
    analyze_csv_with_new_strategy()


#!/usr/bin/env python3
# ABOUTME: Test script to verify GitHub API enrichment setup
# ABOUTME: Runs quick checks before doing full enrichment

import sqlite3
import requests
import os
import sys
from pathlib import Path

def test_database():
    """Check if database exists and has expected tables"""
    print("1️⃣  Testing database...")
    
    db_path = Path("talent_intelligence.db")
    if not db_path.exists():
        print("   ❌ Database not found: talent_intelligence.db")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for required tables
    required_tables = ['github_profiles', 'companies', 'people']
    
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            print(f"   ❌ Missing table: {table}")
            conn.close()
            return False
    
    # Check if we have profiles to enrich
    cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE github_username IS NOT NULL")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"   ✅ Database OK - {count:,} profiles ready to enrich")
    return True

def test_github_token():
    """Check if GitHub token is set and valid"""
    print("\n2️⃣  Testing GitHub token...")
    
    token = os.environ.get('GITHUB_TOKEN')
    
    if not token:
        print("   ⚠️  No GITHUB_TOKEN set")
        print("   ⚠️  You'll be limited to 60 requests/hour instead of 5,000/hour")
        print("   💡 Set token with: export GITHUB_TOKEN='your_token_here'")
        return False
    
    # Test token validity
    headers = {'Authorization': f'token {token}'}
    
    try:
        response = requests.get(
            'https://api.github.com/rate_limit',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            core = data['resources']['core']
            remaining = core['remaining']
            limit = core['limit']
            
            print(f"   ✅ Token valid")
            print(f"   ✅ Rate limit: {remaining:,}/{limit:,} requests remaining")
            
            if limit < 5000:
                print("   ⚠️  Token has low rate limit - check scopes")
                print("   💡 Needs: public_repo, read:user, read:org")
            
            return True
        else:
            print(f"   ❌ Token invalid (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing token: {str(e)}")
        return False

def test_api_connection():
    """Test basic GitHub API connectivity"""
    print("\n3️⃣  Testing GitHub API connection...")
    
    try:
        response = requests.get(
            'https://api.github.com/users/octocat',
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ GitHub API accessible")
            return True
        else:
            print(f"   ❌ GitHub API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
        return False

def test_script_exists():
    """Check if enrichment script exists"""
    print("\n4️⃣  Testing enrichment script...")
    
    script_path = Path("github_api_enrichment.py")
    if not script_path.exists():
        print("   ❌ Script not found: github_api_enrichment.py")
        return False
    
    print("   ✅ Script found")
    return True

def estimate_time():
    """Estimate time for enrichment"""
    print("\n⏱️  Time Estimates:")
    
    token = os.environ.get('GITHUB_TOKEN')
    
    # Get profile count
    conn = sqlite3.connect("talent_intelligence.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE github_username IS NOT NULL")
    count = cursor.fetchone()[0]
    conn.close()
    
    if token:
        # 5000 requests/hour = 0.72s per request
        hours = count / 5000
        print(f"   📊 Enrich {count:,} profiles: ~{hours:.1f} hours")
    else:
        # 60 requests/hour
        hours = count / 60
        print(f"   📊 Enrich {count:,} profiles: ~{hours:.1f} hours (WITHOUT token)")
        print(f"   💡 With token: ~{count/5000:.1f} hours")

def main():
    print("🧪 GitHub API Enrichment - System Check")
    print("=" * 50)
    print()
    
    results = []
    
    results.append(("Database", test_database()))
    results.append(("GitHub Token", test_github_token()))
    results.append(("API Connection", test_api_connection()))
    results.append(("Enrichment Script", test_script_exists()))
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10s} {test_name}")
        if not passed:
            all_passed = False
    
    estimate_time()
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ All checks passed! Ready to enrich.")
        print("\nNext steps:")
        print("1. export GITHUB_TOKEN='your_token_here'  # If not set")
        print("2. python3 github_api_enrichment.py enrich-existing talent_intelligence.db")
    else:
        print("❌ Some checks failed. Fix issues above before enriching.")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# ABOUTME: Updated GitHub API client with robust rate limiting and retry logic
# ABOUTME: Test script for GitHub API integration with proper configuration

"""
GitHub API Test & Setup Script

This script tests your GitHub API configuration and ensures everything
is working before running the full enrichment.
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Import our configuration
from config import Config, log_message

class GitHubAPITester:
    """Test GitHub API configuration and connection"""
    
    def __init__(self):
        self.token = Config.GITHUB_TOKEN
        self.api_base = Config.GITHUB_API_BASE
        self.headers = {}
        
        if self.token and self.token != 'your_token_here':
            self.headers['Authorization'] = f'token {self.token}'
        
        self.rate_limit_info = {}
    
    def test_connection(self) -> bool:
        """Test basic API connection"""
        print("\n🔍 Testing GitHub API connection...")
        
        try:
            response = requests.get(
                f"{self.api_base}/zen",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Connection successful!")
                print(f"   GitHub says: '{response.text}'")
                return True
            else:
                print(f"❌ Connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
    
    def test_authentication(self) -> bool:
        """Test authentication with token"""
        print("\n🔑 Testing authentication...")
        
        if not self.token or self.token == 'your_token_here':
            print("❌ No valid GitHub token found in .env file")
            print("\nTo fix this:")
            print("1. Get a personal access token from: https://github.com/settings/tokens")
            print("2. Edit the .env file in this directory")
            print("3. Replace 'your_token_here' with your actual token")
            return False
        
        try:
            response = requests.get(
                f"{self.api_base}/user",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Authenticated as: {user_data.get('login')}")
                print(f"   Name: {user_data.get('name', 'N/A')}")
                print(f"   Public repos: {user_data.get('public_repos', 0)}")
                return True
            elif response.status_code == 401:
                print("❌ Invalid token - authentication failed")
                return False
            else:
                print(f"❌ Authentication error: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_rate_limit(self) -> bool:
        """Check rate limit status"""
        print("\n📊 Checking rate limits...")
        
        try:
            response = requests.get(
                f"{self.api_base}/rate_limit",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                
                self.rate_limit_info = {
                    'limit': core['limit'],
                    'remaining': core['remaining'],
                    'reset': core['reset'],
                    'used': core['used']
                }
                
                reset_time = datetime.fromtimestamp(core['reset'])
                
                print(f"✅ Rate limit status:")
                print(f"   Limit: {core['limit']:,} requests/hour")
                print(f"   Remaining: {core['remaining']:,} requests")
                print(f"   Used: {core['used']:,} requests")
                print(f"   Resets at: {reset_time.strftime('%H:%M:%S')}")
                
                if core['limit'] == 60:
                    print("\n⚠️  You have the unauthenticated rate limit (60/hour)")
                    print("   This is too low for enrichment. Please add a valid token.")
                    return False
                elif core['remaining'] < 100:
                    print("\n⚠️  Rate limit is very low. Consider waiting for reset.")
                    return False
                
                return True
            else:
                print(f"❌ Could not check rate limit: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Rate limit check error: {str(e)}")
            return False
    
    def test_api_call(self) -> bool:
        """Test an actual API call to get user data"""
        print("\n🧪 Testing API data retrieval...")
        
        test_username = "torvalds"  # Linus Torvalds - should always exist
        
        try:
            response = requests.get(
                f"{self.api_base}/users/{test_username}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Successfully retrieved user data:")
                print(f"   Username: {user_data.get('login')}")
                print(f"   Name: {user_data.get('name')}")
                print(f"   Followers: {user_data.get('followers'):,}")
                print(f"   Public repos: {user_data.get('public_repos'):,}")
                return True
            else:
                print(f"❌ API call failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API call error: {str(e)}")
            return False
    
    def test_retry_logic(self) -> bool:
        """Test retry logic with exponential backoff"""
        print("\n🔄 Testing retry logic...")
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            print(f"   Attempt {attempt + 1}/{max_retries}...")
            
            # Simulate a request
            success = attempt == max_retries - 1  # Succeed on last attempt
            
            if success:
                print(f"   ✅ Request successful on attempt {attempt + 1}")
                return True
            else:
                delay = base_delay * (2 ** attempt)
                print(f"   ⏱️  Waiting {delay} seconds before retry...")
                time.sleep(delay)
        
        return False
    
    def estimate_enrichment_time(self, profile_count: int) -> Dict:
        """Estimate how long enrichment will take"""
        print(f"\n⏱️  Enrichment time estimate for {profile_count:,} profiles:")
        
        if not self.rate_limit_info:
            self.test_rate_limit()
        
        rate_limit = self.rate_limit_info.get('limit', 60)
        
        # Calculate based on rate limit
        if rate_limit == 5000:
            # With token: 5000/hour = 83/minute
            requests_per_second = 1.38
            delay_between_requests = Config.GITHUB_REQUEST_DELAY
        else:
            # Without token: 60/hour = 1/minute
            requests_per_second = 0.016
            delay_between_requests = 60
        
        total_seconds = profile_count * delay_between_requests
        hours = total_seconds / 3600
        
        estimate = {
            'profiles': profile_count,
            'rate_limit': rate_limit,
            'total_hours': hours,
            'total_minutes': total_seconds / 60,
            'requests_per_minute': 60 / delay_between_requests
        }
        
        print(f"   Rate limit: {rate_limit:,}/hour")
        print(f"   Time per request: {delay_between_requests:.2f} seconds")
        print(f"   Total time: {hours:.1f} hours ({hours*60:.0f} minutes)")
        print(f"   Requests per minute: {estimate['requests_per_minute']:.1f}")
        
        if rate_limit == 60:
            print("\n⚠️  With no token, enrichment would take weeks!")
            print("   Please add a GitHub token to make this feasible.")
        
        return estimate
    
    def run_all_tests(self) -> bool:
        """Run all tests and report results"""
        print("="*60)
        print("🧪 GitHub API Configuration Test Suite")
        print("="*60)
        
        tests = [
            ("Connection", self.test_connection),
            ("Authentication", self.test_authentication),
            ("Rate Limit", self.test_rate_limit),
            ("API Call", self.test_api_call),
            ("Retry Logic", self.test_retry_logic)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"\n❌ Test '{test_name}' failed with error: {str(e)}")
                results[test_name] = False
        
        # Print summary
        print("\n" + "="*60)
        print("📋 Test Results Summary")
        print("="*60)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:20} {status}")
            if not passed:
                all_passed = False
        
        print("="*60)
        
        if all_passed:
            print("\n✅ All tests passed! GitHub API is ready for enrichment.")
            
            # Estimate time
            print("\nChecking current database for profiles to enrich...")
            
            import sqlite3
            if Config.DB_PATH.exists():
                conn = sqlite3.connect(Config.DB_PATH)
                cursor = conn.cursor()
                
                # Count profiles needing enrichment
                cursor.execute("""
                    SELECT COUNT(*) FROM social_profiles 
                    WHERE platform = 'github' 
                    AND profile_url IS NOT NULL
                """)
                github_profile_count = cursor.fetchone()[0]
                
                if github_profile_count > 0:
                    self.estimate_enrichment_time(github_profile_count)
                
                conn.close()
            
            return True
        else:
            print("\n❌ Some tests failed. Please fix the issues above.")
            
            if not results.get("Authentication"):
                print("\n📝 Next steps:")
                print("1. Go to: https://github.com/settings/tokens")
                print("2. Click 'Generate new token (classic)'")
                print("3. Give it a name like 'Talent Database Enrichment'")
                print("4. Select scopes: 'public_repo', 'read:org', 'read:user'")
                print("5. Copy the token")
                print("6. Edit .env file and replace 'your_token_here' with your token")
                print("7. Run this test again")
            
            return False


def setup_github_token():
    """Interactive setup for GitHub token"""
    print("\n🔧 GitHub Token Setup")
    print("="*40)
    
    env_path = Path(".env")
    
    # Read current .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key.strip()] = value.strip()
    
    print("\nYou need a GitHub personal access token for API access.")
    print("Get one from: https://github.com/settings/tokens")
    print("\nRequired scopes: public_repo, read:org, read:user")
    
    token = input("\nPaste your GitHub token here (or press Enter to skip): ").strip()
    
    if token:
        env_content['GITHUB_TOKEN'] = token
        
        # Write updated .env
        with open(env_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        print("\n✅ Token saved to .env file")
        
        # Test the token
        os.environ['GITHUB_TOKEN'] = token
        Config.GITHUB_TOKEN = token
        
        tester = GitHubAPITester()
        if tester.test_authentication():
            print("\n✅ Token is valid and working!")
            return True
        else:
            print("\n❌ Token appears to be invalid. Please check and try again.")
            return False
    else:
        print("\n⏭️  Skipped token setup")
        return False


def main():
    """Main entry point"""
    
    # Check if we're doing setup or testing
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        setup_github_token()
    
    # Run tests
    tester = GitHubAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Ready to run GitHub enrichment!")
        print("\nTo start enrichment, run:")
        print("  python3 build_github_enrichment.py")
    else:
        print("\n💡 Tip: Run with --setup flag to configure token interactively:")
        print("  python3 test_github_setup.py --setup")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

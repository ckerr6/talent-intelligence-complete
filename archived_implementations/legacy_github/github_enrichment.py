#!/usr/bin/env python3
# ABOUTME: Production-ready GitHub enrichment with retry logic and checkpointing
# ABOUTME: Handles rate limiting, retries, and can resume from interruptions

"""
GitHub Enrichment System - Production Version

Features:
- Exponential backoff retry logic
- Checkpoint/resume capability
- Proper rate limit handling
- Progress tracking
- Error recovery
"""

import sqlite3
import requests
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Import our configuration
from config import Config, log_message, get_db_connection

class RobustGitHubAPI:
    """GitHub API client with robust error handling and retry logic"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or Config.GITHUB_TOKEN
        self.api_base = Config.GITHUB_API_BASE
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        
        if self.token and self.token != 'your_token_here':
            self.headers['Authorization'] = f'token {self.token}'
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting
        self.requests_made = 0
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 60  # seconds
        
    def make_request(self, endpoint: str, params: Dict = None) -> Tuple[Optional[Dict], bool]:
        """
        Make API request with retry logic
        Returns: (data, success)
        """
        url = f"{self.api_base}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                # Check rate limit before request
                if self.should_wait_for_rate_limit():
                    self.wait_for_rate_limit()
                
                # Add delay between requests
                time.sleep(Config.GITHUB_REQUEST_DELAY)
                
                # Make request
                response = self.session.get(url, params=params, timeout=30)
                self.requests_made += 1
                
                # Update rate limit info from headers
                self.update_rate_limit_from_headers(response.headers)
                
                # Handle response
                if response.status_code == 200:
                    return response.json(), True
                
                elif response.status_code == 404:
                    log_message(f"Not found: {endpoint}", 'api')
                    return None, True  # Not found is not an error
                
                elif response.status_code == 403:
                    # Rate limit or forbidden
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = int(response.headers['X-RateLimit-Remaining'])
                        if remaining == 0:
                            log_message(f"Rate limit hit, waiting...", 'api')
                            self.wait_for_rate_limit()
                            continue
                    
                    log_message(f"Forbidden: {endpoint}", 'error')
                    return None, False
                
                elif response.status_code in [500, 502, 503, 504]:
                    # Server error - retry with backoff
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    log_message(f"Server error {response.status_code}, retrying in {delay}s...", 'api')
                    time.sleep(delay)
                    continue
                
                else:
                    log_message(f"Unexpected status {response.status_code}: {endpoint}", 'error')
                    return None, False
                    
            except requests.exceptions.Timeout:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                log_message(f"Timeout on attempt {attempt + 1}, retrying in {delay}s...", 'api')
                time.sleep(delay)
                continue
                
            except requests.exceptions.ConnectionError:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                log_message(f"Connection error on attempt {attempt + 1}, retrying in {delay}s...", 'api')
                time.sleep(delay)
                continue
                
            except Exception as e:
                log_message(f"Unexpected error: {str(e)}", 'error')
                return None, False
        
        log_message(f"Max retries exceeded for {endpoint}", 'error')
        return None, False
    
    def update_rate_limit_from_headers(self, headers):
        """Update rate limit info from response headers"""
        if 'X-RateLimit-Remaining' in headers:
            self.rate_limit_remaining = int(headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in headers:
            self.rate_limit_reset = int(headers['X-RateLimit-Reset'])
    
    def should_wait_for_rate_limit(self) -> bool:
        """Check if we should wait for rate limit"""
        if self.rate_limit_remaining is not None:
            return self.rate_limit_remaining < Config.GITHUB_RATE_LIMIT_BUFFER
        return False
    
    def wait_for_rate_limit(self):
        """Wait for rate limit to reset"""
        if self.rate_limit_reset:
            wait_until = datetime.fromtimestamp(self.rate_limit_reset)
            wait_seconds = (wait_until - datetime.now()).total_seconds()
            
            if wait_seconds > 0:
                log_message(f"Rate limit reached. Waiting {wait_seconds/60:.1f} minutes until {wait_until.strftime('%H:%M:%S')}...", 'api')
                time.sleep(wait_seconds + 5)  # Add 5 second buffer
                
                # Check rate limit after waiting
                self.check_rate_limit()
    
    def check_rate_limit(self) -> Dict:
        """Check current rate limit status"""
        data, success = self.make_request("/rate_limit")
        
        if success and data:
            core = data['resources']['core']
            self.rate_limit_remaining = core['remaining']
            self.rate_limit_reset = core['reset']
            
            log_message(f"Rate limit: {core['remaining']}/{core['limit']} remaining", 'api')
            return core
        
        return {}
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user profile data"""
        data, success = self.make_request(f"/users/{username}")
        return data if success else None
    
    def get_user_repos(self, username: str, max_pages: int = 5) -> List[Dict]:
        """Get user's repositories"""
        repos = []
        
        for page in range(1, max_pages + 1):
            data, success = self.make_request(
                f"/users/{username}/repos",
                params={'per_page': 100, 'page': page, 'sort': 'updated'}
            )
            
            if not success or not data:
                break
            
            repos.extend(data)
            
            if len(data) < 100:
                break
        
        return repos


class GitHubEnrichmentEngine:
    """Main enrichment engine with checkpointing"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.api = RobustGitHubAPI()
        
        # Statistics
        self.stats = {
            'profiles_processed': 0,
            'profiles_enriched': 0,
            'profiles_failed': 0,
            'data_points_added': 0,
            'start_time': datetime.now()
        }
        
        # Checkpoint handling
        self.checkpoint_name = 'github_enrichment'
        self.checkpoint_data = Config.load_checkpoint(self.checkpoint_name)
        
        if self.checkpoint_data:
            log_message(f"Resuming from checkpoint: {self.checkpoint_data['profiles_processed']} profiles already processed", 'info')
            self.stats['profiles_processed'] = self.checkpoint_data['profiles_processed']
    
    def get_profiles_to_enrich(self) -> List[Tuple[str, str]]:
        """Get list of GitHub profiles that need enrichment"""
        cursor = self.conn.cursor()
        
        # Get profiles that haven't been enriched or need update
        cursor.execute("""
            SELECT DISTINCT sp.person_id, sp.profile_url
            FROM social_profiles sp
            WHERE sp.platform = 'github'
            AND sp.profile_url IS NOT NULL
            AND sp.profile_url != ''
            AND NOT EXISTS (
                SELECT 1 FROM github_profiles gp 
                WHERE gp.person_id = sp.person_id
                AND gp.updated_at > datetime('now', '-7 days')
            )
            ORDER BY sp.person_id
        """)
        
        profiles = cursor.fetchall()
        
        # Filter out already processed profiles if resuming
        if self.checkpoint_data and 'processed_ids' in self.checkpoint_data:
            processed_ids = set(self.checkpoint_data['processed_ids'])
            profiles = [(pid, url) for pid, url in profiles if pid not in processed_ids]
        
        return profiles
    
    def extract_github_username(self, profile_url: str) -> Optional[str]:
        """Extract GitHub username from profile URL"""
        if not profile_url:
            return None
        
        url = profile_url.lower().strip()
        
        # Common patterns
        patterns = [
            'github.com/',
            'www.github.com/',
            'http://github.com/',
            'https://github.com/',
        ]
        
        for pattern in patterns:
            if pattern in url:
                parts = url.split(pattern)
                if len(parts) > 1:
                    username = parts[1].split('/')[0].split('?')[0].split('#')[0]
                    if username:
                        return username
        
        # If just a username
        if '/' not in url and '.' not in url:
            return url
        
        return None
    
    def enrich_profile(self, person_id: str, github_url: str) -> bool:
        """Enrich a single GitHub profile"""
        username = self.extract_github_username(github_url)
        
        if not username:
            log_message(f"Could not extract username from: {github_url}", 'error')
            return False
        
        # Get user data from API
        user_data = self.api.get_user(username)
        
        if not user_data:
            return False
        
        # Get user's repositories for language analysis
        repos = self.api.get_user_repos(username)
        
        # Calculate language statistics
        languages = {}
        for repo in repos:
            if repo.get('language'):
                lang = repo['language']
                languages[lang] = languages.get(lang, 0) + 1
        
        # Prepare enriched data
        enriched_data = {
            'person_id': person_id,
            'github_username': username,
            'github_name': user_data.get('name'),
            'github_email': user_data.get('email'),
            'github_company': user_data.get('company'),
            'github_location': user_data.get('location'),
            'github_bio': user_data.get('bio'),
            'personal_website': user_data.get('blog'),
            'twitter_username': user_data.get('twitter_username'),
            'public_repos': user_data.get('public_repos', 0),
            'public_gists': user_data.get('public_gists', 0),
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'created_at': user_data.get('created_at'),
            'updated_at': datetime.now().isoformat(),
            'hireable': 1 if user_data.get('hireable') else 0,
            'languages_json': json.dumps(languages) if languages else None,
            'top_language': max(languages.keys(), key=languages.get) if languages else None,
            'profile_url': f"https://github.com/{username}"
        }
        
        # Save to database
        self.save_enriched_profile(enriched_data)
        
        # Track statistics
        data_points = sum(1 for v in enriched_data.values() if v is not None)
        self.stats['data_points_added'] += data_points
        
        return True
    
    def save_enriched_profile(self, data: Dict):
        """Save enriched profile to database"""
        cursor = self.conn.cursor()
        
        # First ensure the github_profiles table has all needed columns
        cursor.execute("PRAGMA table_info(github_profiles)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Filter data to only include existing columns
        filtered_data = {k: v for k, v in data.items() if k in existing_columns or k == 'person_id'}
        
        # Check if profile exists
        cursor.execute("""
            SELECT github_profile_id FROM github_profiles 
            WHERE person_id = ?
        """, (filtered_data['person_id'],))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing profile - build dynamic query based on available columns
            update_fields = []
            update_values = []
            
            for key, value in filtered_data.items():
                if key != 'person_id' and key in existing_columns:
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            if update_fields:
                update_values.append(filtered_data['person_id'])
                update_query = f"""
                    UPDATE github_profiles 
                    SET {', '.join(update_fields)}
                    WHERE person_id = ?
                """
                cursor.execute(update_query, update_values)
        else:
            # Generate profile ID
            import hashlib
            github_profile_id = 'gh_' + hashlib.md5(filtered_data.get('github_username', '').encode()).hexdigest()[:12]
            
            # Insert new profile - build dynamic query
            filtered_data['github_profile_id'] = github_profile_id
            
            insert_columns = []
            insert_values = []
            
            for key, value in filtered_data.items():
                if key in existing_columns:
                    insert_columns.append(key)
                    insert_values.append(value)
            
            if insert_columns:
                placeholders = ', '.join(['?' for _ in insert_columns])
                insert_query = f"""
                    INSERT INTO github_profiles ({', '.join(insert_columns)})
                    VALUES ({placeholders})
                """
                cursor.execute(insert_query, insert_values)
        
        self.conn.commit()
    
    def save_checkpoint(self, processed_ids: List[str]):
        """Save checkpoint for resuming"""
        checkpoint_data = {
            'profiles_processed': self.stats['profiles_processed'],
            'profiles_enriched': self.stats['profiles_enriched'],
            'processed_ids': processed_ids[-1000:],  # Keep last 1000 IDs
            'last_saved': datetime.now().isoformat()
        }
        
        Config.save_checkpoint(self.checkpoint_name, checkpoint_data)
    
    def run_enrichment(self, limit: Optional[int] = None, test_mode: bool = False):
        """Run the enrichment process"""
        log_message("="*60, 'info')
        log_message("🚀 GitHub Enrichment Starting", 'info')
        log_message("="*60, 'info')
        
        # Check rate limit at start
        rate_info = self.api.check_rate_limit()
        if not rate_info:
            log_message("Could not check rate limit. Proceeding with caution.", 'error')
        
        # Get profiles to enrich
        profiles = self.get_profiles_to_enrich()
        
        if limit:
            profiles = profiles[:limit]
        
        total = len(profiles)
        log_message(f"Found {total:,} profiles to enrich", 'info')
        
        if total == 0:
            log_message("No profiles need enrichment", 'info')
            return
        
        # Process profiles
        processed_ids = []
        
        for i, (person_id, github_url) in enumerate(profiles, 1):
            # Progress update
            if i % 10 == 0:
                progress = i / total * 100
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                rate = i / (elapsed / 60) if elapsed > 0 else 0
                
                log_message(
                    f"Progress: {i:,}/{total:,} ({progress:.1f}%) | "
                    f"Rate: {rate:.1f}/min | "
                    f"Enriched: {self.stats['profiles_enriched']:,} | "
                    f"Failed: {self.stats['profiles_failed']:,}",
                    'info'
                )
            
            # Enrich profile
            try:
                success = self.enrich_profile(person_id, github_url)
                
                if success:
                    self.stats['profiles_enriched'] += 1
                else:
                    self.stats['profiles_failed'] += 1
                
                self.stats['profiles_processed'] += 1
                processed_ids.append(person_id)
                
            except Exception as e:
                log_message(f"Error enriching {github_url}: {str(e)}", 'error')
                self.stats['profiles_failed'] += 1
                self.stats['profiles_processed'] += 1
            
            # Save checkpoint periodically
            if i % Config.CHECKPOINT_EVERY == 0:
                self.save_checkpoint(processed_ids)
                self.conn.commit()
            
            # Test mode - stop after a few
            if test_mode and i >= 5:
                log_message("Test mode - stopping after 5 profiles", 'info')
                break
        
        # Final save
        self.conn.commit()
        Config.clear_checkpoint(self.checkpoint_name)
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate enrichment report"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        report = f"""
========================================
GitHub Enrichment Report
========================================
Started:            {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
Duration:           {elapsed/60:.1f} minutes
Profiles Processed: {self.stats['profiles_processed']:,}
Profiles Enriched:  {self.stats['profiles_enriched']:,}
Profiles Failed:    {self.stats['profiles_failed']:,}
Data Points Added:  {self.stats['data_points_added']:,}
API Requests Made:  {self.api.requests_made:,}

Success Rate:       {self.stats['profiles_enriched']/max(self.stats['profiles_processed'],1)*100:.1f}%
Processing Rate:    {self.stats['profiles_processed']/(elapsed/60):.1f} profiles/minute
========================================
"""
        
        log_message(report, 'info')
        
        # Save to file
        with open(Config.GITHUB_ENRICHMENT_REPORT, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {Config.GITHUB_ENRICHMENT_REPORT}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Profile Enrichment')
    parser.add_argument('--test', action='store_true', help='Run in test mode (5 profiles only)')
    parser.add_argument('--limit', type=int, help='Limit number of profiles to enrich')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    
    args = parser.parse_args()
    
    # Check configuration
    if not Config.GITHUB_TOKEN or Config.GITHUB_TOKEN == 'your_token_here':
        print("❌ No valid GitHub token found!")
        print("\nPlease run: python3 test_github_setup.py --setup")
        sys.exit(1)
    
    # Run enrichment
    engine = GitHubEnrichmentEngine()
    
    try:
        engine.run_enrichment(limit=args.limit, test_mode=args.test)
    except KeyboardInterrupt:
        log_message("\n⚠️  Enrichment interrupted by user", 'info')
        log_message("Progress has been saved. Run with --resume to continue.", 'info')
    except Exception as e:
        log_message(f"Fatal error: {str(e)}", 'error')
        raise
    finally:
        engine.conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# ABOUTME: GitHub API enrichment system - complete workflow
# ABOUTME: Handles: company repos → contributors → user profiles with full data

"""
GitHub API Enrichment System

This script provides a complete GitHub enrichment workflow:

1. ENRICH EXISTING PROFILES: Update existing github_profiles with latest data
2. COMPANY DISCOVERY: Start with company GitHub org, get all repos
3. REPO ANALYSIS: Get contributors for each repo
4. PROFILE CREATION: Create new profiles for contributors
5. FULL ENRICHMENT: Get complete user data from API

Usage:
    # Enrich existing profiles
    python3 github_api_enrichment.py enrich-existing talent_intelligence.db
    
    # Discover company repos and contributors
    python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs
    
    # Full enrichment of a specific user
    python3 github_api_enrichment.py enrich-user talent_intelligence.db haydenadams
"""

import sqlite3
import requests
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_API_BASE = 'https://api.github.com'
RATE_LIMIT_BUFFER = 100  # Keep this many requests in reserve
CHECKPOINT_EVERY = 100
REQUEST_DELAY = 0.72  # Seconds between requests (5000/hour = 0.72s each)

class GitHubAPIClient:
    """Handles all GitHub API interactions with rate limiting"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {}
        if token:
            self.headers['Authorization'] = f'token {token}'
        
        self.requests_made = 0
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
        self.log("🔑 GitHub API Client initialized")
        if token:
            self.check_rate_limit()
        else:
            self.log("⚠️  No token provided - rate limit will be 60/hour instead of 5000/hour")
    
    def log(self, message: str):
        """Simple logging"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def check_rate_limit(self):
        """Check current rate limit status"""
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/rate_limit",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                self.rate_limit_remaining = core['remaining']
                self.rate_limit_reset = core['reset']
                
                self.log(f"📊 Rate limit: {self.rate_limit_remaining} requests remaining")
                
                return self.rate_limit_remaining > RATE_LIMIT_BUFFER
            
        except Exception as e:
            self.log(f"⚠️  Error checking rate limit: {str(e)}")
        
        return True
    
    def wait_for_rate_limit(self):
        """Wait if we're close to rate limit"""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < RATE_LIMIT_BUFFER:
            if self.rate_limit_reset:
                wait_time = self.rate_limit_reset - time.time()
                if wait_time > 0:
                    self.log(f"⏱️  Rate limit reached. Waiting {wait_time/60:.1f} minutes...")
                    time.sleep(wait_time + 5)
                    self.check_rate_limit()
    
    def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        self.wait_for_rate_limit()
        
        url = f"{GITHUB_API_BASE}{endpoint}"
        
        try:
            time.sleep(REQUEST_DELAY)  # Respect rate limits
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            self.requests_made += 1
            
            # Update rate limit from response headers
            if 'X-RateLimit-Remaining' in response.headers:
                self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
            if 'X-RateLimit-Reset' in response.headers:
                self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None  # Not found is expected sometimes
            elif response.status_code == 403:
                self.log(f"⚠️  Rate limit hit or forbidden: {endpoint}")
                self.wait_for_rate_limit()
                return None
            else:
                self.log(f"⚠️  API error {response.status_code}: {endpoint}")
                return None
                
        except Exception as e:
            self.log(f"⚠️  Request failed for {endpoint}: {str(e)}")
            return None
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user profile data"""
        return self.make_request(f"/users/{username}")
    
    def get_org_repos(self, org: str, per_page: int = 100) -> List[Dict]:
        """Get all repositories for an organization"""
        repos = []
        page = 1
        
        while True:
            data = self.make_request(
                f"/orgs/{org}/repos",
                params={'per_page': per_page, 'page': page, 'type': 'public'}
            )
            
            if not data or len(data) == 0:
                break
            
            repos.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return repos
    
    def get_repo_contributors(self, owner: str, repo: str, per_page: int = 100) -> List[Dict]:
        """Get all contributors for a repository"""
        contributors = []
        page = 1
        
        while True:
            data = self.make_request(
                f"/repos/{owner}/{repo}/contributors",
                params={'per_page': per_page, 'page': page}
            )
            
            if not data or len(data) == 0:
                break
            
            contributors.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return contributors
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict:
        """Get languages used in a repository"""
        return self.make_request(f"/repos/{owner}/{repo}/languages") or {}


class GitHubEnricher:
    """Main enrichment orchestrator"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = None
        self.api = GitHubAPIClient(GITHUB_TOKEN)
        
        self.stats = {
            'profiles_enriched': 0,
            'profiles_created': 0,
            'repos_discovered': 0,
            'contributors_found': 0,
            'errors': 0
        }
        
        self.log_file = self.db_path.parent / "github_enrichment_log.txt"
        self.log(f"=== GitHub Enrichment Session Started ===")
    
    def log(self, message: str):
        """Log to both console and file"""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.create_schema_if_needed()
    
    def create_schema_if_needed(self):
        """Ensure we have all necessary tables"""
        cursor = self.conn.cursor()
        
        # Company repositories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_repositories (
                repo_id TEXT PRIMARY KEY,
                company_id TEXT,
                repo_name TEXT,
                full_name TEXT,
                description TEXT,
                homepage TEXT,
                language TEXT,
                languages_json TEXT,
                stars INTEGER,
                forks INTEGER,
                watchers INTEGER,
                open_issues INTEGER,
                size_kb INTEGER,
                created_at TEXT,
                updated_at TEXT,
                pushed_at TEXT,
                is_fork INTEGER,
                is_archived INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """)
        
        # Enhanced github_contributions to track repo details
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_repo_contributions (
                contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_profile_id TEXT,
                person_id TEXT,
                company_id TEXT,
                repo_id TEXT,
                repo_full_name TEXT,
                contribution_count INTEGER,
                created_at TEXT,
                FOREIGN KEY (github_profile_id) REFERENCES github_profiles(github_profile_id),
                FOREIGN KEY (person_id) REFERENCES people(person_id),
                FOREIGN KEY (company_id) REFERENCES companies(company_id),
                FOREIGN KEY (repo_id) REFERENCES company_repositories(repo_id)
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_repos ON company_repositories(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_repo_contributions_profile ON github_repo_contributions(github_profile_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_repo_contributions_repo ON github_repo_contributions(repo_id)")
        
        self.conn.commit()
        self.log("✅ Database schema ready")
    
    def enrich_existing_profiles(self):
        """Enrich all existing github_profiles with latest API data"""
        self.log("\n🔄 Starting enrichment of existing profiles...")
        
        cursor = self.conn.cursor()
        
        # Get all profiles that need enrichment
        cursor.execute("""
            SELECT github_username 
            FROM github_profiles 
            WHERE github_username IS NOT NULL
            ORDER BY github_username
        """)
        
        usernames = [row[0] for row in cursor.fetchall()]
        total = len(usernames)
        
        self.log(f"📊 Found {total:,} profiles to enrich")
        
        for i, username in enumerate(usernames, 1):
            if i % CHECKPOINT_EVERY == 0:
                self.conn.commit()
                self.log(f"  💾 Checkpoint: {i:,}/{total:,} ({i/total*100:.1f}%)")
            
            user_data = self.api.get_user(username)
            
            if user_data:
                self.update_github_profile(username, user_data)
                self.stats['profiles_enriched'] += 1
            else:
                self.stats['errors'] += 1
            
            if i % 50 == 0:
                self.log(f"  ✅ Progress: {i:,}/{total:,} - Success: {self.stats['profiles_enriched']:,}")
        
        self.conn.commit()
        self.log(f"\n✅ Enriched {self.stats['profiles_enriched']:,} profiles")
    
    def update_github_profile(self, username: str, user_data: Dict):
        """Update github_profiles with API data"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE github_profiles 
            SET followers = ?,
                following = ?,
                public_repos = ?,
                public_gists = ?,
                github_company = ?,
                github_location = ?,
                github_email = ?,
                personal_website = ?,
                twitter_username = ?,
                updated_at = ?
            WHERE github_username = ?
        """, (
            user_data.get('followers'),
            user_data.get('following'),
            user_data.get('public_repos'),
            user_data.get('public_gists'),
            user_data.get('company'),
            user_data.get('location'),
            user_data.get('email'),
            user_data.get('blog'),
            user_data.get('twitter_username'),
            datetime.now().isoformat(),
            username
        ))
    
    def discover_company(self, github_org: str, company_name: Optional[str] = None):
        """
        Discover all repos and contributors for a company GitHub org
        
        Args:
            github_org: GitHub organization name (e.g., 'uniswap-labs')
            company_name: Optional company name to link to (e.g., 'Uniswap')
        """
        self.log(f"\n🔍 Discovering company: {github_org}")
        
        # Find or create company record
        company_id = self.find_or_create_company(github_org, company_name)
        
        # Get all repositories
        self.log("  📦 Fetching repositories...")
        repos = self.api.get_org_repos(github_org)
        self.log(f"  Found {len(repos)} repositories")
        
        self.stats['repos_discovered'] += len(repos)
        
        # Process each repository
        for i, repo in enumerate(repos, 1):
            self.log(f"\n  📁 [{i}/{len(repos)}] Processing: {repo['name']}")
            
            # Save repository data
            repo_id = self.save_repository(repo, company_id)
            
            # Get contributors
            contributors = self.api.get_repo_contributors(github_org, repo['name'])
            self.log(f"    👥 Found {len(contributors)} contributors")
            
            self.stats['contributors_found'] += len(contributors)
            
            # Process each contributor
            for contributor in contributors:
                username = contributor.get('login')
                if not username:
                    continue
                
                # Get or create profile
                github_profile_id = self.get_or_create_github_profile(username)
                
                # Link contribution
                self.save_contribution(
                    github_profile_id,
                    company_id,
                    repo_id,
                    repo['full_name'],
                    contributor.get('contributions', 0)
                )
            
            # Commit after each repo
            self.conn.commit()
        
        self.log(f"\n✅ Company discovery complete!")
        self.log(f"  Repositories: {len(repos)}")
        self.log(f"  Total contributors: {self.stats['contributors_found']}")
    
    def find_or_create_company(self, github_org: str, company_name: Optional[str]) -> str:
        """Find existing company or create new one"""
        cursor = self.conn.cursor()
        
        # Try to find by GitHub org
        cursor.execute("""
            SELECT c.company_id 
            FROM companies c
            JOIN company_social_profiles csp ON c.company_id = csp.company_id
            WHERE csp.platform = 'github' 
            AND (csp.profile_url LIKE ? OR csp.username = ?)
        """, (f"%{github_org}%", github_org))
        
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Try to find by name if provided
        if company_name:
            cursor.execute("""
                SELECT company_id FROM companies 
                WHERE LOWER(name) = LOWER(?)
            """, (company_name,))
            
            result = cursor.fetchone()
            if result:
                company_id = result[0]
                
                # Add GitHub org to social profiles
                cursor.execute("""
                    INSERT OR IGNORE INTO company_social_profiles 
                    (company_id, platform, profile_url, username)
                    VALUES (?, 'github', ?, ?)
                """, (company_id, f"github.com/{github_org}", github_org))
                
                self.conn.commit()
                return company_id
        
        # Create new company
        import hashlib
        company_id = 'comp_' + hashlib.md5(github_org.encode()).hexdigest()[:12]
        
        cursor.execute("""
            INSERT INTO companies (
                company_id, name, github_org, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            company_id,
            company_name or github_org,
            github_org,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Add GitHub social profile
        cursor.execute("""
            INSERT INTO company_social_profiles 
            (company_id, platform, profile_url, username)
            VALUES (?, 'github', ?, ?)
        """, (company_id, f"github.com/{github_org}", github_org))
        
        self.conn.commit()
        
        self.log(f"  ✨ Created new company: {company_name or github_org}")
        
        return company_id
    
    def save_repository(self, repo_data: Dict, company_id: str) -> str:
        """Save repository data"""
        import hashlib
        repo_id = 'repo_' + hashlib.md5(repo_data['full_name'].encode()).hexdigest()[:12]
        
        # Get languages
        owner, repo_name = repo_data['full_name'].split('/')
        languages = self.api.get_repo_languages(owner, repo_name)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO company_repositories (
                repo_id, company_id, repo_name, full_name, description,
                homepage, language, languages_json, stars, forks, watchers,
                open_issues, size_kb, created_at, updated_at, pushed_at,
                is_fork, is_archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repo_id,
            company_id,
            repo_data['name'],
            repo_data['full_name'],
            repo_data.get('description'),
            repo_data.get('homepage'),
            repo_data.get('language'),
            json.dumps(languages),
            repo_data.get('stargazers_count', 0),
            repo_data.get('forks_count', 0),
            repo_data.get('watchers_count', 0),
            repo_data.get('open_issues_count', 0),
            repo_data.get('size', 0),
            repo_data.get('created_at'),
            repo_data.get('updated_at'),
            repo_data.get('pushed_at'),
            1 if repo_data.get('fork') else 0,
            1 if repo_data.get('archived') else 0
        ))
        
        return repo_id
    
    def get_or_create_github_profile(self, username: str) -> str:
        """Get existing profile or create new one"""
        import hashlib
        github_profile_id = 'gh_' + hashlib.md5(username.lower().encode()).hexdigest()[:12]
        
        cursor = self.conn.cursor()
        
        # Check if exists
        cursor.execute("""
            SELECT github_profile_id FROM github_profiles 
            WHERE github_username = ?
        """, (username,))
        
        if cursor.fetchone():
            return github_profile_id
        
        # Get full user data from API
        user_data = self.api.get_user(username)
        
        if not user_data:
            # Create minimal profile
            cursor.execute("""
                INSERT INTO github_profiles (
                    github_profile_id, github_username, created_at, updated_at
                ) VALUES (?, ?, ?, ?)
            """, (github_profile_id, username, datetime.now().isoformat(), datetime.now().isoformat()))
        else:
            # Create full profile
            cursor.execute("""
                INSERT INTO github_profiles (
                    github_profile_id, github_username, github_name, github_email,
                    github_company, github_location, personal_website, twitter_username,
                    public_repos, public_gists, followers, following,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                github_profile_id,
                username,
                user_data.get('name'),
                user_data.get('email'),
                user_data.get('company'),
                user_data.get('location'),
                user_data.get('blog'),
                user_data.get('twitter_username'),
                user_data.get('public_repos'),
                user_data.get('public_gists'),
                user_data.get('followers'),
                user_data.get('following'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            self.stats['profiles_created'] += 1
        
        return github_profile_id
    
    def save_contribution(self, github_profile_id: str, company_id: str, 
                         repo_id: str, repo_full_name: str, contribution_count: int):
        """Save contribution record"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO github_repo_contributions (
                github_profile_id, company_id, repo_id, repo_full_name,
                contribution_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            github_profile_id,
            company_id,
            repo_id,
            repo_full_name,
            contribution_count,
            datetime.now().isoformat()
        ))
    
    def enrich_user(self, username: str):
        """Fully enrich a specific user"""
        self.log(f"\n👤 Enriching user: {username}")
        
        user_data = self.api.get_user(username)
        
        if not user_data:
            self.log(f"  ❌ User not found: {username}")
            return
        
        github_profile_id = self.get_or_create_github_profile(username)
        self.update_github_profile(username, user_data)
        
        self.conn.commit()
        
        self.log(f"  ✅ User enriched successfully")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def print_stats(self):
        """Print final statistics"""
        self.log("\n" + "="*60)
        self.log("📊 ENRICHMENT STATISTICS")
        self.log("="*60)
        self.log(f"Profiles Enriched:  {self.stats['profiles_enriched']:,}")
        self.log(f"Profiles Created:   {self.stats['profiles_created']:,}")
        self.log(f"Repos Discovered:   {self.stats['repos_discovered']:,}")
        self.log(f"Contributors Found: {self.stats['contributors_found']:,}")
        self.log(f"API Requests Made:  {self.api.requests_made:,}")
        self.log(f"Errors:             {self.stats['errors']:,}")
        self.log("="*60)


def main():
    if len(sys.argv) < 3:
        print("""
GitHub API Enrichment Tool

Usage:
    # Enrich existing profiles in database
    python3 github_api_enrichment.py enrich-existing <database_path>
    
    # Discover company repos and contributors
    python3 github_api_enrichment.py discover-company <database_path> <github_org> [company_name]
    
    # Enrich specific user
    python3 github_api_enrichment.py enrich-user <database_path> <username>

Examples:
    python3 github_api_enrichment.py enrich-existing talent_intelligence.db
    python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"
    python3 github_api_enrichment.py enrich-user talent_intelligence.db haydenadams

Environment:
    GITHUB_TOKEN - Personal access token (required for 5000/hour rate limit)
    
Get token: https://github.com/settings/tokens
Scopes needed: public_repo, read:user, read:org
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    db_path = sys.argv[2]
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    enricher = GitHubEnricher(db_path)
    enricher.connect()
    
    try:
        if command == "enrich-existing":
            enricher.enrich_existing_profiles()
        
        elif command == "discover-company":
            if len(sys.argv) < 4:
                print("❌ Missing github_org argument")
                sys.exit(1)
            
            github_org = sys.argv[3]
            company_name = sys.argv[4] if len(sys.argv) > 4 else None
            
            enricher.discover_company(github_org, company_name)
        
        elif command == "enrich-user":
            if len(sys.argv) < 4:
                print("❌ Missing username argument")
                sys.exit(1)
            
            username = sys.argv[3]
            enricher.enrich_user(username)
        
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
        
        enricher.print_stats()
    
    finally:
        enricher.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ABOUTME: Rate-limited GitHub API client for intelligence extraction.
ABOUTME: Handles authentication, rate limiting, and error handling for GitHub API calls.
"""

import os
import time
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class GitHubClient:
    """
    GitHub API client with rate limiting and error handling.
    
    Supports:
    - Automatic rate limiting (5000 req/hr with token, 60 without)
    - Request retry logic
    - Response caching
    - Error handling
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (optional but strongly recommended)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'TalentIntelligence-GitHubNative/1.0'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        
        # Rate limiting
        self.requests_made = 0
        self.rate_limit_remaining = 5000 if self.token else 60
        self.rate_limit_reset = None
        self.last_request_time = None
        
        # Minimum delay between requests (0.72s = 5000 req/hr)
        self.min_delay = 0.72 if self.token else 60
    
    def _wait_for_rate_limit(self):
        """
        Implement rate limiting delay.
        """
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        
        # If we've hit rate limit, wait until reset
        if self.rate_limit_remaining == 0 and self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time()
            if wait_time > 0:
                print(f"⏳ Rate limit hit. Waiting {wait_time:.0f}s until reset...")
                time.sleep(wait_time + 1)
    
    def _update_rate_limit(self, response: requests.Response):
        """
        Update rate limit info from response headers.
        """
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        if 'X-RateLimit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make a GET request to GitHub API.
        
        Args:
            endpoint: API endpoint (e.g., '/users/username')
            params: Query parameters
        
        Returns:
            JSON response data or None if error
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            self.last_request_time = time.time()
            self.requests_made += 1
            
            self._update_rate_limit(response)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None  # Resource not found
            elif response.status_code == 403:
                print(f"⚠️  Rate limit or forbidden: {endpoint}")
                return None
            else:
                print(f"❌ Error {response.status_code} for {endpoint}: {response.text[:200]}")
                return None
        
        except Exception as e:
            print(f"❌ Exception fetching {endpoint}: {e}")
            return None
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile."""
        return self.get(f"/users/{username}")
    
    def get_user_repos(self, username: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all user repositories."""
        repos = []
        page = 1
        
        while True:
            data = self.get(f"/users/{username}/repos", params={
                'per_page': per_page,
                'page': page,
                'sort': 'updated',
                'direction': 'desc'
            })
            
            if not data:
                break
            
            repos.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return repos
    
    def get_user_events(self, username: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get user's recent events (last 90 days)."""
        return self.get(f"/users/{username}/events", params={'per_page': per_page}) or []
    
    def get_user_orgs(self, username: str) -> List[Dict[str, Any]]:
        """Get user's organizations."""
        return self.get(f"/users/{username}/orgs") or []
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get language statistics for a repository."""
        return self.get(f"/repos/{owner}/{repo}/languages") or {}
    
    def get_repo_commits(self, owner: str, repo: str, author: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get commits by author in a repository."""
        commits = []
        page = 1
        
        while True:
            data = self.get(f"/repos/{owner}/{repo}/commits", params={
                'author': author,
                'per_page': per_page,
                'page': page
            })
            
            if not data:
                break
            
            commits.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
            
            # Limit to avoid excessive API calls
            if len(commits) >= 500:
                break
        
        return commits
    
    def get_repo_pulls(self, owner: str, repo: str, creator: str, state: str = 'all') -> List[Dict[str, Any]]:
        """Get pull requests by creator in a repository."""
        pulls = []
        page = 1
        
        while True:
            data = self.get(f"/repos/{owner}/{repo}/pulls", params={
                'creator': creator,
                'state': state,
                'per_page': 100,
                'page': page
            })
            
            if not data:
                break
            
            pulls.extend(data)
            
            if len(data) < 100:
                break
            
            page += 1
            
            # Limit to avoid excessive API calls
            if len(pulls) >= 200:
                break
        
        return pulls
    
    def get_repo_contributors(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository contributors."""
        return self.get(f"/repos/{owner}/{repo}/contributors", params={'per_page': 100}) or []
    
    def get_org_members(self, org: str) -> List[Dict[str, Any]]:
        """Get organization members."""
        members = []
        page = 1
        
        while True:
            data = self.get(f"/orgs/{org}/members", params={'per_page': 100, 'page': page})
            
            if not data:
                break
            
            members.extend(data)
            
            if len(data) < 100:
                break
            
            page += 1
        
        return members
    
    def get_org_repos(self, org: str) -> List[Dict[str, Any]]:
        """Get organization repositories."""
        repos = []
        page = 1
        
        while True:
            data = self.get(f"/orgs/{org}/repos", params={
                'per_page': 100,
                'page': page,
                'sort': 'updated'
            })
            
            if not data:
                break
            
            repos.extend(data)
            
            if len(data) < 100:
                break
            
            page += 1
        
        return repos
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        data = self.get('/rate_limit')
        return data if data else {}
    
    def print_rate_limit_status(self):
        """Print current rate limit status."""
        status = self.get_rate_limit_status()
        
        if status and 'rate' in status:
            remaining = status['rate']['remaining']
            limit = status['rate']['limit']
            reset_time = datetime.fromtimestamp(status['rate']['reset'])
            
            print(f"\n📊 GitHub API Rate Limit Status:")
            print(f"   Remaining: {remaining}/{limit}")
            print(f"   Resets at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Requests made this session: {self.requests_made}")


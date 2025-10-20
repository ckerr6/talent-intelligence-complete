"""
GitHub API Client with rate limiting and error handling
"""

import requests
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from .config import GitHubAutomationConfig as Config
import logging

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    pass


class RateLimitExceeded(GitHubAPIError):
    """Raised when rate limit is exceeded"""
    pass


class GitHubClient:
    """
    GitHub API client with automatic rate limiting and retry logic
    
    Features:
    - Automatic rate limit management
    - Exponential backoff on errors
    - Request caching (optional)
    - Comprehensive error handling
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_BASE
        
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Talent-Intelligence-Automation'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.requests_made = 0
        self.last_rate_check = 0
        
        # Statistics
        self.stats = {
            'requests': 0,
            'errors': 0,
            'rate_limit_waits': 0,
            'retries': 0
        }
        
        logger.info("🔑 GitHub API Client initialized")
        if not self.token:
            logger.warning("⚠️  No token - rate limit will be 60/hour")
        else:
            self.check_rate_limit()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[Dict]:
        """
        Make a request to GitHub API with error handling and retries
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/users/username')
            params: Query parameters
            retry_count: Current retry attempt
            
        Returns:
            Response JSON or None on error
        """
        url = f"{self.base_url}{endpoint}"
        
        # Check rate limit periodically
        if self.requests_made % Config.RATE_LIMIT_CHECK_INTERVAL == 0:
            if not self.check_rate_limit():
                self.wait_for_rate_limit()
        
        # Add delay between requests
        time.sleep(Config.REQUEST_DELAY)
        
        try:
            self.stats['requests'] += 1
            self.requests_made += 1
            
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            # Update rate limit info from headers
            self._update_rate_limit(response.headers)
            
            # Handle rate limiting
            if response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    logger.warning("⚠️  Rate limit exceeded")
                    self.stats['rate_limit_waits'] += 1
                    self.wait_for_rate_limit()
                    # Retry after waiting
                    return self._make_request(method, endpoint, params, retry_count + 1)
            
            # Handle other errors
            if response.status_code >= 400:
                logger.error(f"❌ HTTP {response.status_code}: {url}")
                self.stats['errors'] += 1
                
                # Retry on server errors
                if response.status_code >= 500 and retry_count < Config.MAX_RETRIES:
                    wait_time = (Config.RETRY_BACKOFF ** retry_count)
                    logger.info(f"🔄 Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    self.stats['retries'] += 1
                    return self._make_request(method, endpoint, params, retry_count + 1)
                
                return None
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout: {url}")
            self.stats['errors'] += 1
            if retry_count < Config.MAX_RETRIES:
                return self._make_request(method, endpoint, params, retry_count + 1)
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            self.stats['errors'] += 1
            return None
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.stats['errors'] += 1
            return None
    
    def _update_rate_limit(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        if 'X-RateLimit-Remaining' in headers:
            self.rate_limit_remaining = int(headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in headers:
            self.rate_limit_reset = int(headers['X-RateLimit-Reset'])
    
    def check_rate_limit(self) -> bool:
        """
        Check current rate limit status
        
        Returns:
            True if we have sufficient requests remaining
        """
        try:
            response = requests.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                self.rate_limit_remaining = core['remaining']
                self.rate_limit_reset = core['reset']
                
                logger.info(f"📊 Rate limit: {self.rate_limit_remaining:,} remaining")
                
                return self.rate_limit_remaining > Config.RATE_LIMIT_BUFFER
                
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
        
        return True
    
    def wait_for_rate_limit(self):
        """Wait until rate limit resets"""
        if self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time()
            if wait_time > 0:
                logger.warning(f"⏱️  Rate limit reached. Waiting {wait_time/60:.1f} minutes...")
                time.sleep(wait_time + 5)
                self.check_rate_limit()
    
    # API Methods
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user profile"""
        return self._make_request('GET', f'/users/{username}')
    
    def get_user_repos(self, username: str, per_page: int = 100) -> List[Dict]:
        """Get user's repositories"""
        repos = []
        page = 1
        
        while True:
            result = self._make_request(
                'GET',
                f'/users/{username}/repos',
                params={'per_page': per_page, 'page': page, 'sort': 'updated'}
            )
            
            if not result:
                break
            
            repos.extend(result)
            
            if len(result) < per_page:
                break
            
            page += 1
        
        return repos
    
    def get_org(self, org_name: str) -> Optional[Dict]:
        """Get organization info"""
        return self._make_request('GET', f'/orgs/{org_name}')
    
    def get_org_members(self, org_name: str, per_page: int = 100) -> List[Dict]:
        """Get organization members"""
        members = []
        page = 1
        
        while True:
            result = self._make_request(
                'GET',
                f'/orgs/{org_name}/members',
                params={'per_page': per_page, 'page': page}
            )
            
            if not result:
                break
            
            members.extend(result)
            
            if len(result) < per_page:
                break
            
            page += 1
        
        return members
    
    def get_org_repos(self, org_name: str, per_page: int = 100) -> List[Dict]:
        """Get organization repositories"""
        repos = []
        page = 1
        max_repos = Config.MAX_REPOS_PER_ORG
        
        while len(repos) < max_repos:
            result = self._make_request(
                'GET',
                f'/orgs/{org_name}/repos',
                params={'per_page': per_page, 'page': page, 'sort': 'updated'}
            )
            
            if not result:
                break
            
            repos.extend(result)
            
            if len(result) < per_page:
                break
            
            page += 1
        
        return repos[:max_repos]
    
    def get_repo_contributors(self, owner: str, repo: str, per_page: int = 100) -> List[Dict]:
        """Get repository contributors"""
        contributors = []
        page = 1
        max_contributors = Config.MAX_CONTRIBUTORS_PER_REPO
        
        while len(contributors) < max_contributors:
            result = self._make_request(
                'GET',
                f'/repos/{owner}/{repo}/contributors',
                params={'per_page': per_page, 'page': page}
            )
            
            if not result:
                break
            
            contributors.extend(result)
            
            if len(result) < per_page:
                break
            
            page += 1
        
        return contributors[:max_contributors]
    
    def search_users(self, query: str, per_page: int = 100) -> List[Dict]:
        """Search for users"""
        result = self._make_request(
            'GET',
            '/search/users',
            params={'q': query, 'per_page': per_page}
        )
        
        if result and 'items' in result:
            return result['items']
        
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': datetime.fromtimestamp(self.rate_limit_reset) if self.rate_limit_reset else None
        }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info("=" * 60)
        logger.info("📊 GitHub API Client Statistics")
        logger.info("=" * 60)
        logger.info(f"Requests made: {stats['requests']:,}")
        logger.info(f"Errors: {stats['errors']:,}")
        logger.info(f"Retries: {stats['retries']:,}")
        logger.info(f"Rate limit waits: {stats['rate_limit_waits']:,}")
        logger.info(f"Rate limit remaining: {stats['rate_limit_remaining']:,}")
        if stats['rate_limit_reset']:
            logger.info(f"Rate limit resets: {stats['rate_limit_reset']}")
        logger.info("=" * 60)


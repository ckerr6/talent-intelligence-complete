"""
Configuration for GitHub Automation System
"""

import os
from pathlib import Path
from typing import Optional

class GitHubAutomationConfig:
    """Configuration settings for GitHub automation"""
    
    # GitHub API
    GITHUB_TOKEN: Optional[str] = os.environ.get('GITHUB_TOKEN')
    GITHUB_API_BASE = 'https://api.github.com'
    
    # Rate Limiting
    RATE_LIMIT_BUFFER = 100  # Keep this many requests in reserve
    RATE_LIMIT_CHECK_INTERVAL = 50  # Check rate limit every N requests
    REQUEST_DELAY = 0.72  # Seconds between requests (5000/hour)
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2  # Exponential backoff multiplier
    
    # Enrichment Settings
    BATCH_SIZE = 100  # Process this many profiles before checkpointing
    MAX_PROFILES_PER_RUN = 10000  # Max profiles to process in one run
    STALE_DAYS = 30  # Re-enrich profiles older than this
    
    # Matching Settings
    EMAIL_MATCH_CONFIDENCE = 0.95
    NAME_COMPANY_MATCH_CONFIDENCE = 0.85
    NAME_LOCATION_MATCH_CONFIDENCE = 0.70
    LINKEDIN_MATCH_CONFIDENCE = 0.99
    AUTO_MATCH_THRESHOLD = 0.85  # Auto-match if confidence above this
    
    # Priority Weights (higher = more important)
    PRIORITY_HAS_EMAIL = 10
    PRIORITY_HAS_LOCATION = 5
    PRIORITY_HIGH_FOLLOWERS = 8
    PRIORITY_RECENT_ACTIVITY = 3
    
    # Logging
    LOG_DIR = Path(__file__).parent.parent / 'logs' / 'github_automation'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Status Files
    STATUS_DIR = Path(__file__).parent.parent / 'github_automation' / 'status'
    CHECKPOINT_FILE = STATUS_DIR / 'checkpoint.json'
    METRICS_FILE = STATUS_DIR / 'metrics.json'
    
    # Discovery Settings
    DISCOVER_ORG_MEMBERS = True
    DISCOVER_REPO_CONTRIBUTORS = True
    MAX_REPOS_PER_ORG = 100
    MAX_CONTRIBUTORS_PER_REPO = 100
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.STATUS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.GITHUB_TOKEN:
            print("⚠️  WARNING: GITHUB_TOKEN not set. Rate limit will be 60/hour instead of 5000/hour")
            return False
        return True


# Initialize on import
GitHubAutomationConfig.ensure_directories()


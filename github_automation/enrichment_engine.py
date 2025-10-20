"""
Enrichment Engine for GitHub Profiles

Enriches GitHub profiles with data from GitHub API
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from typing import Dict, Optional, List
from datetime import datetime
from config import Config, get_db_connection
from .github_client import GitHubClient
from .config import GitHubAutomationConfig as AutoConfig
import logging
import json

logger = logging.getLogger(__name__)


class EnrichmentEngine:
    """
    Core enrichment engine
    
    Enriches GitHub profiles by:
    1. Fetching user data from GitHub API
    2. Extracting relevant fields
    3. Updating database
    4. Logging results
    """
    
    def __init__(self, github_client: Optional[GitHubClient] = None):
        self.client = github_client or GitHubClient()
        self.conn = get_db_connection(use_pool=False)
        
        self.stats = {
            'enriched': 0,
            'failed': 0,
            'skipped': 0,
            'api_calls': 0
        }
    
    def enrich_profile(self, profile: Dict) -> bool:
        """
        Enrich a single GitHub profile
        
        Args:
            profile: Profile dict with at least github_username
            
        Returns:
            True if successful, False otherwise
        """
        username = profile.get('github_username')
        if not username:
            logger.error("Profile missing username")
            self.stats['skipped'] += 1
            return False
        
        try:
            # Get user data from GitHub API
            user_data = self.client.get_user(username)
            self.stats['api_calls'] += 1
            
            if not user_data:
                logger.warning(f"⚠️  No data for {username}")
                self.stats['failed'] += 1
                return False
            
            # Extract and normalize data
            enriched_data = self._extract_user_data(user_data)
            
            # Get user's top repositories for language analysis
            repos = self.client.get_user_repos(username, per_page=100)
            self.stats['api_calls'] += 1
            
            if repos:
                enriched_data['top_languages'] = self._analyze_languages(repos)
                enriched_data['public_repos'] = len(repos)
                enriched_data['top_repos'] = [
                    {
                        'name': r['name'],
                        'stars': r['stargazers_count'],
                        'language': r['language']
                    }
                    for r in sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)[:5]
                ]
            
            # Update database
            success = self._update_profile(profile['github_profile_id'], enriched_data)
            
            if success:
                self.stats['enriched'] += 1
                logger.info(f"✅ Enriched {username}")
            else:
                self.stats['failed'] += 1
                logger.error(f"❌ Failed to update {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error enriching {username}: {e}")
            self.stats['failed'] += 1
            return False
    
    def _extract_user_data(self, user_data: Dict) -> Dict:
        """
        Extract relevant fields from GitHub user API response
        
        Args:
            user_data: Raw GitHub API response
            
        Returns:
            Dict of normalized data ready for database
        """
        # Extract LinkedIn from bio if present
        linkedin_url = None
        bio = user_data.get('bio', '')
        if bio:
            # Look for LinkedIn URL patterns
            import re
            linkedin_patterns = [
                r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
                r'linkedin\.com/company/([a-zA-Z0-9_-]+)'
            ]
            for pattern in linkedin_patterns:
                match = re.search(pattern, bio)
                if match:
                    linkedin_url = f"https://www.linkedin.com/in/{match.group(1)}"
                    break
        
        return {
            'github_name': user_data.get('name'),
            'github_email': user_data.get('email'),
            'github_company': user_data.get('company'),
            'bio': user_data.get('bio'),
            'blog': user_data.get('blog'),
            'location': user_data.get('location'),
            'twitter_username': user_data.get('twitter_username'),
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'public_repos': user_data.get('public_repos', 0),
            'hireable': user_data.get('hireable'),
            'avatar_url': user_data.get('avatar_url'),
            'created_at_github': user_data.get('created_at'),
            'updated_at_github': user_data.get('updated_at'),
            'linkedin_url': linkedin_url  # Extracted from bio
        }
    
    def _analyze_languages(self, repos: List[Dict]) -> Dict[str, int]:
        """
        Analyze languages used across repositories
        
        Args:
            repos: List of repository dicts
            
        Returns:
            Dict of language: repo_count
        """
        languages = {}
        
        for repo in repos:
            lang = repo.get('language')
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        # Sort by count
        return dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))
    
    def _update_profile(self, profile_id: str, data: Dict) -> bool:
        """
        Update database with enriched data
        
        Args:
            profile_id: GitHub profile UUID
            data: Enriched data dict
            
        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        
        try:
            # Convert dict fields to JSON
            top_repos_json = json.dumps(data.pop('top_repos', []))
            top_languages_json = json.dumps(data.pop('top_languages', {}))
            linkedin_url = data.pop('linkedin_url', None)
            
            # Build update query
            set_clauses = []
            values = []
            
            for key, value in data.items():
                if value is not None:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            # Always update these fields
            set_clauses.append("last_enriched = NOW()")
            set_clauses.append("updated_at = NOW()")
            
            # Add JSON fields if we have data
            if top_repos_json != '[]':
                # Store in a note or separate table if needed
                pass  # For now, we don't have a field for this
            
            values.append(profile_id)
            
            query = f"""
                UPDATE github_profile
                SET {', '.join(set_clauses)}
                WHERE github_profile_id = %s
            """
            
            cursor.execute(query, values)
            self.conn.commit()
            
            # If we found LinkedIn, also store that for matching
            if linkedin_url:
                # This helps with matching later
                logger.info(f"  📎 Found LinkedIn: {linkedin_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Database update error: {e}")
            self.conn.rollback()
            return False
    
    def enrich_batch(self, profiles: List[Dict]) -> Dict[str, int]:
        """
        Enrich a batch of profiles
        
        Args:
            profiles: List of profile dicts
            
        Returns:
            Dict with counts of success/failure
        """
        logger.info(f"🔄 Enriching batch of {len(profiles)} profiles...")
        
        batch_stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for i, profile in enumerate(profiles, 1):
            username = profile.get('github_username', 'unknown')
            logger.info(f"  [{i}/{len(profiles)}] {username}")
            
            success = self.enrich_profile(profile)
            
            if success:
                batch_stats['success'] += 1
            else:
                batch_stats['failed'] += 1
            
            # Log progress every 10 profiles
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(profiles)} ({i/len(profiles)*100:.1f}%)")
        
        logger.info(f"✅ Batch complete: {batch_stats['success']} success, {batch_stats['failed']} failed")
        
        return batch_stats
    
    def get_stats(self) -> Dict:
        """Get enrichment statistics"""
        return {
            **self.stats,
            'api_stats': self.client.get_stats()
        }
    
    def log_stats(self):
        """Log enrichment statistics"""
        stats = self.get_stats()
        
        logger.info("=" * 60)
        logger.info("📊 Enrichment Statistics")
        logger.info("=" * 60)
        logger.info(f"Profiles enriched: {stats['enriched']:,}")
        logger.info(f"Failed: {stats['failed']:,}")
        logger.info(f"Skipped: {stats['skipped']:,}")
        logger.info(f"API calls made: {stats['api_calls']:,}")
        logger.info("=" * 60)
        
        # Log API client stats
        self.client.log_stats()
    
    def close(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()


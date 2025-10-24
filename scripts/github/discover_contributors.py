#!/usr/bin/env python3
"""
Contributor Discovery Engine

Discovers and enriches contributors to priority repositories.

Features:
- Discovers contributors from GitHub API
- Enriches GitHub profiles with full metadata
- Tags contributors with ecosystem tags
- Assigns importance scores
- Special handling for EIP authors and Paradigm ecosystem
- Records discovery lineage

Usage:
    python3 scripts/github/discover_contributors.py --priority-tier 1
    python3 scripts/github/discover_contributors.py --repos ethereum/EIPs paradigmxyz/reth
    python3 scripts/github/discover_contributors.py --limit 10
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from uuid import UUID
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config, get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GitHub API setup
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API = 'https://api.github.com'
HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'TalentIntelligence-Discovery/1.0'
}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'


class ContributorDiscovery:
    """Discover and enrich contributors to repositories"""
    
    def __init__(self, conn=None, dry_run=False):
        self.conn = conn or get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        self.dry_run = dry_run
        
        self.stats = {
            'repos_processed': 0,
            'contributors_discovered': 0,
            'contributors_enriched': 0,
            'contributors_skipped': 0,
            'eip_authors_found': 0,
            'api_calls': 0,
            'start_time': time.time()
        }
        
        # Cache
        self.profile_cache = {}  # username -> github_profile_id
        self.repo_cache = {}  # full_name -> repo data
        self.ecosystem_cache = {}  # ecosystem_id -> metadata
        
        logger.info(f"🚀 Contributor Discovery initialized (dry_run={dry_run})")
        
        if not GITHUB_TOKEN:
            logger.warning("⚠️  No GITHUB_TOKEN set - API rate limits will be very low")
        else:
            logger.info("✓ GitHub token configured")
    
    def load_caches(self):
        """Load existing data into cache"""
        logger.info("Loading caches...")
        
        # Load existing GitHub profiles
        self.cursor.execute("""
            SELECT github_profile_id, github_username
            FROM github_profile
            WHERE github_username IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.profile_cache[row['github_username'].lower()] = row['github_profile_id']
        
        logger.info(f"  Loaded {len(self.profile_cache)} GitHub profiles")
        
        # Load repos
        self.cursor.execute("""
            SELECT repo_id, full_name, ecosystem_ids, owner_username
            FROM github_repository
        """)
        for row in self.cursor.fetchall():
            self.repo_cache[row['full_name'].lower()] = {
                'repo_id': row['repo_id'],
                'full_name': row['full_name'],
                'ecosystem_ids': row['ecosystem_ids'] or [],
                'owner_username': row['owner_username']
            }
        
        logger.info(f"  Loaded {len(self.repo_cache)} repos")
        
        # Load ecosystems
        self.cursor.execute("""
            SELECT ecosystem_id, ecosystem_name, normalized_name
            FROM crypto_ecosystem
        """)
        for row in self.cursor.fetchall():
            self.ecosystem_cache[row['ecosystem_id']] = {
                'name': row['ecosystem_name'],
                'normalized': row['normalized_name']
            }
        
        logger.info(f"  Loaded {len(self.ecosystem_cache)} ecosystems")
    
    def github_api_call(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a GitHub API call with rate limiting"""
        url = f"{GITHUB_API}{endpoint}"
        
        self.stats['api_calls'] += 1
        
        try:
            response = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
            
            # Check rate limit
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - time.time(), 0)
                logger.warning(f"⚠️  Rate limit low ({remaining} remaining), waiting {wait_time:.0f}s...")
                if wait_time > 0:
                    time.sleep(wait_time + 1)
            
            if response.status_code == 404:
                return None
            
            if response.status_code == 403:
                logger.error(f"Rate limit exceeded")
                return None
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed for {endpoint}: {e}")
            return None
    
    def fetch_repo_contributors(self, full_name: str) -> List[Dict]:
        """Fetch contributors for a repository"""
        logger.info(f"  Fetching contributors for {full_name}...")
        
        contributors = []
        page = 1
        
        while True:
            data = self.github_api_call(
                f"/repos/{full_name}/contributors",
                {'per_page': 100, 'page': page, 'anon': 'false'}
            )
            
            if not data:
                break
            
            for contributor in data:
                if contributor.get('type') == 'User':  # Skip bots
                    contributors.append({
                        'username': contributor['login'],
                        'contributions': contributor['contributions'],
                        'avatar_url': contributor.get('avatar_url'),
                        'url': contributor.get('html_url')
                    })
            
            if len(data) < 100:
                break
            
            page += 1
            
            # Limit to avoid excessive API calls for huge repos
            if page > 10:  # Max 1000 contributors
                logger.warning(f"    Limiting to first 1000 contributors")
                break
        
        logger.info(f"    Found {len(contributors)} contributors")
        return contributors
    
    def fetch_user_profile(self, username: str) -> Optional[Dict]:
        """Fetch detailed user profile from GitHub"""
        data = self.github_api_call(f"/users/{username}")
        
        if not data:
            return None
        
        return {
            'username': data['login'],
            'name': data.get('name'),
            'email': data.get('email'),
            'bio': data.get('bio'),
            'company': data.get('company'),
            'location': data.get('location'),
            'blog': data.get('blog'),
            'twitter_username': data.get('twitter_username'),
            'followers': data.get('followers', 0),
            'following': data.get('following', 0),
            'public_repos': data.get('public_repos', 0),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'avatar_url': data.get('avatar_url'),
            'profile_url': data.get('html_url'),
            'hireable': data.get('hireable', False),
        }
    
    def parse_eip_authors(self, repo_data: Dict) -> Set[str]:
        """Parse EIP files to find authors (special case for ethereum/EIPs)"""
        if 'ethereum/eips' not in repo_data['full_name'].lower():
            return set()
        
        logger.info("  🔍 Parsing EIP authors...")
        
        authors = set()
        
        # Fetch EIP files from repo
        # This would require more complex parsing of the actual files
        # For now, we'll rely on contributors API and tag them as potential EIP authors
        
        return authors
    
    def get_ecosystem_tags(self, repo_data: Dict) -> List[str]:
        """Get ecosystem tags for a repository"""
        tags = []
        
        # Add tags from linked ecosystems
        for ecosystem_id in repo_data['ecosystem_ids']:
            if ecosystem_id in self.ecosystem_cache:
                tags.append(self.ecosystem_cache[ecosystem_id]['normalized'])
        
        # Special tagging
        full_name_lower = repo_data['full_name'].lower()
        
        if 'ethereum' in full_name_lower:
            tags.append('ethereum')
            if 'eips' in full_name_lower:
                tags.append('eip-author')
        
        if 'paradigm' in full_name_lower:
            tags.append('paradigm-ecosystem')
        
        if 'uniswap' in full_name_lower:
            tags.append('uniswap')
            tags.append('defi')
        
        # Remove duplicates
        return list(set(tags))
    
    def create_or_update_profile(
        self,
        username: str,
        profile_data: Dict,
        repo_data: Dict,
        contribution_count: int
    ) -> Optional[UUID]:
        """Create or update a GitHub profile"""
        
        # Check if exists
        profile_id = self.profile_cache.get(username.lower())
        
        ecosystem_tags = self.get_ecosystem_tags(repo_data)
        
        if self.dry_run:
            status = "update" if profile_id else "create"
            logger.info(f"[DRY RUN] Would {status} profile: {username} (tags: {ecosystem_tags})")
            return None
        
        if profile_id:
            # Update existing
            self.cursor.execute("""
                UPDATE github_profile
                SET
                    github_name = COALESCE(%s, github_name),
                    github_email = COALESCE(%s, github_email),
                    bio = COALESCE(%s, bio),
                    github_company = COALESCE(%s, github_company),
                    location = COALESCE(%s, location),
                    blog = COALESCE(%s, blog),
                    twitter_username = COALESCE(%s, twitter_username),
                    followers = GREATEST(COALESCE(followers, 0), %s),
                    following = GREATEST(COALESCE(following, 0), %s),
                    public_repos = GREATEST(COALESCE(public_repos, 0), %s),
                    avatar_url = COALESCE(%s, avatar_url),
                    ecosystem_tags = COALESCE(ecosystem_tags, '{}') || %s::text[],
                    last_enriched = NOW(),
                    updated_at = NOW()
                WHERE github_profile_id = %s
                RETURNING github_profile_id
            """, (
                profile_data.get('name'),
                profile_data.get('email'),
                profile_data.get('bio'),
                profile_data.get('company'),
                profile_data.get('location'),
                profile_data.get('blog'),
                profile_data.get('twitter_username'),
                profile_data.get('followers', 0),
                profile_data.get('following', 0),
                profile_data.get('public_repos', 0),
                profile_data.get('avatar_url'),
                ecosystem_tags,
                profile_id
            ))
            
            self.stats['contributors_enriched'] += 1
        
        else:
            # Create new
            self.cursor.execute("""
                INSERT INTO github_profile (
                    github_username,
                    github_name,
                    github_email,
                    bio,
                    github_company,
                    location,
                    blog,
                    twitter_username,
                    followers,
                    following,
                    public_repos,
                    avatar_url,
                    ecosystem_tags,
                    last_enriched
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING github_profile_id
            """, (
                username,
                profile_data.get('name'),
                profile_data.get('email'),
                profile_data.get('bio'),
                profile_data.get('company'),
                profile_data.get('location'),
                profile_data.get('blog'),
                profile_data.get('twitter_username'),
                profile_data.get('followers', 0),
                profile_data.get('following', 0),
                profile_data.get('public_repos', 0),
                profile_data.get('avatar_url'),
                ecosystem_tags
            ))
            
            profile_id = self.cursor.fetchone()['github_profile_id']
            self.profile_cache[username.lower()] = profile_id
            self.stats['contributors_discovered'] += 1
        
        # Create contribution record
        self.cursor.execute("""
            INSERT INTO github_contribution (
                github_profile_id,
                repo_id,
                contribution_count,
                contribution_type
            ) VALUES (
                %s, %s, %s, 'contributor'
            )
            ON CONFLICT (github_profile_id, repo_id)
            DO UPDATE SET
                contribution_count = GREATEST(github_contribution.contribution_count, EXCLUDED.contribution_count),
                updated_at = NOW()
        """, (profile_id, repo_data['repo_id'], contribution_count))
        
        # Record discovery event
        self.cursor.execute("""
            INSERT INTO entity_discovery (
                entity_type,
                entity_id,
                source_id,
                discovered_via_id,
                discovery_method,
                discovery_metadata
            )
            SELECT
                'person',
                %s,
                ds.source_id,
                %s,
                'contributor_scrape',
                %s::jsonb
            FROM discovery_source ds
            WHERE ds.source_type = 'contributor_expansion'
            ON CONFLICT DO NOTHING
        """, (
            profile_id,
            repo_data['repo_id'],
            json.dumps({'contributions': contribution_count, 'repo': repo_data['full_name']})
        ))
        
        return profile_id
    
    def discover_repo_contributors(self, full_name: str):
        """Discover all contributors for a repository"""
        repo_data = self.repo_cache.get(full_name.lower())
        
        if not repo_data:
            logger.warning(f"Repository not found in cache: {full_name}")
            return
        
        logger.info(f"\n📦 Processing: {full_name}")
        self.stats['repos_processed'] += 1
        
        # Fetch contributors
        contributors = self.fetch_repo_contributors(full_name)
        
        if not contributors:
            logger.warning("  No contributors found")
            return
        
        # Process each contributor
        for i, contributor in enumerate(contributors, 1):
            username = contributor['username']
            
            # Skip if already enriched recently
            if username.lower() in self.profile_cache and i > 20:  # Process top 20 always, skip rest if exists
                self.stats['contributors_skipped'] += 1
                continue
            
            logger.info(f"  [{i}/{len(contributors)}] {username} ({contributor['contributions']} contributions)")
            
            # Fetch profile
            profile_data = self.fetch_user_profile(username)
            
            if not profile_data:
                logger.warning(f"    Could not fetch profile")
                continue
            
            # Create/update profile
            self.create_or_update_profile(
                username,
                profile_data,
                repo_data,
                contributor['contributions']
            )
            
            # Rate limiting
            time.sleep(0.75)
            
            # Commit periodically
            if i % 10 == 0:
                self.conn.commit()
        
        # Update repo contributor sync timestamp
        if not self.dry_run:
            self.cursor.execute("""
                UPDATE github_repository
                SET last_contributor_sync = NOW(),
                    contributor_count = %s
                WHERE repo_id = %s
            """, (len(contributors), repo_data['repo_id']))
        
        self.conn.commit()
        logger.info(f"  ✅ Completed {full_name}")
    
    def discover_by_priority_tier(self, priority_tier: int, limit: Optional[int] = None):
        """Discover contributors for repos in a priority tier"""
        logger.info("=" * 60)
        logger.info(f"🔍 DISCOVERING CONTRIBUTORS - Priority Tier {priority_tier}")
        logger.info("=" * 60)
        
        self.load_caches()
        
        # Get repos in priority tier that need contributor sync
        self.cursor.execute("""
            SELECT r.repo_id, r.full_name, r.ecosystem_ids, r.owner_username,
                   r.last_contributor_sync, r.stars
            FROM github_repository r
            JOIN discovery_source ds ON r.discovery_source_id = ds.source_id
            WHERE ds.priority_tier <= %s
              AND (r.last_contributor_sync IS NULL 
                   OR r.last_contributor_sync < NOW() - INTERVAL '30 days')
            ORDER BY r.stars DESC NULLS LAST
            LIMIT %s
        """, (priority_tier, limit or 1000))
        
        repos = self.cursor.fetchall()
        
        logger.info(f"Found {len(repos)} repositories needing contributor sync")
        
        for i, repo in enumerate(repos, 1):
            logger.info(f"\n[{i}/{len(repos)}]")
            
            # Add to cache
            self.repo_cache[repo['full_name'].lower()] = {
                'repo_id': repo['repo_id'],
                'full_name': repo['full_name'],
                'ecosystem_ids': repo['ecosystem_ids'] or [],
                'owner_username': repo['owner_username']
            }
            
            self.discover_repo_contributors(repo['full_name'])
            
            # Progress update
            if i % 5 == 0:
                elapsed = time.time() - self.stats['start_time']
                rate = i / (elapsed / 60)  # repos per minute
                remaining = len(repos) - i
                eta = remaining / rate if rate > 0 else 0
                
                logger.info(f"\n📊 Progress: {i}/{len(repos)} repos | Rate: {rate:.1f}/min | ETA: {eta:.0f}min")
        
        logger.info("\n✅ Discovery complete!")
        self.print_stats()
    
    def print_stats(self):
        """Print discovery statistics"""
        elapsed = time.time() - self.stats['start_time']
        
        logger.info("=" * 60)
        logger.info("📊 DISCOVERY STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Repositories processed:    {self.stats['repos_processed']:,}")
        logger.info(f"Contributors discovered:   {self.stats['contributors_discovered']:,}")
        logger.info(f"Contributors enriched:     {self.stats['contributors_enriched']:,}")
        logger.info(f"Contributors skipped:      {self.stats['contributors_skipped']:,}")
        logger.info(f"EIP authors found:         {self.stats['eip_authors_found']:,}")
        logger.info(f"API calls made:            {self.stats['api_calls']:,}")
        logger.info(f"")
        logger.info(f"Time elapsed:              {elapsed/60:.1f} minutes")
        logger.info("=" * 60)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Discover and enrich repository contributors'
    )
    parser.add_argument(
        '--priority-tier',
        type=int,
        default=1,
        help='Priority tier to process (1=highest)'
    )
    parser.add_argument(
        '--repos',
        nargs='+',
        help='Specific repos to process (e.g. ethereum/EIPs)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of repos to process'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - don\'t actually create/update profiles'
    )
    
    args = parser.parse_args()
    
    discovery = ContributorDiscovery(dry_run=args.dry_run)
    
    try:
        if args.repos:
            # Process specific repos
            logger.info(f"Processing {len(args.repos)} specific repositories...")
            discovery.load_caches()
            
            for repo_name in args.repos:
                discovery.discover_repo_contributors(repo_name)
            
            discovery.print_stats()
        else:
            # Process by priority tier
            discovery.discover_by_priority_tier(args.priority_tier, args.limit)
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        discovery.print_stats()
        return 1
    
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1
    
    finally:
        discovery.close()


if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3
"""
Priority Repository Importer

Imports the specific high-priority repositories and organizations you specified:
- electric-capital/crypto-ecosystems
- ethereum/EIPs
- All paradigmxyz/* repos
- gakonst personal repos
- And any others specified

Usage:
    python3 scripts/github/import_priority_repositories.py
    python3 scripts/github/import_priority_repositories.py --dry-run
    python3 scripts/github/import_priority_repositories.py --repos ethereum/EIPs paradigmxyz/reth
"""

import argparse
import logging
import os
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

# Priority repositories (Tier 1)
PRIORITY_REPOS = [
    'electric-capital/crypto-ecosystems',
    'ethereum/EIPs',
    'ethereum/ERCs',
    'ethereum/execution-specs',
    'ethereum/consensus-specs',
]

# Priority organizations
PRIORITY_ORGS = [
    'paradigmxyz',  # All Paradigm repos
    'foundry-rs',  # Foundry
    'alloy-rs',  # Alloy
]

# Notable developers to track
NOTABLE_DEVELOPERS = [
    'gakonst',  # Georgios Konstantopoulos
]


class PriorityImporter:
    """Import priority repositories and their metadata"""
    
    def __init__(self, conn=None, dry_run=False):
        self.conn = conn or get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        self.dry_run = dry_run
        
        self.stats = {
            'repos_created': 0,
            'repos_updated': 0,
            'repos_skipped': 0,
            'orgs_processed': 0,
            'api_calls': 0,
            'start_time': time.time()
        }
        
        # Cache
        self.repo_cache = {}  # full_name -> repo_id
        self.ecosystem_cache = {}  # name -> ecosystem_id
        self.discovery_sources = {}  # source_type -> source_id
        
        logger.info(f"🚀 Priority Importer initialized (dry_run={dry_run})")
        
        if not GITHUB_TOKEN:
            logger.warning("⚠️  No GITHUB_TOKEN set - API rate limits will be very low (60/hour)")
        else:
            logger.info("✓ GitHub token configured")
    
    def load_caches(self):
        """Load existing data into cache"""
        logger.info("Loading caches...")
        
        # Load repos
        self.cursor.execute("""
            SELECT repo_id, full_name
            FROM github_repository
        """)
        for row in self.cursor.fetchall():
            self.repo_cache[row['full_name'].lower()] = row['repo_id']
        
        logger.info(f"  Loaded {len(self.repo_cache)} repos")
        
        # Load ecosystems
        self.cursor.execute("""
            SELECT ecosystem_id, ecosystem_name, normalized_name
            FROM crypto_ecosystem
        """)
        for row in self.cursor.fetchall():
            self.ecosystem_cache[row['normalized_name']] = row['ecosystem_id']
            self.ecosystem_cache[row['ecosystem_name'].lower()] = row['ecosystem_id']
        
        logger.info(f"  Loaded {len(self.ecosystem_cache)} ecosystems")
        
        # Load discovery sources
        self.cursor.execute("""
            SELECT source_id, source_type, source_name
            FROM discovery_source
        """)
        for row in self.cursor.fetchall():
            self.discovery_sources[row['source_type']] = row['source_id']
            self.discovery_sources[row['source_name']] = row['source_id']
        
        logger.info(f"  Loaded {len(self.discovery_sources)} discovery sources")
    
    def get_discovery_source(self, source_type: str, source_name: str) -> UUID:
        """Get or create discovery source"""
        if source_name in self.discovery_sources:
            return self.discovery_sources[source_name]
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create discovery source: {source_name}")
            return None
        
        self.cursor.execute("""
            INSERT INTO discovery_source (
                source_type,
                source_name,
                priority_tier,
                metadata
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_name, source_type)
            DO UPDATE SET updated_at = NOW()
            RETURNING source_id
        """, (source_type, source_name, 1, '{}'))
        
        source_id = self.cursor.fetchone()['source_id']
        self.discovery_sources[source_name] = source_id
        self.conn.commit()
        
        return source_id
    
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
                logger.error(f"Rate limit exceeded. Reset at: {response.headers.get('X-RateLimit-Reset')}")
                return None
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed for {endpoint}: {e}")
            return None
    
    def fetch_repo_metadata(self, full_name: str) -> Optional[Dict]:
        """Fetch repository metadata from GitHub API"""
        logger.info(f"  Fetching metadata for {full_name}...")
        
        data = self.github_api_call(f"/repos/{full_name}")
        if not data:
            return None
        
        return {
            'full_name': data['full_name'],
            'repo_name': data['name'],
            'owner_username': data['owner']['login'],
            'description': data.get('description'),
            'language': data.get('language'),
            'stars': data.get('stargazers_count', 0),
            'forks': data.get('forks_count', 0),
            'is_fork': data.get('fork', False),
            'homepage_url': data.get('homepage'),
            'created_at_github': data.get('created_at'),
            'updated_at_github': data.get('updated_at'),
            'last_pushed_at': data.get('pushed_at'),
            'topics': data.get('topics', []),
            'default_branch': data.get('default_branch', 'main'),
        }
    
    def fetch_org_repos(self, org_name: str) -> List[str]:
        """Fetch all repositories for an organization"""
        logger.info(f"  Fetching repos for org: {org_name}...")
        
        repos = []
        page = 1
        
        while True:
            data = self.github_api_call(
                f"/orgs/{org_name}/repos",
                {'per_page': 100, 'page': page, 'type': 'public'}
            )
            
            if not data:
                break
            
            for repo in data:
                repos.append(repo['full_name'])
            
            if len(data) < 100:
                break
            
            page += 1
        
        logger.info(f"    Found {len(repos)} repos")
        return repos
    
    def fetch_user_repos(self, username: str) -> List[str]:
        """Fetch all repositories for a user"""
        logger.info(f"  Fetching repos for user: {username}...")
        
        repos = []
        page = 1
        
        while True:
            data = self.github_api_call(
                f"/users/{username}/repos",
                {'per_page': 100, 'page': page, 'type': 'all'}
            )
            
            if not data:
                break
            
            for repo in data:
                # Include owned repos and significant contributions
                if repo['owner']['login'].lower() == username.lower():
                    repos.append(repo['full_name'])
            
            if len(data) < 100:
                break
            
            page += 1
        
        logger.info(f"    Found {len(repos)} repos")
        return repos
    
    def import_repository(
        self,
        full_name: str,
        source_type: str,
        source_name: str,
        ecosystem_name: Optional[str] = None
    ) -> Optional[UUID]:
        """Import a single repository"""
        
        # Check if exists
        repo_id = self.repo_cache.get(full_name.lower())
        
        if repo_id:
            logger.info(f"  ✓ Repo already exists: {full_name}")
            self.stats['repos_skipped'] += 1
            return repo_id
        
        # Fetch metadata
        metadata = self.fetch_repo_metadata(full_name)
        if not metadata:
            logger.warning(f"  ✗ Could not fetch metadata for {full_name}")
            return None
        
        # Get discovery source
        discovery_source_id = self.get_discovery_source(source_type, source_name)
        
        # Get ecosystem if specified
        ecosystem_ids = []
        if ecosystem_name:
            ecosystem_id = self.ecosystem_cache.get(ecosystem_name.lower())
            if ecosystem_id:
                ecosystem_ids = [ecosystem_id]
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create repo: {full_name} ({metadata['stars']} ⭐)")
            return None
        
        # Create repository
        try:
            self.cursor.execute("""
                INSERT INTO github_repository (
                    full_name,
                    repo_name,
                    owner_username,
                    description,
                    language,
                    stars,
                    forks,
                    is_fork,
                    homepage_url,
                    created_at_github,
                    updated_at_github,
                    last_pushed_at,
                    discovery_source_id,
                    ecosystem_ids
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (full_name)
                DO UPDATE SET
                    description = EXCLUDED.description,
                    language = EXCLUDED.language,
                    stars = EXCLUDED.stars,
                    forks = EXCLUDED.forks,
                    updated_at_github = EXCLUDED.updated_at_github,
                    last_pushed_at = EXCLUDED.last_pushed_at,
                    updated_at = NOW()
                RETURNING repo_id
            """, (
                metadata['full_name'],
                metadata['repo_name'],
                metadata['owner_username'],
                metadata['description'],
                metadata['language'],
                metadata['stars'],
                metadata['forks'],
                metadata['is_fork'],
                metadata['homepage_url'],
                metadata['created_at_github'],
                metadata['updated_at_github'],
                metadata['last_pushed_at'],
                discovery_source_id,
                ecosystem_ids
            ))
            
            repo_id = self.cursor.fetchone()['repo_id']
            self.repo_cache[full_name.lower()] = repo_id
            
            # Record discovery event
            self.cursor.execute("""
                INSERT INTO entity_discovery (
                    entity_type,
                    entity_id,
                    source_id,
                    discovery_method,
                    discovery_metadata
                ) VALUES (
                    'repository',
                    %s,
                    %s,
                    'manual_import',
                    %s
                )
                ON CONFLICT DO NOTHING
            """, (
                repo_id,
                discovery_source_id,
                {'stars': metadata['stars'], 'language': metadata['language']}
            ))
            
            self.conn.commit()
            
            logger.info(f"  ✓ Imported: {full_name} ({metadata['stars']} ⭐, {metadata['language']})")
            self.stats['repos_created'] += 1
            
            return repo_id
        
        except Exception as e:
            logger.error(f"  ✗ Error importing {full_name}: {e}")
            self.conn.rollback()
            return None
    
    def import_priority_repos(self):
        """Import all priority repositories"""
        logger.info("=" * 60)
        logger.info("📥 IMPORTING PRIORITY REPOSITORIES")
        logger.info("=" * 60)
        
        self.load_caches()
        
        # 1. Import individual priority repos
        logger.info(f"\n1️⃣  Importing {len(PRIORITY_REPOS)} priority repositories...")
        for repo_full_name in PRIORITY_REPOS:
            ecosystem_name = repo_full_name.split('/')[0]  # Use org name as ecosystem
            self.import_repository(
                repo_full_name,
                'manual_import',
                f'Priority: {repo_full_name}',
                ecosystem_name
            )
            
            # Rate limiting
            time.sleep(0.75)
        
        # 2. Import all repos from priority orgs
        logger.info(f"\n2️⃣  Importing repositories from {len(PRIORITY_ORGS)} priority organizations...")
        for org_name in PRIORITY_ORGS:
            logger.info(f"\n  Organization: {org_name}")
            self.stats['orgs_processed'] += 1
            
            repos = self.fetch_org_repos(org_name)
            
            for repo_full_name in repos:
                self.import_repository(
                    repo_full_name,
                    'paradigm_ecosystem' if 'paradigm' in org_name.lower() else 'manual_import',
                    f'Organization: {org_name}',
                    org_name
                )
                
                # Rate limiting
                time.sleep(0.75)
        
        # 3. Import repos from notable developers
        logger.info(f"\n3️⃣  Importing repositories from {len(NOTABLE_DEVELOPERS)} notable developers...")
        for username in NOTABLE_DEVELOPERS:
            logger.info(f"\n  Developer: {username}")
            
            repos = self.fetch_user_repos(username)
            
            for repo_full_name in repos:
                self.import_repository(
                    repo_full_name,
                    'manual_import',
                    f'Notable Developer: {username}',
                    None
                )
                
                # Rate limiting
                time.sleep(0.75)
        
        self.conn.commit()
        logger.info("\n✅ Priority repository import complete!")
        self.print_stats()
    
    def print_stats(self):
        """Print import statistics"""
        elapsed = time.time() - self.stats['start_time']
        
        logger.info("=" * 60)
        logger.info("📊 IMPORT STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Repositories created:  {self.stats['repos_created']:,}")
        logger.info(f"Repositories updated:  {self.stats['repos_updated']:,}")
        logger.info(f"Repositories skipped:  {self.stats['repos_skipped']:,}")
        logger.info(f"Organizations:         {self.stats['orgs_processed']:,}")
        logger.info(f"API calls made:        {self.stats['api_calls']:,}")
        logger.info(f"")
        logger.info(f"Time elapsed:          {elapsed:.1f}s")
        logger.info("=" * 60)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Import priority repositories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - don\'t actually import'
    )
    parser.add_argument(
        '--repos',
        nargs='+',
        help='Specific repos to import (e.g. ethereum/EIPs paradigmxyz/reth)'
    )
    
    args = parser.parse_args()
    
    importer = PriorityImporter(dry_run=args.dry_run)
    
    try:
        if args.repos:
            # Import specific repos
            logger.info(f"Importing {len(args.repos)} specific repositories...")
            importer.load_caches()
            
            for repo_name in args.repos:
                importer.import_repository(
                    repo_name,
                    'manual_import',
                    f'Manual: {repo_name}'
                )
                time.sleep(0.75)
            
            importer.print_stats()
        else:
            # Import all priority repos
            importer.import_priority_repos()
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        return 1
    
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1
    
    finally:
        importer.close()


if __name__ == '__main__':
    sys.exit(main())


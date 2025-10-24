#!/usr/bin/env python3
"""
Perpetual Discovery Engine

Runs continuously to discover:
1. All repos from Electric Capital taxonomy (50K+ repos)
2. All contributors from discovered repos
3. Related repos (forks, dependencies, same ecosystem)
4. Orbit expansion around notable developers
5. Trending repos and new activity

This runs indefinitely until manually stopped.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config, get_db_connection
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class PerpetualDiscovery:
    """Continuous discovery engine that never stops"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Stats
        self.stats = {
            'repos_discovered': 0,
            'repos_processed': 0,
            'contributors_discovered': 0,
            'contributors_enriched': 0,
            'api_calls': 0,
            'cycles_completed': 0,
            'errors': 0
        }
        
        self.start_time = datetime.now()
        
    def log_stats(self):
        """Log current statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        logger.info("=" * 80)
        logger.info(f"📊 PERPETUAL DISCOVERY STATS - Elapsed: {elapsed:.1f} minutes")
        logger.info("=" * 80)
        logger.info(f"Cycles completed:        {self.stats['cycles_completed']}")
        logger.info(f"Repos discovered:        {self.stats['repos_discovered']}")
        logger.info(f"Repos processed:         {self.stats['repos_processed']}")
        logger.info(f"Contributors discovered: {self.stats['contributors_discovered']}")
        logger.info(f"Contributors enriched:   {self.stats['contributors_enriched']}")
        logger.info(f"API calls made:          {self.stats['api_calls']}")
        logger.info(f"Errors encountered:      {self.stats['errors']}")
        logger.info("=" * 80)
        
    def get_unprocessed_repos(self, limit=50):
        """Get repos that need contributor discovery"""
        self.cursor.execute("""
            SELECT r.repo_id, r.full_name, r.stars, r.ecosystem_ids,
                   r.last_contributor_sync, ds.priority_tier
            FROM github_repository r
            LEFT JOIN discovery_source ds ON r.discovery_source_id = ds.source_id
            WHERE (r.last_contributor_sync IS NULL 
                   OR r.last_contributor_sync < NOW() - INTERVAL '7 days')
              AND r.stars >= 0
            ORDER BY 
                COALESCE(ds.priority_tier, 5) ASC,
                r.stars DESC NULLS LAST,
                r.last_contributor_sync ASC NULLS FIRST
            LIMIT %s
        """, (limit,))
        
        return self.cursor.fetchall()
    
    def discover_repo_contributors(self, repo_full_name: str, limit=100):
        """Discover contributors for a repository"""
        logger.info(f"\n🔍 Discovering contributors: {repo_full_name}")
        
        try:
            # Get contributors from GitHub API
            url = f"https://api.github.com/repos/{repo_full_name}/contributors"
            params = {'per_page': 100, 'anon': 'false'}
            
            contributors = []
            page = 1
            
            while len(contributors) < limit:
                params['page'] = page
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                self.stats['api_calls'] += 1
                
                if response.status_code == 404:
                    logger.warning(f"  Repository not found: {repo_full_name}")
                    return []
                elif response.status_code == 403:
                    logger.warning(f"  Rate limited or forbidden, sleeping...")
                    time.sleep(60)
                    continue
                elif response.status_code != 200:
                    logger.warning(f"  API error {response.status_code}")
                    return []
                
                page_contributors = response.json()
                if not page_contributors:
                    break
                
                contributors.extend(page_contributors)
                
                if len(page_contributors) < 100:
                    break
                
                page += 1
            
            logger.info(f"  Found {len(contributors)} contributors")
            return contributors[:limit]
            
        except Exception as e:
            logger.error(f"  Error fetching contributors: {e}")
            self.stats['errors'] += 1
            return []
    
    def enrich_github_profile(self, username: str):
        """Enrich a GitHub profile with full data"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=30)
            self.stats['api_calls'] += 1
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                logger.warning(f"  Rate limited while enriching {username}")
                time.sleep(60)
                return None
            else:
                logger.warning(f"  Failed to enrich {username}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"  Error enriching {username}: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_contributor(self, username: str, repo_id: str, contribution_count: int):
        """Process a single contributor"""
        
        # Check if profile exists
        self.cursor.execute("""
            SELECT github_profile_id FROM github_profile WHERE github_username = %s
        """, (username,))
        
        existing = self.cursor.fetchone()
        
        if existing:
            profile_id = existing['github_profile_id']
        else:
            # New profile - enrich and create
            profile_data = self.enrich_github_profile(username)
            
            if not profile_data:
                return None
            
            self.cursor.execute("""
                INSERT INTO github_profile (
                    github_username, github_name, github_email, github_company,
                    bio, location, blog, twitter_username,
                    followers, following, public_repos, avatar_url,
                    created_at_github, updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING github_profile_id
            """, (
                profile_data.get('login'),
                profile_data.get('name'),
                profile_data.get('email'),
                profile_data.get('company'),
                profile_data.get('bio'),
                profile_data.get('location'),
                profile_data.get('blog'),
                profile_data.get('twitter_username'),
                profile_data.get('followers', 0),
                profile_data.get('following', 0),
                profile_data.get('public_repos', 0),
                profile_data.get('avatar_url'),
                profile_data.get('created_at')
            ))
            
            profile_id = self.cursor.fetchone()['github_profile_id']
            self.stats['contributors_discovered'] += 1
            logger.info(f"    ✨ NEW: {username}")
        
        # Record contribution
        self.cursor.execute("""
            INSERT INTO github_contribution (
                github_profile_id, repo_id, contribution_count
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (github_profile_id, repo_id)
            DO UPDATE SET
                contribution_count = GREATEST(
                    github_contribution.contribution_count,
                    EXCLUDED.contribution_count
                ),
                updated_at = NOW()
        """, (profile_id, repo_id, contribution_count))
        
        self.stats['contributors_enriched'] += 1
        return profile_id
    
    def process_repository(self, repo_data: Dict):
        """Process a single repository"""
        repo_full_name = repo_data['full_name']
        repo_id = repo_data['repo_id']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📦 Processing: {repo_full_name}")
        logger.info(f"   Stars: {repo_data['stars']}, Priority: {repo_data.get('priority_tier', 'N/A')}")
        logger.info(f"{'='*80}")
        
        # Discover contributors
        contributors = self.discover_repo_contributors(repo_full_name, limit=100)
        
        if not contributors:
            logger.info(f"  No contributors found")
            return
        
        # Process each contributor
        processed = 0
        for i, contributor in enumerate(contributors[:100], 1):
            username = contributor['login']
            contributions = contributor['contributions']
            
            if i <= 20 or i % 10 == 0:  # Log first 20, then every 10th
                logger.info(f"  [{i}/{len(contributors[:100])}] {username} ({contributions} contributions)")
            
            try:
                self.process_contributor(username, repo_id, contributions)
                processed += 1
                
                # Commit every 10 contributors
                if processed % 10 == 0:
                    self.conn.commit()
                    
            except Exception as e:
                logger.error(f"  Error processing {username}: {e}")
                self.stats['errors'] += 1
                self.conn.rollback()
        
        # Update repo sync time
        self.cursor.execute("""
            UPDATE github_repository
            SET last_contributor_sync = NOW(),
                contributor_count = %s
            WHERE repo_id = %s
        """, (len(contributors), repo_id))
        
        self.conn.commit()
        self.stats['repos_processed'] += 1
        
        logger.info(f"  ✅ Completed {repo_full_name}: {processed} contributors processed")
    
    def discover_related_repos(self):
        """Discover repos related to existing ones"""
        try:
            logger.info("\n🔗 Discovering related repositories...")
            
            # Find repos with many stars that we haven't discovered yet
            # This could expand to forks, dependencies, etc.
            
            # For now, let's query for repos from discovered developers
            self.cursor.execute("""
                SELECT DISTINCT gp.github_username as username, gp.followers
                FROM github_profile gp
                JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
                WHERE gp.public_repos > 5
                  AND gp.followers > 100
                ORDER BY gp.followers DESC
                LIMIT 20
            """)
            
            notable_devs = self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error querying notable devs: {e}")
            self.conn.rollback()
            return
        
        for dev in notable_devs[:5]:  # Limit to 5 per cycle
            username = dev['username']
            logger.info(f"  Checking repos from: {username}")
            
            try:
                url = f"https://api.github.com/users/{username}/repos"
                response = requests.get(url, headers=self.headers, params={'per_page': 30}, timeout=30)
                self.stats['api_calls'] += 1
                
                if response.status_code == 200:
                    repos = response.json()
                    
                    for repo in repos[:10]:  # Top 10 repos
                        repo_full_name = repo['full_name']
                        
                        # Check if we have it
                        self.cursor.execute("""
                            SELECT repo_id FROM github_repository WHERE full_name = %s
                        """, (repo_full_name,))
                        
                        if not self.cursor.fetchone():
                            # New repo! Import it
                            logger.info(f"    🆕 Found new repo: {repo_full_name}")
                            
                            self.cursor.execute("""
                                INSERT INTO github_repository (
                                    full_name, description, stars, forks, language,
                                    owner_username, owner_avatar_url,
                                    created_at, updated_at
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                ON CONFLICT (full_name) DO NOTHING
                            """, (
                                repo_full_name,
                                repo.get('description'),
                                repo.get('stargazers_count', 0),
                                repo.get('forks_count', 0),
                                repo.get('language'),
                                repo['owner']['login'],
                                repo['owner']['avatar_url'],
                                repo.get('created_at')
                            ))
                            
                            self.stats['repos_discovered'] += 1
                    
                    self.conn.commit()
                    
            except Exception as e:
                logger.error(f"  Error discovering repos for {username}: {e}")
                self.stats['errors'] += 1
    
    def run_cycle(self):
        """Run one discovery cycle"""
        try:
            cycle_start = datetime.now()
            logger.info("\n\n" + "="*80)
            logger.info(f"🔄 STARTING DISCOVERY CYCLE #{self.stats['cycles_completed'] + 1}")
            logger.info("="*80)
            
            # Step 1: Get unprocessed repos
            repos = self.get_unprocessed_repos(limit=50)
            logger.info(f"\n📋 Found {len(repos)} repositories to process")
            
            if not repos:
                logger.info("  No repos to process, discovering related repos...")
                self.discover_related_repos()
                repos = self.get_unprocessed_repos(limit=50)
        except Exception as e:
            logger.error(f"Error starting cycle: {e}")
            self.conn.rollback()
            self.stats['errors'] += 1
            return
        
        # Step 2: Process each repo
        for i, repo in enumerate(repos[:10], 1):  # Process 10 per cycle
            logger.info(f"\n[REPO {i}/{min(10, len(repos))}]")
            try:
                self.process_repository(repo)
                
                # Rate limiting: sleep between repos
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing repo: {e}")
                self.stats['errors'] += 1
                self.conn.rollback()
        
        # Step 3: Discover related repos for next cycle
        self.discover_related_repos()
        
        # Complete cycle
        self.stats['cycles_completed'] += 1
        cycle_time = (datetime.now() - cycle_start).total_seconds() / 60
        
        logger.info(f"\n✅ Cycle #{self.stats['cycles_completed']} complete in {cycle_time:.1f} minutes")
        self.log_stats()
        
        # Brief pause between cycles
        logger.info("\n⏸️  Pausing 10 seconds before next cycle...")
        time.sleep(10)
    
    def run_perpetual(self):
        """Run continuously forever"""
        logger.info("\n" + "="*80)
        logger.info("🚀 PERPETUAL DISCOVERY ENGINE STARTED")
        logger.info("="*80)
        logger.info("\nThis will run continuously, discovering:")
        logger.info("  • All repos from Electric Capital taxonomy")
        logger.info("  • Contributors from all repos")
        logger.info("  • Related repos and orbit expansion")
        logger.info("  • New activity and trending repos")
        logger.info("\nPress Ctrl+C to stop (data will be saved)")
        logger.info("="*80)
        
        try:
            while True:
                self.run_cycle()
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Received stop signal...")
            self.log_stats()
            logger.info("\n✅ Discovery engine stopped gracefully")
            
        except Exception as e:
            logger.error(f"\n❌ Fatal error: {e}")
            self.log_stats()
            raise
            
        finally:
            self.cursor.close()
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Perpetual Discovery Engine')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    discovery = PerpetualDiscovery(dry_run=args.dry_run)
    discovery.run_perpetual()

if __name__ == '__main__':
    main()


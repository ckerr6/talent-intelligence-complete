#!/usr/bin/env python3
"""
Comprehensive Discovery Pipeline

Runs the complete discovery workflow:
1. Parse Electric Capital taxonomy (priority ecosystems)
2. Import all priority repositories
3. Discover contributors from all repos
4. Real-time logging of all discoveries

Usage:
    python3 scripts/github/comprehensive_discovery.py
    python3 scripts/github/comprehensive_discovery.py --priority-only
    python3 scripts/github/comprehensive_discovery.py --limit 100
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
import tempfile
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config, get_db_connection

# Enhanced logging with live updates
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Progress tracking
class ProgressTracker:
    def __init__(self):
        self.start_time = time.time()
        self.stats = {
            'taxonomy_parsed': False,
            'ecosystems_imported': 0,
            'repos_imported': 0,
            'contributors_discovered': 0,
            'profiles_enriched': 0,
            'current_phase': 'Starting',
            'current_repo': None,
            'current_contributor': None,
        }
    
    def update(self, **kwargs):
        self.stats.update(kwargs)
        self._print_status()
    
    def _print_status(self):
        elapsed = time.time() - self.start_time
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"📊 LIVE PROGRESS - Elapsed: {elapsed/60:.1f} minutes")
        logger.info(f"{'='*80}")
        logger.info(f"Phase: {self.stats['current_phase']}")
        logger.info(f"")
        logger.info(f"Taxonomy Parsed:        {'✅' if self.stats['taxonomy_parsed'] else '⏳'}")
        logger.info(f"Ecosystems Imported:    {self.stats['ecosystems_imported']:,}")
        logger.info(f"Repositories Imported:  {self.stats['repos_imported']:,}")
        logger.info(f"Contributors Discovered: {self.stats['contributors_discovered']:,}")
        logger.info(f"Profiles Enriched:      {self.stats['profiles_enriched']:,}")
        
        if self.stats['current_repo']:
            logger.info(f"")
            logger.info(f"Current Repo: {self.stats['current_repo']}")
        
        if self.stats['current_contributor']:
            logger.info(f"Current Contributor: {self.stats['current_contributor']}")
        
        logger.info(f"{'='*80}")
        logger.info(f"")

progress = ProgressTracker()

# GitHub API setup
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API = 'https://api.github.com'
HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'TalentIntelligence-Discovery/1.0'
}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

def github_api_call(endpoint: str):
    """Make GitHub API call"""
    url = f"{GITHUB_API}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"API call failed: {e}")
    return None

def parse_electric_capital_taxonomy(priority_only=True):
    """Phase 1: Parse Electric Capital taxonomy"""
    progress.update(current_phase='Phase 1: Parsing Electric Capital Taxonomy')
    
    logger.info(f"🌍 Starting Electric Capital taxonomy parsing...")
    logger.info(f"   Priority mode: {priority_only}")
    
    # Run the taxonomy parser
    cmd = [
        'python3',
        'scripts/github/parse_electric_capital_taxonomy.py',
        '--full'
    ]
    
    if priority_only:
        cmd.append('--priority-only')
    
    logger.info(f"   Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd='/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete',
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        
        # Parse output for stats
        for line in result.stdout.split('\n'):
            if 'ecosystems created' in line.lower():
                try:
                    count = int(''.join(filter(str.isdigit, line)))
                    progress.update(ecosystems_imported=count)
                except:
                    pass
            elif 'repositories' in line.lower() and 'created' in line.lower():
                try:
                    count = int(''.join(filter(str.isdigit, line)))
                    progress.update(repos_imported=count)
                except:
                    pass
        
        progress.update(taxonomy_parsed=True)
        logger.info(f"✅ Taxonomy parsing complete!")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Taxonomy parsing timed out after 2 hours")
        return False
    except Exception as e:
        logger.error(f"❌ Taxonomy parsing failed: {e}")
        return False

def get_priority_repos_from_db():
    """Get all priority repos to process"""
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    # Get repos from priority ecosystems
    cursor.execute("""
        SELECT DISTINCT r.repo_id, r.full_name, r.stars, r.ecosystem_ids
        FROM github_repository r
        JOIN crypto_ecosystem e ON e.ecosystem_id = ANY(r.ecosystem_ids)
        WHERE e.priority_score <= 2
          AND (r.last_contributor_sync IS NULL 
               OR r.last_contributor_sync < NOW() - INTERVAL '30 days')
        ORDER BY r.stars DESC NULLS LAST
        LIMIT 100
    """)
    
    repos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return repos

def discover_repo_contributors_live(full_name: str):
    """Discover contributors with live logging"""
    progress.update(current_repo=full_name, current_contributor=None)
    
    logger.info(f"")
    logger.info(f"📦 Processing: {full_name}")
    logger.info(f"{'─'*80}")
    
    # Fetch contributors
    logger.info(f"   🔍 Fetching contributors from GitHub API...")
    
    page = 1
    all_contributors = []
    
    while page <= 10:  # Max 1000 contributors
        data = github_api_call(f"/repos/{full_name}/contributors?per_page=100&page={page}")
        
        if not data:
            break
        
        contributors = [c for c in data if c.get('type') == 'User']
        all_contributors.extend(contributors)
        
        logger.info(f"   📄 Page {page}: Found {len(contributors)} contributors")
        
        if len(data) < 100:
            break
        
        page += 1
        time.sleep(0.5)
    
    logger.info(f"   ✅ Total: {len(all_contributors)} contributors")
    logger.info(f"")
    
    # Process each contributor
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    for i, contrib in enumerate(all_contributors, 1):
        username = contrib['login']
        contributions = contrib['contributions']
        
        progress.update(
            current_contributor=f"{username} ({i}/{len(all_contributors)})",
            contributors_discovered=progress.stats['contributors_discovered'] + 1
        )
        
        logger.info(f"   [{i:3d}/{len(all_contributors):3d}] {username:30s} | {contributions:4d} contributions")
        
        # Fetch profile
        user_data = github_api_call(f"/users/{username}")
        
        if user_data:
            # Log interesting details
            details = []
            if user_data.get('name'):
                details.append(f"Name: {user_data['name']}")
            if user_data.get('company'):
                details.append(f"Company: {user_data['company']}")
            if user_data.get('location'):
                details.append(f"Location: {user_data['location']}")
            if user_data.get('followers', 0) > 100:
                details.append(f"⭐ {user_data['followers']} followers")
            
            if details:
                logger.info(f"         {' | '.join(details)}")
            
            progress.update(profiles_enriched=progress.stats['profiles_enriched'] + 1)
        
        # Rate limit
        time.sleep(0.75)
        
        # Status update every 10 contributors
        if i % 10 == 0:
            progress.update()
    
    cursor.close()
    conn.close()
    
    logger.info(f"")
    logger.info(f"   ✅ Completed {full_name}")
    logger.info(f"")

def run_comprehensive_discovery(priority_only=True, limit=None):
    """Run the complete discovery pipeline"""
    
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"🚀 COMPREHENSIVE CRYPTO ECOSYSTEM DISCOVERY")
    logger.info(f"{'='*80}")
    logger.info(f"")
    logger.info(f"This will:")
    logger.info(f"  1. Parse Electric Capital taxonomy")
    logger.info(f"  2. Import priority ecosystems and repositories")
    logger.info(f"  3. Discover and enrich all contributors")
    logger.info(f"")
    logger.info(f"Settings:")
    logger.info(f"  Priority Only: {priority_only}")
    logger.info(f"  Limit: {limit or 'No limit'}")
    logger.info(f"")
    logger.info(f"Starting in 3 seconds...")
    time.sleep(3)
    logger.info(f"")
    
    # Phase 1: Parse taxonomy
    success = parse_electric_capital_taxonomy(priority_only)
    
    if not success:
        logger.error(f"❌ Taxonomy parsing failed. Continuing with existing data...")
    
    progress.update()
    
    # Phase 2: Get priority repos
    progress.update(current_phase='Phase 2: Loading Priority Repositories')
    
    logger.info(f"")
    logger.info(f"📚 Loading priority repositories from database...")
    
    repos = get_priority_repos_from_db()
    
    if limit:
        repos = repos[:limit]
    
    logger.info(f"   Found {len(repos)} repositories to process")
    logger.info(f"")
    
    progress.update(repos_imported=len(repos))
    
    # Phase 3: Discover contributors
    progress.update(current_phase='Phase 3: Discovering Contributors')
    
    for i, repo in enumerate(repos, 1):
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"Repository {i}/{len(repos)}")
        logger.info(f"{'='*80}")
        
        discover_repo_contributors_live(repo['full_name'])
        
        # Progress summary every 5 repos
        if i % 5 == 0:
            progress.update()
    
    # Final summary
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"✅ DISCOVERY COMPLETE!")
    logger.info(f"{'='*80}")
    progress.update(current_phase='Complete')
    
    elapsed = time.time() - progress.start_time
    logger.info(f"")
    logger.info(f"Total Time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    logger.info(f"")
    logger.info(f"Next steps:")
    logger.info(f"  ./check_overnight_results.sh")
    logger.info(f"")

def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive crypto ecosystem discovery'
    )
    parser.add_argument(
        '--priority-only',
        action='store_true',
        default=True,
        help='Only process priority ecosystems (Tier 1-2)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of repos to process'
    )
    parser.add_argument(
        '--skip-taxonomy',
        action='store_true',
        help='Skip taxonomy parsing (use existing data)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.skip_taxonomy:
            logger.info("⏭️  Skipping taxonomy parsing")
            progress.update(taxonomy_parsed=True)
            
            # Just do contributor discovery
            progress.update(current_phase='Loading Repositories')
            repos = get_priority_repos_from_db()
            
            if args.limit:
                repos = repos[:args.limit]
            
            progress.update(current_phase='Discovering Contributors')
            
            for i, repo in enumerate(repos, 1):
                logger.info(f"Repository {i}/{len(repos)}")
                discover_repo_contributors_live(repo['full_name'])
        else:
            run_comprehensive_discovery(args.priority_only, args.limit)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info(f"\n\n⚠️  Interrupted by user")
        progress.update(current_phase='Interrupted')
        return 1
    
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())


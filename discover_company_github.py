#!/usr/bin/env python3
"""
Company GitHub Discovery and Enrichment

Comprehensive script to:
1. Discover all repositories for companies with known GitHub orgs
2. Enrich repository metadata (stars, forks, languages, etc.)
3. Discover all contributors for each repository
4. Enrich contributor profiles
5. Match contributors to existing people in database

This is designed to run continuously with detailed progress logging.

Usage:
    # Discover repos for all companies
    python3 discover_company_github.py --discover-repos
    
    # Discover contributors for existing repos
    python3 discover_company_github.py --discover-contributors
    
    # Full pipeline (repos + contributors + enrichment)
    python3 discover_company_github.py --full
    
    # Specific company
    python3 discover_company_github.py --company-id <uuid>
    
    # Continuous mode
    python3 discover_company_github.py --full --continuous
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import time
import logging

sys.path.insert(0, str(Path(__file__).parent))

from config import Config, get_db_connection, load_env_file
load_env_file()

from github_automation.github_client import GitHubClient
from github_automation.enrichment_engine import EnrichmentEngine
from github_automation.matcher import ProfileMatcher

# Setup comprehensive logging
log_dir = Path(__file__).parent / 'logs' / 'company_discovery'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'discovery_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompanyGitHubDiscovery:
    """
    Comprehensive GitHub discovery for companies
    
    Workflow:
    1. Get companies with GitHub orgs (from owner_username in github_repository)
    2. Discover ALL repos for each org (update if needed)
    3. Enrich repository metadata
    4. Discover contributors for each repo
    5. Enrich contributor profiles
    6. Match contributors to people
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        self.github_client = GitHubClient(token=github_token)
        self.enrichment_engine = EnrichmentEngine(self.github_client)
        self.matcher = ProfileMatcher()
        
        self.stats = {
            'companies_processed': 0,
            'companies_failed': 0,
            'repos_discovered': 0,
            'repos_enriched': 0,
            'contributors_discovered': 0,
            'profiles_enriched': 0,
            'profiles_matched': 0,
            'api_calls': 0,
            'errors': [],
            'start_time': time.time()
        }
        
        logger.info("🚀 Company GitHub Discovery initialized")
        logger.info(f"   GitHub rate limit: {self.github_client.rate_limit_remaining} requests remaining")
    
    def get_companies_with_github_orgs(self) -> List[Dict]:
        """Get all companies that have GitHub organizations"""
        logger.info("📋 Fetching companies with GitHub orgs...")
        
        # Get distinct GitHub orgs linked to companies
        self.cursor.execute("""
            SELECT DISTINCT
                c.company_id::text as company_id,
                c.company_name as company_name,
                gr.owner_username as github_org,
                COUNT(DISTINCT gr.repo_id) as existing_repos,
                MAX(gr.updated_at) as last_repo_update
            FROM company c
            JOIN github_repository gr ON c.company_id = gr.company_id
            WHERE gr.owner_username IS NOT NULL
            GROUP BY c.company_id, c.company_name, gr.owner_username
            ORDER BY existing_repos DESC
        """)
        
        companies = []
        for row in self.cursor.fetchall():
            companies.append({
                'company_id': row['company_id'],
                'company_name': row['company_name'],
                'github_org': row['github_org'],
                'existing_repos': row['existing_repos'],
                'last_update': row['last_repo_update']
            })
        
        logger.info(f"✅ Found {len(companies)} companies with GitHub orgs")
        logger.info(f"   Total existing repos: {sum(c['existing_repos'] for c in companies):,}")
        
        return companies
    
    def discover_company_repos(self, company_id: str, github_org: str, company_name: str) -> int:
        """
        Discover all repositories for a company's GitHub org
        
        Returns number of new repos discovered
        """
        logger.info(f"🔍 Discovering repos for {company_name} (@{github_org})")
        
        try:
            # Get all repos from GitHub API
            repos = self.github_client.get_org_repos(github_org, per_page=100)
            self.stats['api_calls'] += 1
            
            if not repos:
                logger.warning(f"   ⚠️  No repos found for {github_org}")
                return 0
            
            logger.info(f"   Found {len(repos)} repos from GitHub API")
            
            # Get existing repos for this org
            self.cursor.execute("""
                SELECT LOWER(full_name) as full_name_lower
                FROM github_repository
                WHERE company_id = %s::uuid
            """, (company_id,))
            
            existing_repos = set(row['full_name_lower'] for row in self.cursor.fetchall())
            
            # Insert new repos
            new_repos = 0
            updated_repos = 0
            
            for repo in repos:
                full_name = repo['full_name']
                full_name_lower = full_name.lower()
                
                if full_name_lower in existing_repos:
                    # Update metadata
                    self.cursor.execute("""
                        UPDATE github_repository
                        SET 
                            stars = %s,
                            forks = %s,
                            language = %s,
                            description = %s,
                            homepage_url = %s,
                            is_fork = %s,
                            updated_at_github = %s,
                            last_pushed_at = %s,
                            updated_at = NOW()
                        WHERE LOWER(full_name) = %s
                          AND company_id = %s::uuid
                    """, (
                        repo.get('stargazers_count', 0),
                        repo.get('forks_count', 0),
                        repo.get('language'),
                        repo.get('description'),
                        repo.get('homepage'),
                        repo.get('fork', False),
                        repo.get('updated_at'),
                        repo.get('pushed_at'),
                        full_name_lower,
                        company_id
                    ))
                    updated_repos += 1
                else:
                    # Insert new repo
                    self.cursor.execute("""
                        INSERT INTO github_repository (
                            company_id, repo_name, full_name, owner_username,
                            language, stars, forks, description, homepage_url,
                            is_fork, created_at_github, updated_at_github, last_pushed_at
                        ) VALUES (
                            %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (full_name) DO NOTHING
                    """, (
                        company_id,
                        repo['name'],
                        full_name,
                        repo['owner']['login'],
                        repo.get('language'),
                        repo.get('stargazers_count', 0),
                        repo.get('forks_count', 0),
                        repo.get('description'),
                        repo.get('homepage'),
                        repo.get('fork', False),
                        repo.get('created_at'),
                        repo.get('updated_at'),
                        repo.get('pushed_at')
                    ))
                    new_repos += 1
            
            self.conn.commit()
            
            logger.info(f"   ✅ Added {new_repos} new repos, updated {updated_repos} existing repos")
            self.stats['repos_discovered'] += new_repos
            self.stats['repos_enriched'] += updated_repos
            
            return new_repos
            
        except Exception as e:
            logger.error(f"   ❌ Error discovering repos for {github_org}: {e}")
            self.stats['errors'].append(f"{github_org}: {str(e)}")
            self.conn.rollback()
            return 0
    
    def discover_repo_contributors(self, repo_id: str, owner: str, repo_name: str) -> int:
        """
        Discover all contributors for a repository
        
        Returns number of new contributors discovered
        """
        logger.info(f"   👥 Discovering contributors for {owner}/{repo_name}")
        
        try:
            # Get contributors from GitHub API
            contributors = self.github_client.get_repo_contributors(owner, repo_name, per_page=100)
            self.stats['api_calls'] += 1
            
            if not contributors:
                logger.info(f"      No contributors found")
                return 0
            
            logger.info(f"      Found {len(contributors)} contributors")
            
            # Get existing GitHub profiles
            usernames = [c['login'] for c in contributors]
            self.cursor.execute("""
                SELECT LOWER(github_username) as username_lower
                FROM github_profile
                WHERE LOWER(github_username) = ANY(%s)
            """, ([u.lower() for u in usernames],))
            
            existing_profiles = set(row['username_lower'] for row in self.cursor.fetchall())
            
            # Create new profiles and contribution records
            new_profiles = 0
            new_contributions = 0
            
            for contributor in contributors:
                username = contributor['login']
                username_lower = username.lower()
                
                # Create profile if doesn't exist
                if username_lower not in existing_profiles:
                    self.cursor.execute("""
                        INSERT INTO github_profile (github_username, avatar_url)
                        VALUES (%s, %s)
                        ON CONFLICT (github_username) DO NOTHING
                        RETURNING github_profile_id::text
                    """, (username, contributor.get('avatar_url')))
                    
                    result = self.cursor.fetchone()
                    if result:
                        new_profiles += 1
                        existing_profiles.add(username_lower)
                
                # Get profile_id
                self.cursor.execute("""
                    SELECT github_profile_id::text
                    FROM github_profile
                    WHERE LOWER(github_username) = %s
                """, (username_lower,))
                
                profile_row = self.cursor.fetchone()
                if not profile_row:
                    continue
                
                profile_id = profile_row['github_profile_id']
                
                # Create contribution record
                self.cursor.execute("""
                    INSERT INTO github_contribution (
                        github_profile_id, repo_id, contribution_count
                    ) VALUES (%s::uuid, %s::uuid, %s)
                    ON CONFLICT (github_profile_id, repo_id) DO UPDATE SET
                        contribution_count = EXCLUDED.contribution_count,
                        updated_at = NOW()
                """, (profile_id, repo_id, contributor.get('contributions', 0)))
                
                new_contributions += 1
            
            self.conn.commit()
            
            logger.info(f"      ✅ Added {new_profiles} new profiles, {new_contributions} contribution records")
            self.stats['contributors_discovered'] += new_profiles
            
            return new_profiles
            
        except Exception as e:
            logger.error(f"      ❌ Error discovering contributors for {owner}/{repo_name}: {e}")
            self.stats['errors'].append(f"{owner}/{repo_name}: {str(e)}")
            self.conn.rollback()
            return 0
    
    def process_company(self, company: Dict, discover_repos: bool = True, discover_contributors: bool = True):
        """Process a single company - discover repos and contributors"""
        company_name = company['company_name']
        github_org = company['github_org']
        company_id = company['company_id']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🏢 Processing: {company_name} (@{github_org})")
        logger.info(f"   Current repos in DB: {company['existing_repos']}")
        logger.info(f"{'='*80}")
        
        try:
            # Step 1: Discover repositories
            if discover_repos:
                new_repos = self.discover_company_repos(company_id, github_org, company_name)
                time.sleep(1)  # Brief delay between API calls
            
            # Step 2: Get all repos for this company
            self.cursor.execute("""
                SELECT repo_id::text, owner_username, repo_name, full_name
                FROM github_repository
                WHERE company_id = %s::uuid
                ORDER BY stars DESC NULLS LAST
            """, (company_id,))
            
            repos = self.cursor.fetchall()
            logger.info(f"\n   📦 Processing {len(repos)} repositories...")
            
            # Step 3: Discover contributors for each repo
            if discover_contributors:
                for i, repo in enumerate(repos, 1):
                    if i % 10 == 0:
                        logger.info(f"   Progress: {i}/{len(repos)} repos processed...")
                    
                    self.discover_repo_contributors(
                        repo['repo_id'],
                        repo['owner_username'],
                        repo['repo_name']
                    )
                    time.sleep(0.5)  # Brief delay between repos
            
            self.stats['companies_processed'] += 1
            logger.info(f"✅ Completed {company_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {company_name}: {e}")
            self.stats['companies_failed'] += 1
            self.stats['errors'].append(f"{company_name}: {str(e)}")
    
    def enrich_new_profiles(self, limit: int = 1000):
        """Enrich profiles that haven't been enriched yet"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 Enriching unenriched GitHub profiles (limit: {limit})")
        logger.info(f"{'='*80}")
        
        # Get unenriched profiles
        self.cursor.execute("""
            SELECT github_profile_id::text, github_username
            FROM github_profile
            WHERE last_enriched IS NULL
            ORDER BY created_at ASC
            LIMIT %s
        """, (limit,))
        
        profiles = self.cursor.fetchall()
        
        if not profiles:
            logger.info("✅ All profiles are enriched!")
            return
        
        logger.info(f"Found {len(profiles)} profiles to enrich")
        
        for i, profile in enumerate(profiles, 1):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(profiles)} profiles enriched...")
            
            try:
                success = self.enrichment_engine.enrich_profile({
                    'github_profile_id': profile['github_profile_id'],
                    'github_username': profile['github_username']
                })
                
                if success:
                    self.stats['profiles_enriched'] += 1
                
                time.sleep(0.75)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error enriching {profile['github_username']}: {e}")
        
        logger.info(f"✅ Enriched {self.stats['profiles_enriched']} profiles")
    
    def match_profiles_to_people(self, limit: int = 5000):
        """Match enriched profiles to existing people"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔗 Matching profiles to people (limit: {limit})")
        logger.info(f"{'='*80}")
        
        match_stats = self.matcher.match_unmatched_profiles(limit=limit)
        
        self.stats['profiles_matched'] = match_stats['matched']
        
        logger.info(f"✅ Matched {match_stats['matched']} profiles to people")
        logger.info(f"   High confidence: {match_stats['high_confidence']}")
        logger.info(f"   Medium confidence: {match_stats['medium_confidence']}")
        logger.info(f"   Low confidence: {match_stats['low_confidence']}")
    
    def print_stats(self):
        """Print final statistics"""
        elapsed = time.time() - self.stats['start_time']
        hours = elapsed / 3600
        
        print("\n" + "="*80)
        print("📊 DISCOVERY STATISTICS")
        print("="*80)
        print(f"⏱️  Total time: {hours:.2f} hours")
        print(f"\n🏢 Companies:")
        print(f"   Processed: {self.stats['companies_processed']}")
        print(f"   Failed: {self.stats['companies_failed']}")
        print(f"\n📦 Repositories:")
        print(f"   New repos discovered: {self.stats['repos_discovered']}")
        print(f"   Repos updated: {self.stats['repos_enriched']}")
        print(f"\n👥 Contributors:")
        print(f"   New profiles discovered: {self.stats['contributors_discovered']}")
        print(f"   Profiles enriched: {self.stats['profiles_enriched']}")
        print(f"   Profiles matched to people: {self.stats['profiles_matched']}")
        print(f"\n🌐 API:")
        print(f"   Total API calls: {self.stats['api_calls']}")
        print(f"   Rate limit remaining: {self.github_client.rate_limit_remaining}")
        
        if self.stats['errors']:
            print(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:
                print(f"   {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more")
        
        print("="*80)
    
    def run_full_discovery(self, continuous: bool = False):
        """Run full discovery pipeline"""
        iteration = 0
        
        while True:
            iteration += 1
            logger.info(f"\n{'#'*80}")
            logger.info(f"# ITERATION {iteration}")
            logger.info(f"{'#'*80}\n")
            
            # Step 1: Get companies
            companies = self.get_companies_with_github_orgs()
            
            # Step 2: Process each company
            for i, company in enumerate(companies, 1):
                logger.info(f"\n[{i}/{len(companies)}] Company {i} of {len(companies)}")
                self.process_company(company, discover_repos=True, discover_contributors=True)
                
                # Print progress summary every 10 companies
                if i % 10 == 0:
                    self.print_stats()
            
            # Step 3: Enrich new profiles
            self.enrich_new_profiles(limit=1000)
            
            # Step 4: Match profiles to people
            self.match_profiles_to_people(limit=5000)
            
            # Final stats
            self.print_stats()
            
            if not continuous:
                break
            
            logger.info("\n⏸️  Waiting 1 hour before next iteration...")
            time.sleep(3600)
    
    def close(self):
        """Cleanup"""
        self.cursor.close()
        self.conn.close()
        self.enrichment_engine.close()
        self.matcher.close()


def main():
    parser = argparse.ArgumentParser(
        description='Company GitHub Discovery and Enrichment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--discover-repos', action='store_true',
                        help='Discover repositories for companies')
    parser.add_argument('--discover-contributors', action='store_true',
                        help='Discover contributors for repositories')
    parser.add_argument('--enrich-profiles', action='store_true',
                        help='Enrich discovered GitHub profiles')
    parser.add_argument('--match-profiles', action='store_true',
                        help='Match profiles to people')
    parser.add_argument('--full', action='store_true',
                        help='Run full pipeline (all steps)')
    parser.add_argument('--continuous', action='store_true',
                        help='Run continuously (every hour)')
    parser.add_argument('--company-id', type=str,
                        help='Process specific company by ID')
    
    args = parser.parse_args()
    
    # Default to full if no specific flags
    if not any([args.discover_repos, args.discover_contributors, 
                args.enrich_profiles, args.match_profiles, args.full]):
        args.full = True
    
    logger.info("🚀 Starting Company GitHub Discovery")
    logger.info(f"   Mode: {'Continuous' if args.continuous else 'One-time'}")
    
    discovery = CompanyGitHubDiscovery()
    
    try:
        if args.full:
            discovery.run_full_discovery(continuous=args.continuous)
        else:
            companies = discovery.get_companies_with_github_orgs()
            
            if args.company_id:
                companies = [c for c in companies if c['company_id'] == args.company_id]
            
            if args.discover_repos or args.discover_contributors:
                for company in companies:
                    discovery.process_company(
                        company,
                        discover_repos=args.discover_repos,
                        discover_contributors=args.discover_contributors
                    )
            
            if args.enrich_profiles:
                discovery.enrich_new_profiles()
            
            if args.match_profiles:
                discovery.match_profiles_to_people()
            
            discovery.print_stats()
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        discovery.print_stats()
    
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}", exc_info=True)
    
    finally:
        discovery.close()


if __name__ == '__main__':
    main()


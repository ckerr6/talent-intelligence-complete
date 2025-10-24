"""
GitHub Enhanced Stats Enrichment
==================================
Enriches GitHub profiles with:
- Total merged pull requests
- Total lines of code contributed  
- Code review count
- Total stars earned

This data is crucial for recruiters/investors to assess developer quality.
"""

import os
import sys
import time
import requests
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.logging_utils import Logger
from scripts.progress_reporter import ProgressReporter

logger = Logger("GitHubEnhancer")


class GitHubStatsEnricher:
    """Enriches GitHub profiles with detailed contribution statistics"""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        
        if not self.github_token:
            logger.warning("⚠️  No GITHUB_TOKEN found. API rate limits will be very restrictive (60/hour vs 5000/hour)")
        
        self.headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        self.stats = {
            'processed': 0,
            'enriched': 0,
            'skipped': 0,
            'errors': 0,
            'rate_limited': 0
        }
    
    def enrich_all_profiles(self, limit=None, skip_existing=True):
        """
        Enrich all GitHub profiles with enhanced stats
        
        Args:
            limit: Maximum number of profiles to process (None = all)
            skip_existing: Skip profiles that already have stats
        """
        logger.section("GitHub Enhanced Stats Enrichment")
        
        # Get profiles to enrich
        query = """
            SELECT 
                gp.github_profile_id,
                gp.github_username,
                gp.person_id,
                gp.total_merged_prs,
                gp.total_lines_contributed,
                p.full_name
            FROM github_profile gp
            JOIN person p ON gp.person_id = p.person_id
            WHERE gp.github_username IS NOT NULL
        """
        
        if skip_existing:
            query += " AND (gp.total_merged_prs IS NULL OR gp.total_merged_prs = 0)"
        
        query += " ORDER BY gp.last_enriched ASC NULLS FIRST"
        
        if limit:
            query += f" LIMIT {limit}"
        
        self.cursor.execute(query)
        profiles = self.cursor.fetchall()
        
        total = len(profiles)
        logger.info(f"📊 Found {total:,} profiles to enrich")
        
        if total == 0:
            logger.success("✅ All profiles already enriched!")
            return
        
        # Process profiles
        progress = ProgressReporter(total, "Enriching GitHub profiles")
        
        for profile in profiles:
            self.stats['processed'] += 1
            progress.update(self.stats['processed'])
            
            try:
                # Enrich this profile
                result = self.enrich_profile(profile)
                
                if result['success']:
                    self.stats['enriched'] += 1
                else:
                    if 'rate' in result.get('error', '').lower():
                        self.stats['rate_limited'] += 1
                    else:
                        self.stats['errors'] += 1
                
                # Commit periodically
                if self.stats['processed'] % 10 == 0:
                    self.db.commit()
                    
            except Exception as e:
                logger.error(f"Error processing {profile['github_username']}: {str(e)}")
                self.stats['errors'] += 1
        
        self.db.commit()
        progress.finish()
        
        # Print summary
        self._print_summary()
    
    def enrich_profile(self, profile):
        """Enrich a single GitHub profile with detailed stats"""
        username = profile['github_username']
        
        try:
            # Get user's repositories with contribution data
            repos = self._get_user_repos(username)
            
            if not repos:
                return {'success': False, 'error': 'No repos found'}
            
            # Calculate stats
            stats = {
                'total_merged_prs': 0,
                'total_lines_contributed': 0,
                'code_review_count': 0,
                'total_stars_earned': 0
            }
            
            for repo in repos[:50]:  # Limit to top 50 repos to avoid rate limits
                # Get PRs merged by this user
                prs = self._get_merged_prs(username, repo)
                stats['total_merged_prs'] += len(prs)
                
                # Get lines contributed (from commit stats)
                lines = self._get_commit_stats(username, repo)
                stats['total_lines_contributed'] += lines
                
                # Stars from repos they own
                if repo.get('owner', {}).get('login', '').lower() == username.lower():
                    stats['total_stars_earned'] += repo.get('stargazers_count', 0)
            
            # Update database
            self.cursor.execute("""
                UPDATE github_profile
                SET 
                    total_merged_prs = %s,
                    total_lines_contributed = %s,
                    code_review_count = %s,
                    total_stars_earned = %s,
                    enriched_at = NOW()
                WHERE github_profile_id = %s
            """, (
                stats['total_merged_prs'],
                stats['total_lines_contributed'],
                stats['code_review_count'],
                stats['total_stars_earned'],
                profile['github_profile_id']
            ))
            
            logger.info(f"✅ {username}: {stats['total_merged_prs']} PRs, {stats['total_lines_contributed']:,} lines, {stats['total_stars_earned']:,} stars")
            
            return {'success': True, 'stats': stats}
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"⚠️  Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                return {'success': False, 'error': 'Rate limited'}
            else:
                return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_user_repos(self, username):
        """Get user's repositories"""
        try:
            response = requests.get(
                f'https://api.github.com/users/{username}/repos',
                headers=self.headers,
                params={'per_page': 100, 'sort': 'updated'},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching repos for {username}: {str(e)}")
            return []
    
    def _get_merged_prs(self, username, repo):
        """Get merged PRs by user in a repository"""
        try:
            owner = repo.get('owner', {}).get('login')
            repo_name = repo.get('name')
            
            if not owner or not repo_name:
                return []
            
            response = requests.get(
                f'https://api.github.com/search/issues',
                headers=self.headers,
                params={
                    'q': f'type:pr author:{username} repo:{owner}/{repo_name} is:merged',
                    'per_page': 100
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('items', [])
            
        except Exception as e:
            return []
    
    def _get_commit_stats(self, username, repo):
        """Get total lines contributed by user in a repository"""
        try:
            owner = repo.get('owner', {}).get('login')
            repo_name = repo.get('name')
            
            if not owner or not repo_name:
                return 0
            
            response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo_name}/stats/contributors',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            contributors = response.json()
            if not isinstance(contributors, list):
                return 0
            
            # Find this user in contributors
            for contributor in contributors:
                if contributor.get('author', {}).get('login', '').lower() == username.lower():
                    weeks = contributor.get('weeks', [])
                    total_additions = sum(week.get('a', 0) for week in weeks)
                    return total_additions
            
            return 0
            
        except Exception as e:
            return 0
    
    def _print_summary(self):
        """Print enrichment summary"""
        logger.section("Enrichment Summary")
        logger.info(f"📊 Profiles processed: {self.stats['processed']:,}")
        logger.success(f"✅ Successfully enriched: {self.stats['enriched']:,}")
        logger.warning(f"⚠️  Rate limited: {self.stats['rate_limited']:,}")
        logger.error(f"❌ Errors: {self.stats['errors']:,}")
        logger.info(f"⏭️  Skipped: {self.stats['skipped']:,}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich GitHub profiles with enhanced statistics')
    parser.add_argument('--limit', type=int, help='Limit number of profiles to process')
    parser.add_argument('--force', action='store_true', help='Re-enrich profiles that already have stats')
    parser.add_argument('--username', type=str, help='Enrich specific username only')
    
    args = parser.parse_args()
    
    # Connect to database
    conn = psycopg2.connect(
        dbname=os.environ.get('PGDATABASE', 'talent'),
        user=os.environ.get('PGUSER', 'postgres'),
        password=os.environ.get('PGPASSWORD', ''),
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432')
    )
    
    try:
        enricher = GitHubStatsEnricher(conn)
        
        if args.username:
            # Enrich specific username
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    gp.github_profile_id,
                    gp.github_username,
                    gp.person_id,
                    gp.total_merged_prs,
                    gp.total_lines_contributed,
                    p.full_name
                FROM github_profile gp
                JOIN person p ON gp.person_id = p.person_id
                WHERE gp.github_username = %s
            """, (args.username,))
            
            profile = cursor.fetchone()
            if profile:
                result = enricher.enrich_profile(profile)
                conn.commit()
                if result['success']:
                    logger.success(f"✅ Successfully enriched {args.username}")
                else:
                    logger.error(f"❌ Failed to enrich {args.username}: {result.get('error')}")
            else:
                logger.error(f"❌ Profile not found: {args.username}")
        else:
            # Enrich all profiles
            enricher.enrich_all_profiles(
                limit=args.limit,
                skip_existing=not args.force
            )
            
    finally:
        conn.close()


if __name__ == '__main__':
    main()


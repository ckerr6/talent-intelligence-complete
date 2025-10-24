#!/usr/bin/env python3
"""
ABOUTME: Computes importance scores for all repositories and developers
ABOUTME: Calls existing database functions to populate importance_score fields

Compute All Importance Scores
==============================
Computes importance scores using existing database functions:
- compute_repository_importance() for repositories
- compute_developer_importance() for GitHub profiles

Importance scores help rank:
- Most influential repositories
- Most valuable developers
- Quality of contributions

Usage:
    python3 compute_all_importance_scores.py --repos
    python3 compute_all_importance_scores.py --developers
    python3 compute_all_importance_scores.py --all
    python3 compute_all_importance_scores.py --limit 1000

Author: AI Assistant (Tier 1 Data Completion)
Date: October 24, 2025
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Dict, Optional
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import load_env_file, get_db_connection
load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImportanceScoreComputer:
    """Computes importance scores for repositories and developers"""
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'repos_processed': 0,
            'repos_scored': 0,
            'developers_processed': 0,
            'developers_scored': 0,
            'errors': []
        }
    
    def compute_repository_scores(self, limit: Optional[int] = None) -> int:
        """
        Compute importance scores for all repositories
        
        Uses compute_repository_importance() function from migration
        """
        cursor = self.conn.cursor()
        
        # Get all repos that need scoring
        query = """
            SELECT repo_id, full_name, stars, forks
            FROM github_repository
            WHERE importance_score IS NULL OR importance_score = 0
            ORDER BY stars DESC NULLS LAST, repo_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        repos = cursor.fetchall()
        
        total = len(repos)
        if total == 0:
            logger.info("No repositories need scoring")
            return 0
        
        logger.info(f"Computing importance scores for {total:,} repositories...")
        
        start_time = time.time()
        scored_count = 0
        
        for i, repo_row in enumerate(repos, 1):
            repo = dict(repo_row)
            
            try:
                # Call the compute function and update the score
                cursor.execute("""
                    UPDATE github_repository
                    SET importance_score = compute_repository_importance(repo_id)
                    WHERE repo_id = %s::uuid
                    RETURNING importance_score
                """, (repo['repo_id'],))
                
                result = cursor.fetchone()
                score = result['importance_score'] if result else 0
                
                # Count as scored regardless of score value
                scored_count += 1
                self.stats['repos_processed'] += 1
                
                # Commit every 1000 repos
                if i % 1000 == 0:
                    self.conn.commit()
                    
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total - i) / rate if rate > 0 else 0
                    
                    logger.info(
                        f"  Progress: {i:,}/{total:,} ({i/total*100:.1f}%) | "
                        f"Scored: {scored_count:,} | "
                        f"Rate: {rate:.0f}/sec | "
                        f"ETA: {eta/60:.1f}min"
                    )
                
            except Exception as e:
                logger.error(f"Error scoring repo {repo['full_name']}: {e}")
                self.stats['errors'].append(f"Repo {repo['full_name']}: {e}")
                self.conn.rollback()
        
        # Final commit
        self.conn.commit()
        
        self.stats['repos_scored'] = scored_count
        
        logger.info(f"\n✅ Completed repository scoring")
        logger.info(f"   Processed: {self.stats['repos_processed']:,}")
        logger.info(f"   Scored: {scored_count:,}")
        
        return scored_count
    
    def compute_developer_scores(self, limit: Optional[int] = None) -> int:
        """
        Compute importance scores for all developers
        
        Uses compute_developer_importance() function from migration
        """
        cursor = self.conn.cursor()
        
        # Get all profiles that need scoring
        query = """
            SELECT github_profile_id, github_username, followers
            FROM github_profile
            WHERE importance_score IS NULL OR importance_score = 0
            ORDER BY followers DESC NULLS LAST, github_profile_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        profiles = cursor.fetchall()
        
        total = len(profiles)
        if total == 0:
            logger.info("No developers need scoring")
            return 0
        
        logger.info(f"Computing importance scores for {total:,} developers...")
        
        start_time = time.time()
        scored_count = 0
        
        for i, profile_row in enumerate(profiles, 1):
            profile = dict(profile_row)
            
            try:
                # Call the compute function and update the score
                cursor.execute("""
                    UPDATE github_profile
                    SET importance_score = compute_developer_importance(github_profile_id)
                    WHERE github_profile_id = %s::uuid
                    RETURNING importance_score
                """, (profile['github_profile_id'],))
                
                result = cursor.fetchone()
                score = result['importance_score'] if result else 0
                
                # Count as scored regardless of score value
                scored_count += 1
                self.stats['developers_processed'] += 1
                
                # Commit every 1000 profiles
                if i % 1000 == 0:
                    self.conn.commit()
                    
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total - i) / rate if rate > 0 else 0
                    
                    logger.info(
                        f"  Progress: {i:,}/{total:,} ({i/total*100:.1f}%) | "
                        f"Scored: {scored_count:,} | "
                        f"Rate: {rate:.0f}/sec | "
                        f"ETA: {eta/60:.1f}min"
                    )
                
            except Exception as e:
                logger.error(f"Error scoring developer {profile['github_username']}: {e}")
                self.stats['errors'].append(f"Developer {profile['github_username']}: {e}")
                self.conn.rollback()
        
        # Final commit
        self.conn.commit()
        
        self.stats['developers_scored'] = scored_count
        
        logger.info(f"\n✅ Completed developer scoring")
        logger.info(f"   Processed: {self.stats['developers_processed']:,}")
        logger.info(f"   Scored: {scored_count:,}")
        
        return scored_count
    
    def create_indexes(self):
        """Create indexes on importance_score fields for fast queries"""
        cursor = self.conn.cursor()
        
        logger.info("Creating indexes on importance_score fields...")
        
        try:
            # Repository importance index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_github_repository_importance 
                ON github_repository(importance_score DESC NULLS LAST)
                WHERE importance_score > 0
            """)
            
            # Developer importance index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_github_profile_importance 
                ON github_profile(importance_score DESC NULLS LAST)
                WHERE importance_score > 0
            """)
            
            self.conn.commit()
            logger.info("✅ Indexes created")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            self.conn.rollback()
    
    def generate_report(self):
        """Generate report of top repositories and developers"""
        cursor = self.conn.cursor()
        
        logger.info("\n" + "="*70)
        logger.info("Top 20 Repositories by Importance")
        logger.info("="*70)
        
        cursor.execute("""
            SELECT 
                full_name,
                stars,
                forks,
                importance_score,
                language
            FROM github_repository
            WHERE importance_score > 0
            ORDER BY importance_score DESC
            LIMIT 20
        """)
        
        print("\n{:<50} {:>8} {:>7} {:>10} {:>15}".format(
            "Repository", "Stars", "Forks", "Importance", "Language"
        ))
        print("-" * 100)
        
        for row in cursor.fetchall():
            repo = dict(row)
            print("{:<50} {:>8} {:>7} {:>10.2f} {:>15}".format(
                repo['full_name'][:50],
                repo.get('stars', 0) or 0,
                repo.get('forks', 0) or 0,
                repo.get('importance_score', 0) or 0,
                (repo.get('language') or 'N/A')[:15]
            ))
        
        logger.info("\n" + "="*70)
        logger.info("Top 20 Developers by Importance")
        logger.info("="*70)
        
        cursor.execute("""
            SELECT 
                gp.github_username,
                gp.followers,
                gp.public_repos,
                gp.importance_score,
                p.full_name
            FROM github_profile gp
            LEFT JOIN person p ON gp.person_id = p.person_id
            WHERE gp.importance_score > 0
            ORDER BY gp.importance_score DESC
            LIMIT 20
        """)
        
        print("\n{:<25} {:>10} {:>10} {:>12} {:>30}".format(
            "Username", "Followers", "Repos", "Importance", "Name"
        ))
        print("-" * 100)
        
        for row in cursor.fetchall():
            dev = dict(row)
            print("{:<25} {:>10} {:>10} {:>12.2f} {:>30}".format(
                dev['github_username'][:25],
                dev.get('followers', 0) or 0,
                dev.get('public_repos', 0) or 0,
                dev.get('importance_score', 0) or 0,
                (dev.get('full_name') or '')[:30]
            ))
        
        # Summary statistics
        logger.info("\n" + "="*70)
        logger.info("Summary Statistics")
        logger.info("="*70)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_repos,
                COUNT(CASE WHEN importance_score > 0 THEN 1 END) as repos_with_scores,
                AVG(CASE WHEN importance_score > 0 THEN importance_score END) as avg_score,
                MAX(importance_score) as max_score
            FROM github_repository
        """)
        
        repo_stats = dict(cursor.fetchone())
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_developers,
                COUNT(CASE WHEN importance_score > 0 THEN 1 END) as developers_with_scores,
                AVG(CASE WHEN importance_score > 0 THEN importance_score END) as avg_score,
                MAX(importance_score) as max_score
            FROM github_profile
        """)
        
        dev_stats = dict(cursor.fetchone())
        
        print(f"\nRepositories:")
        print(f"  Total: {repo_stats['total_repos']:,}")
        print(f"  With scores: {repo_stats['repos_with_scores']:,} ({repo_stats['repos_with_scores']/repo_stats['total_repos']*100:.1f}%)")
        print(f"  Avg score: {repo_stats.get('avg_score', 0) or 0:.2f}")
        print(f"  Max score: {repo_stats.get('max_score', 0) or 0:.2f}")
        
        print(f"\nDevelopers:")
        print(f"  Total: {dev_stats['total_developers']:,}")
        print(f"  With scores: {dev_stats['developers_with_scores']:,} ({dev_stats['developers_with_scores']/dev_stats['total_developers']*100:.1f}%)")
        print(f"  Avg score: {dev_stats.get('avg_score', 0) or 0:.2f}")
        print(f"  Max score: {dev_stats.get('max_score', 0) or 0:.2f}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Compute importance scores for repos and developers')
    parser.add_argument('--repos', action='store_true', help='Compute repository scores only')
    parser.add_argument('--developers', action='store_true', help='Compute developer scores only')
    parser.add_argument('--all', action='store_true', help='Compute all scores')
    parser.add_argument('--limit', type=int, help='Limit number to process (for testing)')
    parser.add_argument('--report', action='store_true', help='Generate report only (no computation)')
    args = parser.parse_args()
    
    print("\n" + "📊 " + "=" * 66)
    print("📊  Importance Score Computation")
    print("📊 " + "=" * 66)
    
    computer = ImportanceScoreComputer()
    
    try:
        if args.report:
            print("\n📋 Generating report only...")
            computer.generate_report()
        
        elif args.all or (not args.repos and not args.developers):
            print("\n📋 Computing importance scores for repos and developers...")
            
            # Phase 1: Repositories
            print("\n" + "="*70)
            print("Phase 1: Repository Importance Scores")
            print("="*70)
            computer.compute_repository_scores(limit=args.limit)
            
            # Phase 2: Developers
            print("\n" + "="*70)
            print("Phase 2: Developer Importance Scores")
            print("="*70)
            computer.compute_developer_scores(limit=args.limit)
            
            # Phase 3: Create indexes
            print("\n" + "="*70)
            print("Phase 3: Create Indexes")
            print("="*70)
            computer.create_indexes()
            
            # Phase 4: Generate report
            print("\n" + "="*70)
            print("Phase 4: Generate Report")
            print("="*70)
            computer.generate_report()
        
        elif args.repos:
            print("\n📋 Computing repository importance scores...")
            computer.compute_repository_scores(limit=args.limit)
            computer.create_indexes()
        
        elif args.developers:
            print("\n📋 Computing developer importance scores...")
            computer.compute_developer_scores(limit=args.limit)
            computer.create_indexes()
        
        # Final stats
        stats = computer.stats
        
        print("\n" + "📊 " + "=" * 66)
        print("📊  Final Results")
        print("📊 " + "=" * 66)
        print(f"✅ Repos processed: {stats['repos_processed']:,}")
        print(f"✅ Repos scored: {stats['repos_scored']:,}")
        print(f"✅ Developers processed: {stats['developers_processed']:,}")
        print(f"✅ Developers scored: {stats['developers_scored']:,}")
        
        if stats['errors']:
            print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
            print("   (See log for details)")
        
        print("=" * 70)
        
    finally:
        computer.close()


if __name__ == '__main__':
    main()


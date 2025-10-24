#!/usr/bin/env python3
"""
ABOUTME: Builds GitHub collaboration network edges
ABOUTME: Maps who has worked with whom on shared repositories

Build GitHub Collaboration Network
===================================
Creates edges between people who have contributed to the same repositories.

Algorithm:
1. For each repository with 2+ contributors
2. Create edges between all contributor pairs
3. Weight by shared repos, contributions, time overlap
4. Aggregate across all repos

This enables queries like:
- "Find people who worked with Vitalik Buterin"
- "Show me Uniswap developers who know each other"
- "Who has Paradigm hiring managers worked with before?"

Usage:
    python3 build_collaboration_edges.py --all
    python3 build_collaboration_edges.py --ecosystem ethereum
    python3 build_collaboration_edges.py --min-contributors 5

Author: AI Assistant (Collaboration Network)
Date: October 24, 2025
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import time
import json
import psutil
import traceback
from datetime import date, datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import load_env_file, get_db_connection
load_env_file()

# Setup comprehensive logging
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"collaboration_network_build_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Progress checkpoint file
CHECKPOINT_FILE = LOG_DIR / "collaboration_network_checkpoint.json"


class CollaborationNetworkBuilder:
    """Builds GitHub collaboration network with comprehensive monitoring"""
    
    def __init__(self, resume_from_checkpoint=True):
        logger.info("="*80)
        logger.info("Initializing Collaboration Network Builder")
        logger.info("="*80)
        
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'repos_processed': 0,
            'repos_skipped': 0,
            'collaborator_pairs_found': 0,
            'edges_created': 0,
            'edges_updated': 0,
            'errors': 0,
            'start_time': time.time(),
            'last_checkpoint_time': time.time()
        }
        
        # Track processed repos for resume capability
        self.processed_repo_ids = set()
        
        # Load checkpoint if exists
        if resume_from_checkpoint and CHECKPOINT_FILE.exists():
            self._load_checkpoint()
        
        # Log system resources
        self._log_system_resources()
    
    def _log_system_resources(self):
        """Log current system resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            logger.info("="*80)
            logger.info("SYSTEM RESOURCES")
            logger.info("="*80)
            logger.info(f"Process Memory (RSS): {memory_info.rss / 1024 / 1024:.2f} MB")
            logger.info(f"Process Memory (VMS): {memory_info.vms / 1024 / 1024:.2f} MB")
            logger.info(f"System Memory Available: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB")
            logger.info(f"System Memory Percent: {psutil.virtual_memory().percent}%")
            logger.info(f"CPU Count: {psutil.cpu_count()}")
            logger.info(f"Disk Free: {psutil.disk_usage('/').free / 1024 / 1024 / 1024:.2f} GB")
            logger.info("="*80)
        except Exception as e:
            logger.warning(f"Could not log system resources: {e}")
    
    def _load_checkpoint(self):
        """Load progress from checkpoint file"""
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint = json.load(f)
            
            self.processed_repo_ids = set(checkpoint.get('processed_repo_ids', []))
            self.stats.update(checkpoint.get('stats', {}))
            
            logger.info("="*80)
            logger.info("RESUMING FROM CHECKPOINT")
            logger.info("="*80)
            logger.info(f"Processed repos: {len(self.processed_repo_ids)}")
            logger.info(f"Edges created: {self.stats.get('edges_created', 0)}")
            logger.info(f"Edges updated: {self.stats.get('edges_updated', 0)}")
            logger.info("="*80)
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
    
    def _save_checkpoint(self):
        """Save progress to checkpoint file"""
        try:
            checkpoint = {
                'processed_repo_ids': list(self.processed_repo_ids),
                'stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            logger.debug(f"Checkpoint saved: {len(self.processed_repo_ids)} repos processed")
        except Exception as e:
            logger.error(f"Could not save checkpoint: {e}")
    
    def get_repositories_to_process(
        self,
        ecosystem: Optional[str] = None,
        min_contributors: int = 2,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get repositories that have multiple contributors
        
        Args:
            ecosystem: Filter to specific ecosystem
            min_contributors: Minimum contributors per repo
            limit: Max repos to process
        """
        cursor = self.conn.cursor()
        
        where_clauses = [
            f"gr.contributor_count >= {min_contributors}"
        ]
        
        if ecosystem:
            where_clauses.append(f"""
                EXISTS (
                    SELECT 1 FROM ecosystem_repository er
                    JOIN crypto_ecosystem ce ON er.ecosystem_id = ce.ecosystem_id
                    WHERE er.repo_id = gr.repo_id
                    AND LOWER(ce.ecosystem_name) = LOWER('{ecosystem}')
                )
            """)
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                gr.repo_id,
                gr.full_name,
                gr.contributor_count,
                gr.stars
            FROM github_repository gr
            WHERE {where_clause}
            ORDER BY gr.contributor_count DESC, gr.stars DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_repo_contributors(self, repo_id: str) -> List[Dict]:
        """
        Get all contributors (with person links) for a repo
        
        Returns: List of {person_id, contribution_count, first_date, last_date}
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                gp.person_id,
                gc.contribution_count,
                gc.first_contribution_date,
                gc.last_contribution_date
            FROM github_contribution gc
            JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
            WHERE gc.repo_id = %s::uuid
            AND gp.person_id IS NOT NULL
            ORDER BY gc.contribution_count DESC
        """, (repo_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def calculate_collaboration_strength(
        self,
        shared_repos: int,
        shared_contributions: int,
        months_overlap: int
    ) -> float:
        """
        Calculate collaboration strength (0-1 scale)
        
        Factors:
        - Number of shared repos (0.4 weight)
        - Total shared contributions (0.3 weight)
        - Duration of collaboration (0.3 weight)
        """
        # Repos: normalize by 10 repos max
        repo_score = min(shared_repos / 10.0, 1.0) * 0.4
        
        # Contributions: normalize by 100 contributions max
        contrib_score = min(shared_contributions / 100.0, 1.0) * 0.3
        
        # Duration: normalize by 24 months max
        duration_score = min(months_overlap / 24.0, 1.0) * 0.3
        
        return min(repo_score + contrib_score + duration_score, 1.0)
    
    def create_collaboration_edges_for_repo(self, repo_id: str, repo_name: str) -> int:
        """
        Create collaboration edges for all contributor pairs in a repo
        
        Returns: Number of pairs processed
        """
        contributors = self.get_repo_contributors(repo_id)
        
        if len(contributors) < 2:
            return 0
        
        pairs_processed = 0
        
        # Create edges between all pairs
        for i, contributor_a in enumerate(contributors):
            for contributor_b in contributors[i+1:]:
                person_a_id = contributor_a['person_id']
                person_b_id = contributor_b['person_id']
                
                if person_a_id == person_b_id:
                    continue
                
                # Always use consistent ordering (smaller UUID first)
                if person_a_id > person_b_id:
                    person_a_id, person_b_id = person_b_id, person_a_id
                    contributor_a, contributor_b = contributor_b, contributor_a
                
                # Calculate metrics for this repo
                shared_contribs = (
                    contributor_a['contribution_count'] + 
                    contributor_b['contribution_count']
                )
                
                # Calculate time overlap
                first_a = contributor_a.get('first_contribution_date')
                last_a = contributor_a.get('last_contribution_date')
                first_b = contributor_b.get('first_contribution_date')
                last_b = contributor_b.get('last_contribution_date')
                
                overlap_start = max(first_a, first_b) if (first_a and first_b) else None
                overlap_end = min(last_a, last_b) if (last_a and last_b) else None
                
                overlap_months = 0
                if overlap_start and overlap_end and overlap_end >= overlap_start:
                    days = (overlap_end - overlap_start).days
                    overlap_months = max(days // 30, 1)
                
                # Upsert edge
                self._upsert_collaboration_edge(
                    person_a_id,
                    person_b_id,
                    repo_id,
                    repo_name,
                    shared_contribs,
                    overlap_start,
                    overlap_end,
                    overlap_months
                )
                
                pairs_processed += 1
        
        return pairs_processed
    
    def _upsert_collaboration_edge(
        self,
        person_a_id: str,
        person_b_id: str,
        repo_id: str,
        repo_name: str,
        contributions: int,
        first_date: Optional[date],
        last_date: Optional[date],
        months: int
    ):
        """
        Insert or update a collaboration edge
        
        On conflict, aggregate metrics across repos
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO edge_github_collaboration (
                    src_person_id,
                    dst_person_id,
                    shared_repos,
                    shared_contributions,
                    first_collaboration_date,
                    last_collaboration_date,
                    collaboration_months,
                    repos_list,
                    top_shared_repos
                )
                VALUES (
                    %s::uuid,
                    %s::uuid,
                    1,
                    %s,
                    %s,
                    %s,
                    %s,
                    ARRAY[%s::uuid],
                    jsonb_build_array(
                        jsonb_build_object(
                            'repo_name', %s,
                            'contributions', %s
                        )
                    )
                )
                ON CONFLICT (src_person_id, dst_person_id) DO UPDATE SET
                    shared_repos = edge_github_collaboration.shared_repos + 1,
                    shared_contributions = edge_github_collaboration.shared_contributions + EXCLUDED.shared_contributions,
                    first_collaboration_date = LEAST(
                        edge_github_collaboration.first_collaboration_date,
                        EXCLUDED.first_collaboration_date
                    ),
                    last_collaboration_date = GREATEST(
                        edge_github_collaboration.last_collaboration_date,
                        EXCLUDED.last_collaboration_date
                    ),
                    collaboration_months = GREATEST(
                        edge_github_collaboration.collaboration_months,
                        EXCLUDED.collaboration_months
                    ),
                    repos_list = array_append(edge_github_collaboration.repos_list, %s::uuid),
                    top_shared_repos = edge_github_collaboration.top_shared_repos || EXCLUDED.top_shared_repos,
                    updated_at = NOW()
                RETURNING (xmax = 0) as is_insert
            """, (
                person_a_id, person_b_id,
                contributions, first_date, last_date, months, repo_id,
                repo_name, contributions,
                repo_id
            ))
            
            result = cursor.fetchone()
            if result and result['is_insert']:
                self.stats['edges_created'] += 1
            else:
                self.stats['edges_updated'] += 1
            
        except Exception as e:
            logger.error(f"Error upserting edge: {e}")
            self.conn.rollback()
            raise
    
    def compute_collaboration_strengths(self):
        """
        Compute collaboration_strength for all edges
        
        Should be run after all edges are created
        """
        logger.info("Computing collaboration strengths...")
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE edge_github_collaboration
            SET collaboration_strength = LEAST(
                -- Repos factor (max 0.4)
                (shared_repos::FLOAT / 10.0) * 0.4 +
                -- Contributions factor (max 0.3)
                (LEAST(shared_contributions::FLOAT / 100.0, 1.0)) * 0.3 +
                -- Duration factor (max 0.3)
                (LEAST(collaboration_months::FLOAT / 24.0, 1.0)) * 0.3,
                1.0
            )
            WHERE collaboration_strength IS NULL
        """)
        
        self.conn.commit()
        logger.info(f"Updated {cursor.rowcount:,} collaboration strengths")
    
    def build_network(
        self,
        ecosystem: Optional[str] = None,
        min_contributors: int = 2,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Build the complete collaboration network with full monitoring
        
        Returns: Stats dictionary
        """
        logger.info("="*80)
        logger.info("STARTING NETWORK BUILD")
        logger.info("="*80)
        
        # Get repos to process
        repos = self.get_repositories_to_process(ecosystem, min_contributors, limit)
        total_repos = len(repos)
        
        if total_repos == 0:
            logger.warning("No repositories found matching criteria")
            return self.stats
        
        # Filter out already processed repos
        repos_to_process = [r for r in repos if r['repo_id'] not in self.processed_repo_ids]
        already_processed = total_repos - len(repos_to_process)
        
        if already_processed > 0:
            logger.info(f"Skipping {already_processed:,} already processed repos")
        
        total_repos = len(repos_to_process)
        
        if total_repos == 0:
            logger.info("All repositories already processed!")
            return self.stats
        
        logger.info(f"Processing {total_repos:,} repositories...")
        if ecosystem:
            logger.info(f"  Ecosystem: {ecosystem}")
        logger.info(f"  Min contributors: {min_contributors}")
        logger.info(f"  Log file: {log_file}")
        logger.info(f"  Checkpoint file: {CHECKPOINT_FILE}")
        logger.info("="*80)
        
        start_time = time.time()
        last_resource_log = time.time()
        
        for i, repo in enumerate(repos_to_process, 1):
            try:
                logger.debug(f"Processing repo {i}/{total_repos}: {repo['full_name']} "
                           f"({repo['contributor_count']} contributors)")
                
                pairs = self.create_collaboration_edges_for_repo(
                    repo['repo_id'],
                    repo['full_name']
                )
                
                self.stats['repos_processed'] += 1
                self.stats['collaborator_pairs_found'] += pairs
                self.processed_repo_ids.add(repo['repo_id'])
                
                # Commit and checkpoint every 100 repos
                if i % 100 == 0:
                    self.conn.commit()
                    self._save_checkpoint()
                    
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total_repos - i) / rate if rate > 0 else 0
                    
                    logger.info("="*80)
                    logger.info(f"PROGRESS UPDATE - Checkpoint #{i // 100}")
                    logger.info("="*80)
                    logger.info(
                        f"  Repos: {i:,}/{total_repos:,} ({i/total_repos*100:.1f}%)"
                    )
                    logger.info(
                        f"  Pairs Found: {self.stats['collaborator_pairs_found']:,}"
                    )
                    logger.info(
                        f"  Edges Created: {self.stats['edges_created']:,}"
                    )
                    logger.info(
                        f"  Edges Updated: {self.stats['edges_updated']:,}"
                    )
                    logger.info(
                        f"  Errors: {self.stats['errors']}"
                    )
                    logger.info(
                        f"  Rate: {rate:.2f} repos/sec ({rate*60:.1f} repos/min)"
                    )
                    logger.info(
                        f"  Elapsed: {elapsed/60:.1f} minutes"
                    )
                    logger.info(
                        f"  ETA: {eta/60:.1f} minutes"
                    )
                    logger.info("="*80)
                
                # Log system resources every 500 repos
                if i % 500 == 0 or (time.time() - last_resource_log) > 600:
                    self._log_system_resources()
                    last_resource_log = time.time()
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error("="*80)
                logger.error(f"ERROR PROCESSING REPO: {repo['full_name']}")
                logger.error(f"Repo ID: {repo['repo_id']}")
                logger.error(f"Error: {e}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                logger.error("="*80)
                self.conn.rollback()
        
        # Final commit
        logger.info("Committing final batch...")
        self.conn.commit()
        
        # Save final checkpoint
        self._save_checkpoint()
        
        # Compute strengths
        logger.info("Computing collaboration strengths...")
        self.compute_collaboration_strengths()
        
        logger.info("="*80)
        logger.info("✅ NETWORK BUILD COMPLETE!")
        logger.info("="*80)
        return self.stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def pre_flight_check(builder):
    """Run comprehensive pre-flight checks before building network"""
    logger.info("="*80)
    logger.info("PRE-FLIGHT CHECKS")
    logger.info("="*80)
    
    checks_passed = True
    
    try:
        # Check 1: Database connectivity
        cursor = builder.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM github_repository")
        result = cursor.fetchone()
        repo_count = result['cnt'] if isinstance(result, dict) else result[0]
        logger.info(f"✅ Database connection: OK ({repo_count:,} total repos)")
        
        # Check 2: Repos to process
        cursor.execute("""
            SELECT 
                COUNT(*) as repos_with_2plus,
                SUM((contributor_count * (contributor_count - 1)) / 2) as estimated_edges,
                pg_size_pretty(pg_database_size('talent')) as db_size,
                pg_size_pretty(pg_total_relation_size('edge_github_collaboration')) as table_size
            FROM github_repository
            WHERE contributor_count >= 2
        """)
        result = cursor.fetchone()
        repos_to_process = result['repos_with_2plus']
        estimated_edges = result['estimated_edges']
        db_size = result['db_size']
        table_size = result['table_size']
        
        logger.info(f"✅ Repos to process: {repos_to_process:,}")
        logger.info(f"✅ Estimated edges: {estimated_edges:,}")
        logger.info(f"✅ Current DB size: {db_size}")
        logger.info(f"✅ Current table size: {table_size}")
        
        # Check 3: Disk space
        disk = psutil.disk_usage('/')
        free_gb = disk.free / 1024 / 1024 / 1024
        estimated_size_gb = (estimated_edges * 1000) / 1024 / 1024 / 1024  # ~1KB per edge
        
        if free_gb > estimated_size_gb * 10:
            logger.info(f"✅ Disk space: {free_gb:.1f} GB free (need ~{estimated_size_gb:.1f} GB)")
        else:
            logger.error(f"❌ Disk space: Only {free_gb:.1f} GB free (need ~{estimated_size_gb:.1f} GB)")
            checks_passed = False
        
        # Check 4: Memory
        mem = psutil.virtual_memory()
        mem_available_gb = mem.available / 1024 / 1024 / 1024
        
        if mem_available_gb > 1:
            logger.info(f"✅ Memory available: {mem_available_gb:.1f} GB")
        else:
            logger.warning(f"⚠️  Memory available: {mem_available_gb:.1f} GB (low)")
        
        # Check 5: Existing progress
        cursor.execute("SELECT COUNT(*) as cnt FROM edge_github_collaboration")
        result = cursor.fetchone()
        existing_edges = result['cnt'] if isinstance(result, dict) else result[0]
        logger.info(f"✅ Existing edges: {existing_edges:,}")
        
        # Estimate time
        # Based on test: 100 repos in 1.5 minutes = 68 repos/min
        estimated_minutes = repos_to_process / 68
        logger.info(f"⏱️  Estimated time: {estimated_minutes:.1f} minutes ({estimated_minutes/60:.1f} hours)")
        
    except Exception as e:
        logger.error(f"❌ Pre-flight check failed: {e}")
        logger.error(traceback.format_exc())
        checks_passed = False
    
    logger.info("="*80)
    
    if checks_passed:
        logger.info("✅ ALL PRE-FLIGHT CHECKS PASSED")
    else:
        logger.error("❌ SOME PRE-FLIGHT CHECKS FAILED")
    
    logger.info("="*80)
    
    return checks_passed


def main():
    parser = argparse.ArgumentParser(description='Build GitHub collaboration network')
    parser.add_argument('--all', action='store_true', help='Process all repos')
    parser.add_argument('--ecosystem', type=str, help='Filter to specific ecosystem')
    parser.add_argument('--min-contributors', type=int, default=2, help='Minimum contributors per repo')
    parser.add_argument('--limit', type=int, help='Limit number of repos to process')
    parser.add_argument('--skip-preflight', action='store_true', help='Skip pre-flight checks')
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    print("\n" + "🕸️  " + "=" * 78)
    print("🕸️   GitHub Collaboration Network Builder")
    print("🕸️  " + "=" * 78)
    
    builder = CollaborationNetworkBuilder()
    
    try:
        # Run pre-flight checks
        if not args.skip_preflight:
            if not pre_flight_check(builder):
                logger.error("Pre-flight checks failed. Aborting.")
                return
            
            # Ask for confirmation
            if not args.limit and not args.no_confirm:
                response = input("\n⚠️  Ready to build FULL network. Continue? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Aborted by user.")
                    return
        
        # Build network
        logger.info("\nStarting network build...\n")
        stats = builder.build_network(
            ecosystem=args.ecosystem,
            min_contributors=args.min_contributors,
            limit=args.limit
        )
        
        elapsed = time.time() - stats['start_time']
        
        # Final stats
        print("\n" + "📊 " + "=" * 78)
        print("📊  Network Building Results")
        print("📊 " + "=" * 78)
        print(f"✅ Repos processed: {stats['repos_processed']:,}")
        print(f"✅ Repos skipped: {stats.get('repos_skipped', 0):,}")
        print(f"✅ Collaborator pairs found: {stats['collaborator_pairs_found']:,}")
        print(f"✅ Edges created: {stats['edges_created']:,}")
        print(f"✅ Edges updated: {stats['edges_updated']:,}")
        print(f"❌ Errors: {stats.get('errors', 0)}")
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
        print(f"📈 Rate: {stats['repos_processed']/(elapsed/60):.0f} repos/min")
        print("=" * 80)
        
        # Show sample query
        print("\n" + "🔍 " + "=" * 66)
        print("🔍  Sample Queries")
        print("🔍 " + "=" * 66)
        print("""
-- Find collaborators for a person
SELECT * FROM get_person_collaborators(
  'person-uuid-here',
  0.5,  -- min strength
  20    -- limit
);

-- Find mutual connections between two people
SELECT * FROM find_common_connections(
  'person-a-uuid',
  'person-b-uuid'
);

-- Top collaboration pairs
SELECT 
  p1.full_name as person_a,
  p2.full_name as person_b,
  egc.shared_repos,
  egc.collaboration_strength
FROM edge_github_collaboration egc
JOIN person p1 ON egc.src_person_id = p1.person_id
JOIN person p2 ON egc.dst_person_id = p2.person_id
ORDER BY egc.collaboration_strength DESC
LIMIT 20;
""")
        
    finally:
        builder.close()


if __name__ == '__main__':
    main()


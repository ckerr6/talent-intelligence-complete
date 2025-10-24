#!/usr/bin/env python3
"""
ABOUTME: Orchestrates batch GitHub PR enrichment for profiles
ABOUTME: Processes profiles in priority tiers with rate limiting and resume capability

Batch PR Enrichment Orchestrator
=================================
Enriches GitHub profiles with PR statistics in batches, respecting rate limits.

Prioritization Tiers:
- Tier 1: Profiles linked to people (highest priority)
- Tier 2: Profiles with followers > 100
- Tier 3: Profiles in tracked ecosystems
- Tier 4: All active profiles (contributed in last 2 years)

Features:
- Rate limit management (5K/hour GitHub API limit)
- Progress tracking and resume capability
- Overnight batch processing
- Error handling and retry logic

Usage:
    python3 batch_pr_enrichment_orchestrator.py --tier 1 --limit 5000
    python3 batch_pr_enrichment_orchestrator.py --tier 1 --all
    python3 batch_pr_enrichment_orchestrator.py --resume
    python3 batch_pr_enrichment_orchestrator.py --all-tiers  # Run all tiers

Author: AI Assistant (Tier 1 Data Completion)
Date: October 24, 2025
"""

import argparse
import sys
from pathlib import Path
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import load_env_file, get_db_connection
load_env_file()

# Import the GitHub stats enricher
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'api' / 'services'))
from github_enhanced_stats_service import GitHubStatsEnricher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CHECKPOINT_FILE = Path(__file__).parent / 'batch_enrichment_checkpoint.json'
RATE_LIMIT_PER_HOUR = 4500  # Conservative (leave 500 buffer)
BATCH_SIZE = 100  # Process this many before checkpointing


class BatchEnrichmentOrchestrator:
    """Orchestrates batch GitHub PR enrichment"""
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        self.enricher = GitHubStatsEnricher()
        
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'rate_limited': 0,
            'start_time': time.time(),
            'tier': None
        }
        
        # Load checkpoint if exists
        self.checkpoint = self._load_checkpoint()
    
    def _load_checkpoint(self) -> Dict:
        """Load checkpoint from file"""
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}")
        
        return {
            'last_processed_id': None,
            'tier': None,
            'processed_count': 0,
            'timestamp': None
        }
    
    def _save_checkpoint(self, tier: int, last_id: str, processed_count: int):
        """Save checkpoint to file"""
        try:
            checkpoint = {
                'last_processed_id': last_id,
                'tier': tier,
                'processed_count': processed_count,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save checkpoint: {e}")
    
    def get_tier_profiles(self, tier: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Get profiles for a specific tier
        
        Tiers:
        1. Profiles linked to people
        2. Profiles with followers > 100
        3. Profiles in tracked ecosystems
        4. All active profiles (contributed in last 2 years)
        """
        cursor = self.conn.cursor()
        
        # Base query - profiles not yet enriched or stale
        base_where = """
            WHERE (
                gp.total_merged_prs IS NULL 
                OR gp.last_enriched IS NULL
                OR gp.last_enriched < NOW() - INTERVAL '30 days'
            )
        """
        
        # Resume from checkpoint if applicable
        resume_clause = ""
        if self.checkpoint.get('tier') == tier and self.checkpoint.get('last_processed_id'):
            resume_clause = f"AND gp.github_profile_id > '{self.checkpoint['last_processed_id']}'::uuid"
        
        if tier == 1:
            # Tier 1: Linked to people (highest priority)
            query = f"""
                SELECT 
                    gp.github_profile_id,
                    gp.github_username,
                    gp.person_id,
                    gp.followers,
                    gp.public_repos
                FROM github_profile gp
                {base_where}
                AND gp.person_id IS NOT NULL
                {resume_clause}
                ORDER BY gp.github_profile_id
            """
        
        elif tier == 2:
            # Tier 2: High followers (influential)
            query = f"""
                SELECT 
                    gp.github_profile_id,
                    gp.github_username,
                    gp.person_id,
                    gp.followers,
                    gp.public_repos
                FROM github_profile gp
                {base_where}
                AND gp.followers > 100
                {resume_clause}
                ORDER BY gp.followers DESC, gp.github_profile_id
            """
        
        elif tier == 3:
            # Tier 3: Ecosystem contributors
            query = f"""
                SELECT 
                    gp.github_profile_id,
                    gp.github_username,
                    gp.person_id,
                    gp.followers,
                    gp.public_repos
                FROM github_profile gp
                {base_where}
                AND gp.ecosystem_tags IS NOT NULL
                AND array_length(gp.ecosystem_tags, 1) > 0
                {resume_clause}
                ORDER BY array_length(gp.ecosystem_tags, 1) DESC, gp.github_profile_id
            """
        
        elif tier == 4:
            # Tier 4: Active profiles (contributed recently)
            query = f"""
                SELECT 
                    gp.github_profile_id,
                    gp.github_username,
                    gp.person_id,
                    gp.followers,
                    gp.public_repos
                FROM github_profile gp
                {base_where}
                AND gp.updated_at_github > NOW() - INTERVAL '2 years'
                {resume_clause}
                ORDER BY gp.updated_at_github DESC, gp.github_profile_id
            """
        
        else:
            raise ValueError(f"Invalid tier: {tier}")
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def enrich_profile(self, profile: Dict) -> bool:
        """
        Enrich a single profile with PR stats
        
        Returns: True if successful, False otherwise
        """
        try:
            username = profile['github_username']
            profile_id = profile['github_profile_id']
            
            # Call enricher (same service used by API)
            result = self.enricher.enrich_profile(username)
            
            if not result or 'error' in result:
                logger.warning(f"Failed to enrich {username}: {result.get('error', 'Unknown error')}")
                return False
            
            # Update database
            self.cursor.execute("""
                UPDATE github_profile
                SET 
                    total_merged_prs = %s,
                    total_commits = %s,
                    total_issues = %s,
                    total_pull_requests = %s,
                    contribution_quality_score = %s,
                    last_enriched = NOW(),
                    updated_at = NOW()
                WHERE github_profile_id = %s::uuid
            """, (
                result.get('merged_prs', 0),
                result.get('total_commits', 0),
                result.get('total_issues', 0),
                result.get('total_pull_requests', 0),
                result.get('quality_score', 0.0),
                profile_id
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error enriching profile {profile.get('github_username')}: {e}")
            self.conn.rollback()
            return False
    
    def process_tier(self, tier: int, limit: Optional[int] = None) -> Dict:
        """Process all profiles in a tier"""
        self.stats['tier'] = tier
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing Tier {tier}")
        logger.info(f"{'='*70}")
        
        # Get profiles for this tier
        profiles = self.get_tier_profiles(tier, limit)
        total = len(profiles)
        
        if total == 0:
            logger.info(f"No profiles to process in Tier {tier}")
            return self.stats
        
        logger.info(f"Found {total:,} profiles to enrich in Tier {tier}")
        
        # Calculate estimated time
        requests_per_profile = 2  # Estimate
        total_requests = total * requests_per_profile
        hours_needed = total_requests / RATE_LIMIT_PER_HOUR
        logger.info(f"Estimated time: {hours_needed:.1f} hours ({total_requests:,} API requests)")
        
        # Process profiles
        start_time = time.time()
        request_count = 0
        hour_start = time.time()
        
        for i, profile in enumerate(profiles, 1):
            # Rate limiting check
            elapsed_hour = time.time() - hour_start
            if elapsed_hour < 3600 and request_count >= RATE_LIMIT_PER_HOUR:
                # Hit rate limit, wait until hour is up
                sleep_time = 3600 - elapsed_hour + 60  # Add 1 min buffer
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time/60:.1f} minutes...")
                time.sleep(sleep_time)
                request_count = 0
                hour_start = time.time()
                self.stats['rate_limited'] += 1
            
            # Reset counter if new hour
            if time.time() - hour_start >= 3600:
                request_count = 0
                hour_start = time.time()
            
            # Process profile
            try:
                success = self.enrich_profile(profile)
                
                if success:
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1
                
                self.stats['total_processed'] += 1
                request_count += 2  # Estimate 2 requests per profile
                
                # Progress logging
                if i % 100 == 0 or i == total:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = total - i
                    eta_seconds = remaining / rate if rate > 0 else 0
                    
                    logger.info(
                        f"  Progress: {i:,}/{total:,} ({i/total*100:.1f}%) | "
                        f"Success: {self.stats['successful']:,} | "
                        f"Failed: {self.stats['failed']:,} | "
                        f"Rate: {rate*3600:.0f}/hr | "
                        f"ETA: {eta_seconds/3600:.1f}h"
                    )
                
                # Checkpoint every BATCH_SIZE
                if i % BATCH_SIZE == 0:
                    self._save_checkpoint(tier, profile['github_profile_id'], i)
                
                # Small delay to be gentle on API
                time.sleep(0.75)  # ~4800/hour max
                
            except KeyboardInterrupt:
                logger.info("\n\nInterrupted by user. Saving checkpoint...")
                self._save_checkpoint(tier, profile['github_profile_id'], i)
                raise
            
            except Exception as e:
                logger.error(f"Unexpected error processing profile: {e}")
                self.stats['failed'] += 1
        
        # Clear checkpoint when tier complete
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        
        logger.info(f"\n✅ Tier {tier} complete!")
        return self.stats
    
    def process_all_tiers(self, limit_per_tier: Optional[int] = None):
        """Process all tiers in sequence"""
        for tier in range(1, 5):
            logger.info(f"\n{'#'*70}")
            logger.info(f"# Starting Tier {tier}")
            logger.info(f"{'#'*70}\n")
            
            self.process_tier(tier, limit=limit_per_tier)
            
            # Summary between tiers
            logger.info(f"\nTier {tier} Summary:")
            logger.info(f"  Processed: {self.stats['total_processed']:,}")
            logger.info(f"  Successful: {self.stats['successful']:,}")
            logger.info(f"  Failed: {self.stats['failed']:,}")
        
        logger.info(f"\n{'='*70}")
        logger.info("All tiers complete!")
        logger.info(f"{'='*70}")
    
    def close(self):
        """Close connections"""
        if self.conn:
            self.conn.close()
        if self.enricher:
            self.enricher.close()


def main():
    parser = argparse.ArgumentParser(description='Batch GitHub PR enrichment orchestrator')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3, 4], help='Process specific tier')
    parser.add_argument('--all-tiers', action='store_true', help='Process all tiers in sequence')
    parser.add_argument('--limit', type=int, help='Limit profiles per tier')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    print("\n" + "🚀 " + "=" * 66)
    print("🚀  Batch GitHub PR Enrichment Orchestrator")
    print("🚀 " + "=" * 66)
    
    orchestrator = BatchEnrichmentOrchestrator()
    
    try:
        if args.resume:
            checkpoint = orchestrator.checkpoint
            if checkpoint.get('tier'):
                print(f"\n📋 Resuming Tier {checkpoint['tier']} from checkpoint")
                print(f"   Last processed: {checkpoint.get('last_processed_id', 'N/A')}")
                print(f"   Already processed: {checkpoint.get('processed_count', 0):,}")
                
                orchestrator.process_tier(checkpoint['tier'], limit=args.limit)
            else:
                print("\n⚠️  No checkpoint found. Use --tier or --all-tiers to start fresh.")
        
        elif args.all_tiers:
            print("\n📋 Processing all tiers in sequence")
            if args.limit:
                print(f"   Limit per tier: {args.limit:,}")
            
            orchestrator.process_all_tiers(limit_per_tier=args.limit)
        
        elif args.tier:
            print(f"\n📋 Processing Tier {args.tier}")
            if args.limit:
                print(f"   Limit: {args.limit:,}")
            
            orchestrator.process_tier(args.tier, limit=args.limit)
        
        else:
            print("\n⚠️  Please specify --tier, --all-tiers, or --resume")
            parser.print_help()
            return
        
        # Final stats
        stats = orchestrator.stats
        elapsed = time.time() - stats['start_time']
        
        print("\n" + "📊 " + "=" * 66)
        print("📊  Final Results")
        print("📊 " + "=" * 66)
        print(f"✅ Total processed: {stats['total_processed']:,}")
        print(f"✅ Successful: {stats['successful']:,}")
        print(f"❌ Failed: {stats['failed']:,}")
        print(f"⏸️  Rate limited pauses: {stats['rate_limited']}")
        print(f"⏱️  Total time: {elapsed/3600:.2f} hours")
        print(f"📈 Rate: {stats['total_processed']/(elapsed/3600):.0f} profiles/hour")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   Checkpoint saved. Run with --resume to continue.")
    
    finally:
        orchestrator.close()


if __name__ == '__main__':
    main()


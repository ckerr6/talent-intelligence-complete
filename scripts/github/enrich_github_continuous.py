#!/usr/bin/env python3
"""
Continuous GitHub Enrichment Script

Continuously enriches GitHub profiles and matches them to people.

Usage:
    # Run once with default batch size
    python3 enrich_github_continuous.py

    # Run with custom batch size
    python3 enrich_github_continuous.py --batch-size 500

    # Run continuous mode (keeps going until stopped)
    python3 enrich_github_continuous.py --continuous

    # Run with matching after enrichment
    python3 enrich_github_continuous.py --with-matching
    
    # Status only (don't enrich)
    python3 enrich_github_continuous.py --status-only
"""

import argparse
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# IMPORTANT: Load .env file BEFORE any other imports
from config import load_env_file
load_env_file()

from github_automation.github_client import GitHubClient
from github_automation.enrichment_engine import EnrichmentEngine
from github_automation.queue_manager import QueueManager
from github_automation.matcher import ProfileMatcher
from github_automation.config import GitHubAutomationConfig as Config
import logging

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_DIR / f'enrichment_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def show_status(queue_manager: QueueManager):
    """Show current status"""
    print("\n" + "=" * 70)
    print("📊 GITHUB ENRICHMENT STATUS")
    print("=" * 70)
    
    stats = queue_manager.get_statistics()
    
    print(f"\n📈 Current State:")
    print(f"  Total GitHub profiles: {stats['total']:,}")
    print(f"  Enriched profiles: {stats['enriched']:,} ({stats['enrichment_coverage']:.1f}%)")
    print(f"  Matched to people: {stats['matched']:,} ({stats['match_rate']:.1f}%)")
    print(f"  Pending enrichment: {stats['stale']:,}")
    
    print(f"\n🎯 Goals:")
    print(f"  Target enrichment: 85% ({int(stats['total'] * 0.85):,} profiles)")
    print(f"  Target matches: 50% ({int(stats['total'] * 0.50):,} profiles)")
    
    remaining_to_enrich = int(stats['total'] * 0.85) - stats['enriched']
    remaining_to_match = int(stats['total'] * 0.50) - stats['matched']
    
    print(f"\n📋 Remaining:")
    print(f"  Need to enrich: {max(0, remaining_to_enrich):,} more profiles")
    print(f"  Need to match: {max(0, remaining_to_match):,} more profiles")
    
    # Estimate time
    if stats['stale'] > 0:
        # Assume 1 second per profile (with API delays)
        est_hours = stats['stale'] / 3600
        print(f"\n⏱️  Estimated time to complete: {est_hours:.1f} hours")
        print(f"   (At ~1 profile/second with GitHub API rate limits)")
    
    print("\n" + "=" * 70)


def run_enrichment(batch_size: int = 100, with_matching: bool = False):
    """Run one batch of enrichment"""
    print("\n" + "🚀 " + "=" * 66)
    print("🚀  Starting GitHub Enrichment")
    print("🚀 " + "=" * 66)
    
    # Validate configuration
    if not Config.validate():
        logger.error("❌ Configuration validation failed")
        return False
    
    # Initialize components
    logger.info("Initializing components...")
    client = GitHubClient()
    engine = EnrichmentEngine(client)
    queue = QueueManager()
    
    # Show initial status
    show_status(queue)
    
    # Get profiles to enrich
    logger.info(f"\n📋 Getting batch of {batch_size} profiles...")
    profiles = queue.get_batch(batch_size)
    
    if not profiles:
        logger.info("✅ No profiles need enrichment!")
        return True
    
    logger.info(f"✅ Found {len(profiles)} profiles to enrich")
    
    # Enrich batch
    start_time = time.time()
    batch_stats = engine.enrich_batch(profiles)
    elapsed = time.time() - start_time
    
    # Mark as enriched
    for profile in profiles:
        if profile.get('github_username'):  # Only mark if we processed it
            queue.mark_enriched(profile['github_profile_id'], success=True)
    
    # Show results
    print("\n" + "📊 " + "=" * 66)
    print("📊  Enrichment Complete")
    print("📊 " + "=" * 66)
    print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
    print(f"✅  Success: {batch_stats['success']:,}")
    print(f"❌  Failed: {batch_stats['failed']:,}")
    print(f"📈  Rate: {batch_stats['success']/elapsed:.1f} profiles/second")
    print("=" * 70)
    
    # Run matching if requested
    if with_matching and batch_stats['success'] > 0:
        print("\n" + "🔗 " + "=" * 66)
        print("🔗  Running Profile Matching")
        print("🔗 " + "=" * 66)
        
        matcher = ProfileMatcher()
        match_stats = matcher.match_unmatched_profiles(limit=batch_stats['success'])
        
        print(f"\n✅  Matched: {match_stats['matched']:,}")
        print(f"  High confidence: {match_stats['high_confidence']:,}")
        print(f"  Medium confidence: {match_stats['medium_confidence']:,}")
        print(f"  Low confidence: {match_stats['low_confidence']:,}")
        print("=" * 70)
        
        matcher.close()
    
    # Show updated status
    show_status(queue)
    
    # Cleanup
    engine.close()
    queue.close()
    
    return True


def run_continuous(batch_size: int = 100, with_matching: bool = False):
    """Run continuous enrichment"""
    print("\n" + "🔄 " + "=" * 66)
    print("🔄  Starting CONTINUOUS Enrichment Mode")
    print("🔄  Press Ctrl+C to stop")
    print("🔄 " + "=" * 66)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n\n{'='*70}")
            print(f"🔄  ITERATION {iteration}")
            print(f"{'='*70}")
            
            success = run_enrichment(batch_size, with_matching)
            
            if not success:
                logger.error("Enrichment batch failed, waiting before retry...")
                time.sleep(60)
                continue
            
            # Short delay between batches
            logger.info("Waiting 10 seconds before next batch...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n" + "🛑 " + "=" * 66)
        print("🛑  Stopped by user")
        print("🛑 " + "=" * 66)
        return True


def main():
    parser = argparse.ArgumentParser(
        description='GitHub Profile Enrichment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of profiles to enrich per batch (default: 100)'
    )
    
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously until stopped'
    )
    
    parser.add_argument(
        '--with-matching',
        action='store_true',
        help='Run matching after enrichment'
    )
    
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Show status only (no enrichment)'
    )
    
    args = parser.parse_args()
    
    # Show status only
    if args.status_only:
        queue = QueueManager()
        show_status(queue)
        queue.close()
        return
    
    # Run enrichment
    if args.continuous:
        run_continuous(args.batch_size, args.with_matching)
    else:
        run_enrichment(args.batch_size, args.with_matching)


if __name__ == '__main__':
    main()


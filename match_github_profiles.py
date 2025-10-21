#!/usr/bin/env python3
"""
Match GitHub Profiles to People

Matches enriched GitHub profiles to existing people in the database
using multiple matching strategies.

Usage:
    python3 match_github_profiles.py --limit 1000
    python3 match_github_profiles.py --all  # Match all unmatched profiles
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import load_env_file
load_env_file()

from github_automation.matcher import ProfileMatcher
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Match GitHub profiles to people')
    parser.add_argument('--limit', type=int, default=1000, help='Number of profiles to match')
    parser.add_argument('--all', action='store_true', help='Match all unmatched profiles')
    args = parser.parse_args()
    
    print("\n" + "🔗 " + "=" * 66)
    print("🔗  GitHub Profile Matching")
    print("🔗 " + "=" * 66)
    
    matcher = ProfileMatcher()
    
    # Match unmatched profiles
    limit = None if args.all else args.limit
    
    if args.all:
        print("\n⚠️  Matching ALL unmatched profiles (no limit)")
    else:
        print(f"\n📋 Matching up to {limit:,} profiles")
    
    stats = matcher.match_unmatched_profiles(limit=limit)
    
    print("\n" + "📊 " + "=" * 66)
    print("📊  Matching Results")
    print("📊 " + "=" * 66)
    print(f"✅ Total matched: {stats['matched']:,}")
    print(f"   High confidence (>85%): {stats['high_confidence']:,}")
    print(f"   Medium confidence (70-85%): {stats['medium_confidence']:,}")
    print(f"   Low confidence (<70%): {stats['low_confidence']:,}")
    print(f"⏭️  Skipped (no match): {stats.get('skipped', 0):,}")
    print("=" * 70)
    
    matcher.close()


if __name__ == '__main__':
    main()


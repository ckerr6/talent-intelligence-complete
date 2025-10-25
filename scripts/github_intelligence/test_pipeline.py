#!/usr/bin/env python3
"""
Quick test script to validate the GitHub intelligence extraction pipeline.
Tests the complete pipeline on a single well-known developer.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.github_intelligence.intelligence_orchestrator import IntelligenceOrchestrator


def main():
    print("=" * 70)
    print("🧪 GitHub-Native Intelligence Pipeline Test")
    print("=" * 70)
    print()
    print("This test will:")
    print("1. Fetch profile data from GitHub API")
    print("2. Extract skills, seniority, network, activity, reachability")
    print("3. Store intelligence in database")
    print()
    print("Testing on: @vitalik (Vitalik Buterin)")
    print()
    
    input("Press Enter to start test...")
    
    # Initialize orchestrator
    orchestrator = IntelligenceOrchestrator()
    
    # Test single profile
    success = orchestrator.enrich_and_store('vitalik')
    
    print()
    print("=" * 70)
    if success:
        print("✅ TEST PASSED - Pipeline working correctly!")
        print()
        print("Next steps:")
        print("1. Check database: SELECT * FROM github_intelligence WHERE github_profile_id IN (SELECT github_profile_id FROM github_profile WHERE github_username = 'vitalik');")
        print("2. Run on more profiles: python scripts/github_intelligence/intelligence_orchestrator.py --test")
        print("3. Run on existing profiles: python scripts/github_intelligence/intelligence_orchestrator.py --mode existing --limit 100")
    else:
        print("❌ TEST FAILED - Check error messages above")
    print("=" * 70)


if __name__ == '__main__':
    main()


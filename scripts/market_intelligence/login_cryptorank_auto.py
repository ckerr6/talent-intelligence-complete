#!/usr/bin/env python3
# ABOUTME: Non-interactive login script for CryptoRank with Google OAuth
# ABOUTME: Automatically opens browser and waits for you to login

"""
CryptoRank Login Helper (Auto Mode)

This script automatically opens a browser for you to login to CryptoRank.

Usage:
    python login_cryptorank_auto.py
"""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cryptorank_scraper import CryptoRankScraper


async def main():
    """Run interactive login"""
    print("=" * 70)
    print("CryptoRank Login Helper (Auto Mode)")
    print("=" * 70)
    print()
    print("Opening browser for login...")
    print()
    print("Steps:")
    print("  1. Browser window will open in 3 seconds")
    print("  2. Login using Google (or any method you prefer)")
    print("  3. After logging in, navigate to: https://cryptorank.io/funding-rounds")
    print("  4. Wait for this script to confirm (or timeout after 5 minutes)")
    print()
    
    # Small delay
    await asyncio.sleep(3)
    
    # Create scraper with visible browser
    async with CryptoRankScraper(
        headless=False,  # Show browser
        use_saved_session=False  # Don't load old session
    ) as scraper:
        # Run manual login
        success = await scraper.manual_login(timeout=300)  # 5 minutes
        
        if success:
            print()
            print("=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            print()
            print("Your session has been saved!")
            print()
            print("You can now run scraping commands without logging in:")
            print()
            print("  # Scrape 1 page (50 companies with details)")
            print("  PYTHONPATH=$PWD python3 scripts/market_intelligence/continuous_funding_sync.py --pages 1")
            print()
            print("  # Scrape specific company")
            print("  PYTHONPATH=$PWD python3 scripts/market_intelligence/continuous_funding_sync.py --company tbook")
            print()
            print("  # Scrape many pages")
            print("  PYTHONPATH=$PWD python3 scripts/market_intelligence/continuous_funding_sync.py --pages 10")
            print()
            print("=" * 70)
        else:
            print()
            print("=" * 70)
            print("❌ Login failed or session not saved")
            print("=" * 70)
            print()
            print("Please try again.")
            print()


if __name__ == '__main__':
    asyncio.run(main())


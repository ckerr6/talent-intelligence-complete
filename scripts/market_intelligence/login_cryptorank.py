#!/usr/bin/env python3
# ABOUTME: Interactive login script for CryptoRank with Google OAuth
# ABOUTME: Saves browser session for future automated scraping

"""
CryptoRank Login Helper

This script helps you login to CryptoRank (including with Google OAuth)
and saves your session for future automated scraping.

Usage:
    python login_cryptorank.py
    
The script will:
1. Open a browser window
2. Let you login manually (Google OAuth, email/password, etc.)
3. Save your session automatically
4. Future scraping runs will use this saved session
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
    print("CryptoRank Login Helper")
    print("=" * 70)
    print()
    print("This script will help you login to CryptoRank and save your session.")
    print()
    print("Steps:")
    print("  1. A browser window will open")
    print("  2. Login using any method (Google, email/password, etc.)")
    print("  3. After logging in, navigate to the Funding Rounds page")
    print("  4. The session will be saved automatically")
    print()
    print("You have 5 minutes to complete the login.")
    print()
    
    input("Press Enter to continue...")
    
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


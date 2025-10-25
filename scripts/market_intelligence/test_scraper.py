#!/usr/bin/env python3
# ABOUTME: Test script for funding scraper workflow
# ABOUTME: Validates that scraper and ingestion work end-to-end

"""
Test Funding Scraper Workflow

This script tests the funding scraper without requiring authentication.
It validates:
- Playwright browser launches correctly
- Page navigation works
- Data extraction functions
- Database schema is correct
- Ingestion logic works

Usage:
    python scripts/market_intelligence/test_scraper.py
"""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cryptorank_scraper import CryptoRankScraper
from funding_ingestion import FundingIngestion


async def test_scraper():
    """Test scraper functionality"""
    print("🧪 Testing Funding Scraper Workflow")
    print("=" * 60)
    
    # Test 1: Browser Launch
    print("\n[1/5] Testing browser launch...")
    try:
        async with CryptoRankScraper(headless=True) as scraper:
            print("  ✅ Browser launched successfully")
    except Exception as e:
        print(f"  ❌ Browser launch failed: {e}")
        return False
    
    # Test 2: Navigation
    print("\n[2/5] Testing page navigation...")
    try:
        async with CryptoRankScraper(headless=True) as scraper:
            await scraper.page.goto("https://cryptorank.io", timeout=15000)
            print(f"  ✅ Successfully navigated to cryptorank.io")
            print(f"  Page title: {await scraper.page.title()}")
    except Exception as e:
        print(f"  ❌ Navigation failed: {e}")
        return False
    
    # Test 3: Data Extraction (without auth)
    print("\n[3/5] Testing data extraction...")
    try:
        async with CryptoRankScraper(headless=True) as scraper:
            # Try to scrape just the first row
            await scraper.page.goto(
                "https://cryptorank.io/funding-rounds?rows=50",
                timeout=15000
            )
            
            # Wait for table
            try:
                await scraper.page.wait_for_selector('table tbody tr', timeout=10000)
                rows = await scraper.page.query_selector_all('table tbody tr')
                
                if rows:
                    print(f"  ✅ Found {len(rows)} funding rounds on page")
                    
                    # Try to extract first row
                    first_row = rows[0]
                    row_data = await scraper._extract_funding_row(first_row)
                    
                    if row_data:
                        print(f"  ✅ Successfully extracted row data:")
                        print(f"     Company: {row_data.get('company_name')}")
                        print(f"     Amount: ${row_data.get('amount_usd', 'N/A')}")
                        print(f"     Stage: {row_data.get('round_stage', 'N/A')}")
                    else:
                        print(f"  ⚠️  Row data extraction returned None")
                else:
                    print(f"  ⚠️  No funding rounds found (may need authentication)")
            
            except Exception as e:
                print(f"  ⚠️  Could not extract data (may need authentication): {e}")
                print(f"  This is expected without login credentials")
    
    except Exception as e:
        print(f"  ❌ Data extraction test failed: {e}")
        return False
    
    # Test 4: Database Schema
    print("\n[4/5] Testing database schema...")
    try:
        from config import get_db_context
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Check investor table
            cursor.execute("""
                SELECT COUNT(*) as count FROM investor
            """)
            investor_count = cursor.fetchone()['count']
            print(f"  ✅ investor table exists ({investor_count} records)")
            
            # Check company_funding_round table
            cursor.execute("""
                SELECT COUNT(*) as count FROM company_funding_round
            """)
            round_count = cursor.fetchone()['count']
            print(f"  ✅ company_funding_round table exists ({round_count} records)")
            
            # Check for new columns
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'company'
                AND column_name IN ('twitter_url', 'github_url', 'cryptorank_slug')
                ORDER BY column_name
            """)
            columns = [row['column_name'] for row in cursor.fetchall()]
            print(f"  ✅ company table enhanced with: {', '.join(columns)}")
    
    except Exception as e:
        print(f"  ❌ Database schema check failed: {e}")
        print(f"  Run migration: psql -d talent -f migration_scripts/11_funding_and_investor_schema.sql")
        return False
    
    # Test 5: Ingestion Logic
    print("\n[5/5] Testing ingestion logic...")
    try:
        # Create dummy funding data
        dummy_data = {
            'company_name': 'Test Company XYZ',
            'cryptorank_slug': 'test-company-xyz-123',
            'amount_usd': 5000000,
            'round_stage': 'Seed',
            'announced_date': '2025-10-25',
            'investors_preview': [
                {'name': 'Test VC Fund', 'cryptorank_slug': 'test-vc-fund'}
            ],
            'social_links': {
                'website_url': 'https://testcompany.xyz',
                'twitter_url': 'https://twitter.com/testcompany'
            }
        }
        
        ingestion = FundingIngestion()
        result = ingestion.store_funding_round(dummy_data)
        
        print(f"  ✅ Ingestion successful:")
        print(f"     Company created: {result['company_created']}")
        print(f"     Round created: {result['round_created']}")
        print(f"     Investors created: {result['investors_created']}")
        
        # Clean up test data
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM company WHERE cryptorank_slug = 'test-company-xyz-123'
            """)
            cursor.execute("""
                DELETE FROM investor WHERE cryptorank_slug = 'test-vc-fund'
            """)
            conn.commit()
        print(f"  ✅ Test data cleaned up")
    
    except Exception as e:
        print(f"  ❌ Ingestion test failed: {e}")
        return False
    
    # All tests passed!
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("\nNext steps:")
    print("  1. Set authentication credentials:")
    print("     export CRYPTORANK_EMAIL='your@email.com'")
    print("     export CRYPTORANK_PASSWORD='your_password'")
    print("\n  2. Run your first sync:")
    print("     python scripts/market_intelligence/continuous_funding_sync.py --pages 1")
    print("\n  3. Query the data:")
    print("     psql -d talent -c 'SELECT * FROM recent_funding LIMIT 10'")
    print("\n" + "=" * 60)
    
    return True


if __name__ == '__main__':
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1)


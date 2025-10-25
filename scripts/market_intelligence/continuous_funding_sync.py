#!/usr/bin/env python3
# ABOUTME: Continuous funding data sync from cryptorank.io
# ABOUTME: Orchestrates scraping and ingestion on a schedule

"""
Continuous Funding Data Sync

This script orchestrates the continuous scraping and ingestion of
funding data from cryptorank.io. It can be run:
- One-time (scrape and ingest immediately)
- Scheduled (run daily/weekly via cron)
- Continuous (loop with delays)

Usage:
    # One-time sync
    python continuous_funding_sync.py --pages 5
    
    # Continuous mode (runs every 24 hours)
    python continuous_funding_sync.py --continuous --interval 86400
    
    # With authentication
    python continuous_funding_sync.py --email user@example.com --password secret
"""

import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

from cryptorank_scraper import CryptoRankScraper
from funding_ingestion import FundingIngestion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FundingSyncOrchestrator:
    """Orchestrates funding data scraping and ingestion"""
    
    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = True,
        save_screenshots: bool = False
    ):
        """
        Initialize orchestrator
        
        Args:
            email: CryptoRank login email
            password: CryptoRank login password
            headless: Run browser in headless mode
            save_screenshots: Save debug screenshots
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.save_screenshots = save_screenshots
        
        # Create data directory for scraped JSON
        self.data_dir = Path(__file__).parent / "scraped_data"
        self.data_dir.mkdir(exist_ok=True)
    
    async def sync_funding_list(self, pages: int = 1) -> dict:
        """
        Scrape and ingest funding list
        
        Args:
            pages: Number of pages to scrape (50 companies per page)
        
        Returns:
            Statistics about what was synced
        """
        logger.info(f"Starting funding list sync ({pages} page(s))...")
        start_time = datetime.now()
        
        stats = {
            'pages_scraped': pages,
            'companies_scraped': 0,
            'companies_stored': 0,
            'rounds_created': 0,
            'investors_created': 0,
            'errors': 0,
            'duration_seconds': 0
        }
        
        try:
            # Step 1: Scrape data
            logger.info("Step 1: Scraping data from cryptorank.io...")
            
            async with CryptoRankScraper(
                headless=self.headless,
                save_screenshots=self.save_screenshots
            ) as scraper:
                # Login if credentials provided
                if self.email and self.password:
                    await scraper.login(self.email, self.password)
                
                # Scrape funding list
                funding_list = await scraper.scrape_funding_list(pages=pages)
                stats['companies_scraped'] = len(funding_list)
                
                # Save raw data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                data_file = self.data_dir / f"funding_list_{timestamp}.json"
                
                import json
                with open(data_file, 'w') as f:
                    json.dump({'funding_list': funding_list}, f, indent=2)
                
                logger.info(f"Scraped {len(funding_list)} companies, saved to {data_file}")
            
            # Step 2: Ingest into database
            logger.info("Step 2: Ingesting into database...")
            
            ingestion = FundingIngestion()
            ingest_stats = ingestion.store_funding_list(funding_list)
            
            stats['companies_stored'] = (
                ingest_stats.get('companies_created', 0) +
                ingest_stats.get('companies_updated', 0)
            )
            stats['rounds_created'] = ingest_stats.get('rounds_created', 0)
            stats['investors_created'] = ingest_stats.get('investors_created', 0)
            
            logger.info(f"Ingestion complete: {ingest_stats}")
        
        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)
            stats['errors'] = 1
        
        finally:
            stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Sync complete: {stats}")
        return stats
    
    async def sync_company_detail(self, cryptorank_slug: str) -> dict:
        """
        Scrape and ingest detailed company data
        
        Args:
            cryptorank_slug: Company slug (e.g., 'echodotxyz')
        
        Returns:
            Statistics about what was synced
        """
        logger.info(f"Starting company detail sync: {cryptorank_slug}")
        start_time = datetime.now()
        
        stats = {
            'company': cryptorank_slug,
            'rounds_scraped': 0,
            'rounds_stored': 0,
            'investors_created': 0,
            'errors': 0,
            'duration_seconds': 0
        }
        
        try:
            # Step 1: Scrape company details
            logger.info("Step 1: Scraping company details...")
            
            async with CryptoRankScraper(
                headless=self.headless,
                save_screenshots=self.save_screenshots
            ) as scraper:
                # Login if credentials provided
                if self.email and self.password:
                    await scraper.login(self.email, self.password)
                
                # Scrape company
                company_data = await scraper.scrape_company_detail(cryptorank_slug)
                stats['rounds_scraped'] = len(company_data.get('funding_rounds', []))
                
                # Save raw data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                data_file = self.data_dir / f"company_{cryptorank_slug}_{timestamp}.json"
                
                import json
                with open(data_file, 'w') as f:
                    json.dump({'company_data': company_data}, f, indent=2)
                
                logger.info(f"Scraped company data, saved to {data_file}")
            
            # Step 2: Ingest into database
            logger.info("Step 2: Ingesting into database...")
            
            ingestion = FundingIngestion()
            ingest_result = ingestion.store_funding_round(company_data)
            
            stats['rounds_stored'] = 1 if ingest_result.get('round_created') else 0
            stats['investors_created'] = ingest_result.get('investors_created', 0)
            
            logger.info(f"Ingestion complete: {ingest_result}")
        
        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)
            stats['errors'] = 1
        
        finally:
            stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Company sync complete: {stats}")
        return stats
    
    async def continuous_sync(self, pages: int = 1, interval_seconds: int = 86400):
        """
        Run continuous sync loop
        
        Args:
            pages: Number of pages to scrape per sync
            interval_seconds: Delay between syncs (default: 24 hours)
        """
        logger.info(f"Starting continuous sync (every {interval_seconds}s)...")
        
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Sync iteration #{iteration} - {datetime.now().isoformat()}")
            logger.info(f"{'='*60}")
            
            try:
                stats = await self.sync_funding_list(pages=pages)
                
                logger.info(f"Iteration #{iteration} complete: {stats}")
                logger.info(f"Next sync in {interval_seconds}s ({interval_seconds/3600:.1f} hours)")
                
                # Wait for next iteration
                await asyncio.sleep(interval_seconds)
            
            except KeyboardInterrupt:
                logger.info("Continuous sync interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous sync: {e}", exc_info=True)
                logger.info(f"Retrying in {interval_seconds}s...")
                await asyncio.sleep(interval_seconds)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Continuous funding data sync from cryptorank.io',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape first 5 pages one time
  python continuous_funding_sync.py --pages 5
  
  # Scrape specific company
  python continuous_funding_sync.py --company echodotxyz
  
  # Continuous mode (daily updates)
  python continuous_funding_sync.py --continuous --pages 10 --interval 86400
  
  # With authentication
  export CRYPTORANK_EMAIL=user@example.com
  export CRYPTORANK_PASSWORD=secret
  python continuous_funding_sync.py --pages 5
        """
    )
    
    parser.add_argument('--pages', type=int, default=1,
                       help='Number of pages to scrape (50 companies per page)')
    parser.add_argument('--company', type=str,
                       help='Scrape specific company by cryptorank slug')
    parser.add_argument('--email', type=str,
                       help='CryptoRank login email (or set CRYPTORANK_EMAIL env var)')
    parser.add_argument('--password', type=str,
                       help='CryptoRank login password (or set CRYPTORANK_PASSWORD env var)')
    parser.add_argument('--continuous', action='store_true',
                       help='Run in continuous mode (loop forever)')
    parser.add_argument('--interval', type=int, default=86400,
                       help='Interval between syncs in seconds (default: 86400 = 24 hours)')
    parser.add_argument('--show-browser', action='store_true',
                       help='Show browser window (for debugging)')
    parser.add_argument('--screenshots', action='store_true',
                       help='Save screenshots for debugging')
    
    args = parser.parse_args()
    
    # Get credentials from args or environment
    email = args.email or os.environ.get('CRYPTORANK_EMAIL')
    password = args.password or os.environ.get('CRYPTORANK_PASSWORD')
    
    if not email or not password:
        logger.warning("No login credentials provided. Some data may not be accessible.")
        logger.warning("Set CRYPTORANK_EMAIL and CRYPTORANK_PASSWORD env vars or use --email/--password")
    
    # Initialize orchestrator
    orchestrator = FundingSyncOrchestrator(
        email=email,
        password=password,
        headless=not args.show_browser,
        save_screenshots=args.screenshots
    )
    
    # Run appropriate sync mode
    if args.company:
        # Scrape specific company
        await orchestrator.sync_company_detail(args.company)
    
    elif args.continuous:
        # Continuous mode
        await orchestrator.continuous_sync(
            pages=args.pages,
            interval_seconds=args.interval
        )
    
    else:
        # One-time sync
        await orchestrator.sync_funding_list(pages=args.pages)


if __name__ == '__main__':
    asyncio.run(main())


#!/usr/bin/env python3
# ABOUTME: Playwright-based scraper for cryptorank.io funding data
# ABOUTME: Extracts funding rounds, investors, and company metadata

"""
CryptoRank Funding Data Scraper

This module uses Playwright to scrape VC funding data from cryptorank.io.
It extracts:
- Funding rounds (date, amount, stage, investors)
- Investor details (name, website, social links)
- Company metadata (website, github, twitter, etc.)

Usage:
    python scripts/market_intelligence/cryptorank_scraper.py --pages 5
    python scripts/market_intelligence/cryptorank_scraper.py --company echodotxyz
"""

import asyncio
import argparse
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CryptoRankScraper:
    """Scrapes funding data from cryptorank.io"""
    
    BASE_URL = "https://cryptorank.io"
    FUNDING_LIST_URL = f"{BASE_URL}/funding-rounds?rows=50"
    
    def __init__(self, headless: bool = True, save_screenshots: bool = False):
        """
        Initialize scraper
        
        Args:
            headless: Run browser in headless mode
            save_screenshots: Save screenshots for debugging
        """
        self.headless = headless
        self.save_screenshots = save_screenshots
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        
        # Create output directory for screenshots if needed
        if save_screenshots:
            self.screenshot_dir = Path(__file__).parent / "screenshots"
            self.screenshot_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def start(self):
        """Start browser and create page"""
        logger.info("Starting Playwright browser...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        
        # Create context with realistic user agent
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        self.page = await self.context.new_page()
        logger.info("✅ Browser started")
    
    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("✅ Browser closed")
    
    async def login(self, email: str, password: str):
        """
        Login to cryptorank.io
        
        Args:
            email: User email
            password: User password
        """
        logger.info("Attempting login to cryptorank.io...")
        
        try:
            # Navigate to login page
            await self.page.goto(f"{self.BASE_URL}/login", wait_until='networkidle')
            
            # Fill login form
            await self.page.fill('input[type="email"]', email)
            await self.page.fill('input[type="password"]', password)
            
            # Click login button
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation
            await self.page.wait_for_url(self.BASE_URL, timeout=10000)
            
            logger.info("✅ Logged in successfully")
            
            if self.save_screenshots:
                await self.page.screenshot(path=self.screenshot_dir / "login_success.png")
        
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            if self.save_screenshots:
                await self.page.screenshot(path=self.screenshot_dir / "login_error.png")
            raise
    
    async def scrape_funding_list(self, pages: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape funding rounds list
        
        Args:
            pages: Number of pages to scrape (50 companies per page)
        
        Returns:
            List of funding round summaries
        """
        logger.info(f"Scraping funding list (first {pages} page(s))...")
        
        all_rounds = []
        
        for page_num in range(1, pages + 1):
            logger.info(f"Scraping page {page_num}/{pages}...")
            
            # Navigate to funding list
            url = f"{self.FUNDING_LIST_URL}&page={page_num}"
            await self.page.goto(url, wait_until='networkidle')
            
            # Wait for table to load
            await self.page.wait_for_selector('table tbody tr', timeout=10000)
            
            # Extract funding rounds from table
            rows = await self.page.query_selector_all('table tbody tr')
            logger.info(f"Found {len(rows)} funding rounds on page {page_num}")
            
            for idx, row in enumerate(rows, 1):
                try:
                    round_data = await self._extract_funding_row(row)
                    if round_data:
                        all_rounds.append(round_data)
                        logger.debug(f"  [{idx}] {round_data['company_name']} - ${round_data.get('amount', 'N/A')}")
                except Exception as e:
                    logger.warning(f"Failed to extract row {idx}: {e}")
                    continue
            
            # Add small delay between pages
            if page_num < pages:
                await asyncio.sleep(2)
        
        logger.info(f"✅ Scraped {len(all_rounds)} funding rounds from {pages} page(s)")
        return all_rounds
    
    async def _extract_funding_row(self, row) -> Optional[Dict[str, Any]]:
        """Extract data from a single table row"""
        try:
            # Get company name and link
            name_cell = await row.query_selector('td:nth-child(1) a')
            if not name_cell:
                return None
            
            company_name = await name_cell.text_content()
            company_link = await name_cell.get_attribute('href')
            
            # Extract cryptorank slug from URL (e.g., /ico/echodotxyz -> echodotxyz)
            cryptorank_slug = company_link.split('/')[-1] if company_link else None
            
            # Get funding amount
            amount_cell = await row.query_selector('td:nth-child(2)')
            amount_text = await amount_cell.text_content() if amount_cell else ""
            amount = self._parse_amount(amount_text.strip())
            
            # Get funding stage
            stage_cell = await row.query_selector('td:nth-child(3)')
            stage = await stage_cell.text_content() if stage_cell else ""
            stage = stage.strip()
            
            # Get date
            date_cell = await row.query_selector('td:nth-child(5)')
            date_text = await date_cell.text_content() if date_cell else ""
            announced_date = self._parse_date(date_text.strip())
            
            # Get lead investors (quick preview)
            investors_cell = await row.query_selector('td:nth-child(4)')
            investors_preview = []
            if investors_cell:
                investor_links = await investors_cell.query_selector_all('a')
                for inv_link in investor_links[:3]:  # First 3 investors
                    inv_name = await inv_link.text_content()
                    inv_href = await inv_link.get_attribute('href')
                    inv_slug = inv_href.split('/')[-1] if inv_href else None
                    investors_preview.append({
                        'name': inv_name.strip(),
                        'cryptorank_slug': inv_slug
                    })
            
            return {
                'company_name': company_name.strip(),
                'cryptorank_slug': cryptorank_slug,
                'amount_usd': amount,
                'round_stage': stage,
                'announced_date': announced_date,
                'investors_preview': investors_preview,
                'detail_url': f"{self.BASE_URL}{company_link}" if company_link else None
            }
        
        except Exception as e:
            logger.warning(f"Error extracting row: {e}")
            return None
    
    async def scrape_company_detail(self, cryptorank_slug: str) -> Dict[str, Any]:
        """
        Scrape detailed company information
        
        Args:
            cryptorank_slug: Company slug (e.g., 'echodotxyz')
        
        Returns:
            Detailed company data with funding rounds and social links
        """
        logger.info(f"Scraping company details: {cryptorank_slug}")
        
        company_data = {
            'cryptorank_slug': cryptorank_slug,
            'funding_rounds': [],
            'social_links': {},
            'metadata': {}
        }
        
        # Step 1: Scrape funding rounds from ICO page
        ico_url = f"{self.BASE_URL}/ico/{cryptorank_slug}"
        logger.info(f"  Visiting {ico_url}")
        
        try:
            await self.page.goto(ico_url, wait_until='networkidle', timeout=15000)
            
            # Extract funding rounds
            funding_rounds = await self._extract_funding_rounds()
            company_data['funding_rounds'] = funding_rounds
            logger.info(f"  Found {len(funding_rounds)} funding rounds")
            
            if self.save_screenshots:
                await self.page.screenshot(path=self.screenshot_dir / f"{cryptorank_slug}_funding.png")
        
        except PlaywrightTimeoutError:
            logger.warning(f"  Timeout on funding page for {cryptorank_slug}")
        except Exception as e:
            logger.warning(f"  Error scraping funding page: {e}")
        
        # Step 2: Scrape social links from overview page
        overview_url = f"{self.BASE_URL}/price/{cryptorank_slug}"
        logger.info(f"  Visiting {overview_url}")
        
        try:
            await self.page.goto(overview_url, wait_until='networkidle', timeout=15000)
            
            # Extract social links and metadata
            social_links = await self._extract_social_links()
            company_data['social_links'] = social_links
            logger.info(f"  Found {len(social_links)} social links")
            
            # Extract company metadata
            metadata = await self._extract_company_metadata()
            company_data['metadata'] = metadata
            
            if self.save_screenshots:
                await self.page.screenshot(path=self.screenshot_dir / f"{cryptorank_slug}_overview.png")
        
        except PlaywrightTimeoutError:
            logger.warning(f"  Timeout on overview page for {cryptorank_slug}")
        except Exception as e:
            logger.warning(f"  Error scraping overview page: {e}")
        
        logger.info(f"✅ Completed scraping {cryptorank_slug}")
        return company_data
    
    async def _extract_funding_rounds(self) -> List[Dict[str, Any]]:
        """Extract all funding rounds from ICO page"""
        funding_rounds = []
        
        try:
            # Wait for page to load
            await asyncio.sleep(2)
            
            # The funding rounds are typically displayed in a section
            # Let's try to find text patterns first
            page_text = await self.page.text_content('body')
            
            # Look for "Funding Rounds" heading and extract from there
            # Try to find by searching for stage types: Strategic, Seed, Series A, etc.
            
            # Get all text that might contain funding round info
            # Common pattern: Stage name, Date, Amount, Investors
            
            # Try finding specific elements
            # Look for round containers - they typically have stage, date, amount
            
            # Method 1: Look for elements containing round stages
            stage_keywords = ['Strategic', 'Seed', 'Series A', 'Series B', 'Private', 'M&A', 'Undisclosed', 'Pre-Seed']
            
            # Get all divs and check their text
            all_elements = await self.page.query_selector_all('div, section, article')
            
            for elem in all_elements:
                try:
                    text = await elem.text_content()
                    if not text:
                        continue
                    
                    text = text.strip()
                    
                    # Check if this might be a funding round container
                    # Look for stage keywords
                    round_stage = None
                    for keyword in stage_keywords:
                        if keyword in text and len(text) < 500:  # Not too long
                            round_stage = keyword
                            break
                    
                    if not round_stage:
                        continue
                    
                    # Try to extract round info
                    round_data = {'round_stage': round_stage}
                    
                    # Look for date pattern (e.g., "21 Oct 2025")
                    date_match = re.search(r'(\d{1,2}\s+\w{3}(?:\s+\d{4})?)', text)
                    if date_match:
                        round_data['announced_date'] = self._parse_date(date_match.group(1))
                    
                    # Look for amount pattern (e.g., "$ 5.00M")
                    amount_match = re.search(r'\$\s*([\d.]+)\s*([MKB])?', text)
                    if amount_match:
                        round_data['amount_usd'] = self._parse_amount(amount_match.group(0))
                    
                    # Look for investors - links to /funds/
                    investor_links = await elem.query_selector_all('a[href*="/funds/"]')
                    investors = []
                    
                    for inv_link in investor_links:
                        inv_name = await inv_link.text_content()
                        inv_href = await inv_link.get_attribute('href')
                        inv_slug = inv_href.split('/')[-1].replace('/rounds', '') if inv_href else None
                        
                        # Check if marked as Lead
                        parent_text = text
                        is_lead = 'Lead' in parent_text and inv_name in parent_text[:parent_text.index('Lead') + 50]
                        
                        if inv_name and inv_name.strip():
                            investors.append({
                                'name': inv_name.strip(),
                                'cryptorank_slug': inv_slug,
                                'role': 'lead' if is_lead else 'participant'
                            })
                    
                    if investors:
                        round_data['investors'] = investors
                    
                    # Only add if we have at least stage and date or amount
                    if 'announced_date' in round_data or 'amount_usd' in round_data:
                        funding_rounds.append(round_data)
                        logger.debug(f"  Extracted round: {round_stage}, ${round_data.get('amount_usd', 'N/A')}")
                
                except Exception as e:
                    continue
        
        except Exception as e:
            logger.warning(f"Error extracting funding rounds: {e}")
        
        # Deduplicate rounds (sometimes we catch the same round multiple times)
        unique_rounds = []
        seen = set()
        for round_data in funding_rounds:
            key = (
                round_data.get('round_stage'),
                round_data.get('announced_date'),
                round_data.get('amount_usd')
            )
            if key not in seen:
                seen.add(key)
                unique_rounds.append(round_data)
        
        return unique_rounds
    
    async def _extract_social_links(self) -> Dict[str, str]:
        """Extract social media links from overview page"""
        social_links = {}
        
        try:
            # Look for social links section
            # Common patterns: look for links with social media domains
            all_links = await self.page.query_selector_all('a[href]')
            
            for link in all_links:
                href = await link.get_attribute('href')
                if not href:
                    continue
                
                # Check for common social platforms
                if 'twitter.com' in href or 'x.com' in href:
                    social_links['twitter_url'] = href
                elif 'github.com' in href:
                    social_links['github_url'] = href
                elif 'linkedin.com' in href:
                    social_links['linkedin_url'] = href
                elif 'telegram.org' in href or 't.me' in href:
                    social_links['telegram_url'] = href
                elif 'discord' in href:
                    social_links['discord_url'] = href
                elif not any(x in href for x in ['cryptorank', 'facebook', 'instagram', 'youtube']) and \
                     (href.startswith('http://') or href.startswith('https://')) and \
                     'website_url' not in social_links:
                    # Likely company website (first non-social link)
                    social_links['website_url'] = href
        
        except Exception as e:
            logger.warning(f"Error extracting social links: {e}")
        
        return social_links
    
    async def _extract_company_metadata(self) -> Dict[str, Any]:
        """Extract company metadata (description, etc.)"""
        metadata = {}
        
        try:
            # Extract company name
            name_elem = await self.page.query_selector('h1')
            if name_elem:
                metadata['company_name'] = (await name_elem.text_content()).strip()
            
            # Extract description
            desc_elem = await self.page.query_selector('meta[name="description"]')
            if desc_elem:
                metadata['description'] = await desc_elem.get_attribute('content')
        
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return metadata
    
    @staticmethod
    def _parse_amount(amount_text: str) -> Optional[float]:
        """Parse funding amount from text (e.g., '$10.5M' -> 10500000)"""
        if not amount_text or amount_text == 'N/A':
            return None
        
        # Remove $ and whitespace
        amount_text = amount_text.replace('$', '').replace(',', '').strip()
        
        # Handle M (millions) and K (thousands)
        multiplier = 1
        if 'M' in amount_text:
            multiplier = 1_000_000
            amount_text = amount_text.replace('M', '')
        elif 'K' in amount_text:
            multiplier = 1_000
            amount_text = amount_text.replace('K', '')
        elif 'B' in amount_text:
            multiplier = 1_000_000_000
            amount_text = amount_text.replace('B', '')
        
        try:
            return float(amount_text) * multiplier
        except ValueError:
            return None
    
    @staticmethod
    def _parse_date(date_text: str) -> Optional[str]:
        """Parse date from text to ISO format"""
        if not date_text or date_text == 'N/A':
            return None
        
        # Common formats: "24 Oct", "Oct 24", "24 Oct 2024", etc.
        try:
            # Try various date formats
            for fmt in ['%d %b %Y', '%d %b', '%b %d %Y', '%b %d']:
                try:
                    dt = datetime.strptime(date_text, fmt)
                    # If year is not in string, use current year
                    if '%Y' not in fmt:
                        dt = dt.replace(year=datetime.now().year)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scrape funding data from cryptorank.io')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
    parser.add_argument('--company', type=str, help='Scrape specific company by slug')
    parser.add_argument('--email', type=str, help='Login email (if required)')
    parser.add_argument('--password', type=str, help='Login password (if required)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--show-browser', action='store_true', help='Show browser (opposite of headless)')
    parser.add_argument('--screenshots', action='store_true', help='Save screenshots for debugging')
    parser.add_argument('--output', type=str, help='Output JSON file')
    
    args = parser.parse_args()
    
    # Override headless if --show-browser
    if args.show_browser:
        args.headless = False
    
    # Initialize scraper
    async with CryptoRankScraper(headless=args.headless, save_screenshots=args.screenshots) as scraper:
        results = {}
        
        # Login if credentials provided
        if args.email and args.password:
            await scraper.login(args.email, args.password)
        
        # Scrape specific company
        if args.company:
            company_data = await scraper.scrape_company_detail(args.company)
            results['company_data'] = company_data
        
        # Scrape funding list
        else:
            funding_list = await scraper.scrape_funding_list(pages=args.pages)
            results['funding_list'] = funding_list
            results['total_companies'] = len(funding_list)
        
        # Save results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"✅ Results saved to {output_path}")
        else:
            print(json.dumps(results, indent=2))


if __name__ == '__main__':
    asyncio.run(main())


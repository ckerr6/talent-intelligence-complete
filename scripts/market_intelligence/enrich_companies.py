#!/usr/bin/env python3
# ABOUTME: Enrich specific companies with detailed funding and social data
# ABOUTME: Takes company slugs and visits their detail pages

"""
Selective Company Enrichment

Enriches specific companies by visiting their detail pages to get:
- All funding rounds (not just the preview)
- Complete investor lists with roles
- Social media links (Twitter, GitHub, LinkedIn, etc.)

Usage:
    python enrich_companies.py slug1 slug2 slug3
    python enrich_companies.py --from-db --min-amount 1000000
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cryptorank_scraper import CryptoRankScraper
from funding_ingestion import FundingIngestion
from config import get_db_context


async def enrich_companies(slugs: list[str]):
    """Enrich specific companies with full details"""
    print(f"Enriching {len(slugs)} companies...")
    
    async with CryptoRankScraper(headless=True, use_saved_session=True) as scraper:
        ingestion = FundingIngestion()
        
        for idx, slug in enumerate(slugs, 1):
            try:
                print(f"\n[{idx}/{len(slugs)}] Enriching {slug}...")
                
                # Scrape full company details
                company_data = await scraper.scrape_company_detail(slug)
                
                # Get company name from database
                with get_db_context() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT company_name FROM company
                        WHERE cryptorank_slug = %s
                    """, (slug,))
                    result = cursor.fetchone()
                    if result:
                        company_data['company_name'] = result['company_name']
                
                # Store in database
                result = ingestion.store_funding_round(company_data)
                
                print(f"  ✅ Stored: {result['round_created']} rounds, {result['investors_created']} investors")
                
                # Small delay between companies
                await asyncio.sleep(2)
            
            except Exception as e:
                print(f"  ❌ Error enriching {slug}: {e}")
                continue
    
    print(f"\n✅ Enrichment complete!")


def get_companies_to_enrich(min_amount: float = None, max_count: int = None):
    """Get list of companies from database that need enrichment"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT c.cryptorank_slug, c.company_name, MAX(cfr.amount_usd) as max_amount
            FROM company c
            JOIN company_funding_round cfr ON c.company_id = cfr.company_id
            WHERE c.cryptorank_slug IS NOT NULL
              AND cfr.source = 'cryptorank'
        """
        
        params = []
        if min_amount:
            query += " AND cfr.amount_usd >= %s"
            params.append(min_amount)
        
        query += """
            GROUP BY c.cryptorank_slug, c.company_name
            ORDER BY max_amount DESC NULLS LAST
        """
        
        if max_count:
            query += f" LIMIT {max_count}"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return [r['cryptorank_slug'] for r in results]


async def main():
    parser = argparse.ArgumentParser(description='Enrich companies with detailed funding data')
    parser.add_argument('slugs', nargs='*', help='Company slugs to enrich')
    parser.add_argument('--from-db', action='store_true',
                       help='Get companies from database')
    parser.add_argument('--min-amount', type=float,
                       help='Minimum funding amount (when using --from-db)')
    parser.add_argument('--max-count', type=int, default=50,
                       help='Maximum number of companies to enrich (default: 50)')
    
    args = parser.parse_args()
    
    # Get slugs either from command line or database
    if args.from_db:
        print("Fetching companies from database...")
        slugs = get_companies_to_enrich(
            min_amount=args.min_amount,
            max_count=args.max_count
        )
        print(f"Found {len(slugs)} companies to enrich")
        
        if not slugs:
            print("No companies found matching criteria")
            return
        
        # Show what we'll enrich
        print("\nCompanies to enrich:")
        for i, slug in enumerate(slugs[:10], 1):
            print(f"  {i}. {slug}")
        if len(slugs) > 10:
            print(f"  ... and {len(slugs) - 10} more")
        print()
    
    elif args.slugs:
        slugs = args.slugs
    
    else:
        print("Error: Provide either company slugs or use --from-db")
        parser.print_help()
        return
    
    # Enrich companies
    await enrich_companies(slugs)


if __name__ == '__main__':
    asyncio.run(main())


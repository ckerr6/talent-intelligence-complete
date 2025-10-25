#!/usr/bin/env python3
# ABOUTME: Data ingestion module for cryptorank funding data
# ABOUTME: Stores scraped funding rounds and investors into PostgreSQL database

"""
Funding Data Ingestion

This module handles storing scraped funding data from cryptorank.io
into the PostgreSQL database. It:
- Creates/updates investor records
- Creates/updates company funding rounds
- Matches companies to existing database records
- Updates company social links

Usage:
    from funding_ingestion import FundingIngestion
    
    ingestion = FundingIngestion()
    ingestion.store_funding_round(funding_data)
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, date
import json

from config import get_db_context, Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FundingIngestion:
    """Handles ingestion of funding data into database"""
    
    def __init__(self):
        """Initialize ingestion handler"""
        pass
    
    def store_funding_list(self, funding_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Store a list of funding rounds
        
        Args:
            funding_list: List of funding round data from scraper
        
        Returns:
            Statistics about what was stored
        """
        stats = {
            'companies_created': 0,
            'companies_updated': 0,
            'rounds_created': 0,
            'rounds_updated': 0,
            'investors_created': 0
        }
        
        for funding_data in funding_list:
            try:
                result = self.store_funding_round(funding_data)
                
                if result['company_created']:
                    stats['companies_created'] += 1
                elif result['company_updated']:
                    stats['companies_updated'] += 1
                
                if result['round_created']:
                    stats['rounds_created'] += 1
                elif result['round_updated']:
                    stats['rounds_updated'] += 1
                
                stats['investors_created'] += result['investors_created']
            
            except Exception as e:
                logger.error(f"Error storing funding data for {funding_data.get('company_name')}: {e}")
                continue
        
        logger.info(f"Ingestion complete: {stats}")
        return stats
    
    def store_funding_round(self, funding_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a single funding round
        
        Args:
            funding_data: Funding round data from scraper
        
        Returns:
            Dictionary with what was created/updated
        """
        result = {
            'company_created': False,
            'company_updated': False,
            'round_created': False,
            'round_updated': False,
            'investors_created': 0
        }
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Step 1: Get or create company
            company_id = self._get_or_create_company(
                cursor,
                company_name=funding_data.get('company_name'),
                cryptorank_slug=funding_data.get('cryptorank_slug'),
                social_links=funding_data.get('social_links', {}),
                metadata=funding_data.get('metadata', {})
            )
            
            if not company_id:
                logger.warning(f"Could not create/find company: {funding_data.get('company_name')}")
                return result
            
            result['company_created'] = True  # Simplified for now
            
            # Step 2: Process investors
            investor_ids = []
            investors_data = funding_data.get('investors_preview', [])
            if 'funding_rounds' in funding_data and funding_data['funding_rounds']:
                # If we have detailed funding rounds, use those investors
                for round_data in funding_data['funding_rounds']:
                    investors_data.extend(round_data.get('investors', []))
            
            for investor_data in investors_data:
                investor_id = self._get_or_create_investor(cursor, investor_data)
                if investor_id:
                    investor_ids.append({
                        'investor_id': str(investor_id),
                        'role': investor_data.get('role', 'participant'),
                        'name': investor_data.get('name')
                    })
                    result['investors_created'] += 1
            
            # Step 3: Store funding round(s)
            if 'funding_rounds' in funding_data and funding_data['funding_rounds']:
                # Detailed funding rounds from company detail page
                for round_data in funding_data['funding_rounds']:
                    round_id = self._create_or_update_funding_round(
                        cursor,
                        company_id=company_id,
                        round_data=round_data,
                        investor_ids=investor_ids
                    )
                    if round_id:
                        result['round_created'] = True
            else:
                # Single funding round from list view
                round_id = self._create_or_update_funding_round(
                    cursor,
                    company_id=company_id,
                    round_data=funding_data,
                    investor_ids=investor_ids
                )
                if round_id:
                    result['round_created'] = True
            
            conn.commit()
        
        return result
    
    def _get_or_create_company(
        self,
        cursor,
        company_name: str,
        cryptorank_slug: Optional[str] = None,
        social_links: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Get existing company or create new one
        
        Returns company_id
        """
        if not company_name:
            return None
        
        social_links = social_links or {}
        metadata = metadata or {}
        
        # Try to find existing company by cryptorank_slug
        if cryptorank_slug:
            cursor.execute("""
                SELECT company_id FROM company
                WHERE cryptorank_slug = %s
            """, (cryptorank_slug,))
            
            result = cursor.fetchone()
            if result:
                company_id = result['company_id']
                
                # Update social links if provided
                if social_links:
                    self._update_company_social_links(cursor, company_id, social_links)
                
                return company_id
        
        # Try to find by name (case insensitive)
        cursor.execute("""
            SELECT company_id FROM company
            WHERE LOWER(company_name) = LOWER(%s)
            LIMIT 1
        """, (company_name,))
        
        result = cursor.fetchone()
        if result:
            company_id = result['company_id']
            
            # Update cryptorank_slug if we have it
            if cryptorank_slug:
                cursor.execute("""
                    UPDATE company
                    SET cryptorank_slug = %s
                    WHERE company_id = %s
                """, (cryptorank_slug, company_id))
            
            # Update social links
            if social_links:
                self._update_company_social_links(cursor, company_id, social_links)
            
            return company_id
        
        # Create new company
        company_id = uuid4()
        
        # Extract domain from website URL if available
        website_url = social_links.get('website_url')
        company_domain = self._extract_domain(website_url) if website_url else company_name.lower().replace(' ', '')
        
        cursor.execute("""
            INSERT INTO company (
                company_id,
                company_domain,
                company_name,
                website_url,
                linkedin_url,
                twitter_url,
                github_url,
                telegram_url,
                discord_url,
                cryptorank_slug
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (company_domain) DO UPDATE
            SET
                company_name = COALESCE(EXCLUDED.company_name, company.company_name),
                website_url = COALESCE(EXCLUDED.website_url, company.website_url),
                linkedin_url = COALESCE(EXCLUDED.linkedin_url, company.linkedin_url),
                twitter_url = COALESCE(EXCLUDED.twitter_url, company.twitter_url),
                github_url = COALESCE(EXCLUDED.github_url, company.github_url),
                telegram_url = COALESCE(EXCLUDED.telegram_url, company.telegram_url),
                discord_url = COALESCE(EXCLUDED.discord_url, company.discord_url),
                cryptorank_slug = COALESCE(EXCLUDED.cryptorank_slug, company.cryptorank_slug)
            RETURNING company_id
        """, (
            company_id,
            company_domain,
            company_name,
            social_links.get('website_url'),
            social_links.get('linkedin_url'),
            social_links.get('twitter_url'),
            social_links.get('github_url'),
            social_links.get('telegram_url'),
            social_links.get('discord_url'),
            cryptorank_slug
        ))
        
        result = cursor.fetchone()
        return result['company_id'] if result else company_id
    
    def _update_company_social_links(self, cursor, company_id: UUID, social_links: Dict[str, str]):
        """Update social media links for a company"""
        if not social_links:
            return
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        for field in ['website_url', 'linkedin_url', 'twitter_url', 'github_url', 'telegram_url', 'discord_url']:
            if field in social_links and social_links[field]:
                update_fields.append(f"{field} = COALESCE({field}, %s)")
                params.append(social_links[field])
        
        if update_fields:
            params.append(company_id)
            query = f"""
                UPDATE company
                SET {', '.join(update_fields)}
                WHERE company_id = %s
            """
            cursor.execute(query, tuple(params))
    
    def _get_or_create_investor(self, cursor, investor_data: Dict[str, Any]) -> Optional[UUID]:
        """
        Get existing investor or create new one
        
        Returns investor_id
        """
        if not investor_data or not investor_data.get('name'):
            return None
        
        investor_name = investor_data['name']
        cryptorank_slug = investor_data.get('cryptorank_slug')
        
        # Try to find existing investor
        if cryptorank_slug:
            cursor.execute("""
                SELECT investor_id FROM investor
                WHERE cryptorank_slug = %s
            """, (cryptorank_slug,))
            
            result = cursor.fetchone()
            if result:
                return result['investor_id']
        
        # Try by name
        cursor.execute("""
            SELECT investor_id FROM investor
            WHERE LOWER(investor_name) = LOWER(%s)
            LIMIT 1
        """, (investor_name,))
        
        result = cursor.fetchone()
        if result:
            # Update cryptorank_slug if we have it
            if cryptorank_slug:
                cursor.execute("""
                    UPDATE investor
                    SET cryptorank_slug = %s
                    WHERE investor_id = %s AND cryptorank_slug IS NULL
                """, (cryptorank_slug, result['investor_id']))
            
            return result['investor_id']
        
        # Create new investor
        investor_id = uuid4()
        
        cursor.execute("""
            INSERT INTO investor (
                investor_id,
                investor_name,
                cryptorank_slug
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (cryptorank_slug) DO UPDATE
            SET investor_name = EXCLUDED.investor_name
            RETURNING investor_id
        """, (investor_id, investor_name, cryptorank_slug))
        
        result = cursor.fetchone()
        return result['investor_id'] if result else investor_id
    
    def _create_or_update_funding_round(
        self,
        cursor,
        company_id: UUID,
        round_data: Dict[str, Any],
        investor_ids: List[Dict[str, Any]]
    ) -> Optional[UUID]:
        """Create or update a funding round"""
        
        # Check if round already exists
        cryptorank_slug = round_data.get('cryptorank_slug')
        announced_date = round_data.get('announced_date')
        round_stage = round_data.get('round_stage')
        
        # Try to find existing round
        if cryptorank_slug and announced_date and round_stage:
            cursor.execute("""
                SELECT round_id FROM company_funding_round
                WHERE company_id = %s
                AND cryptorank_slug = %s
                AND announced_date = %s
                AND round_stage = %s
            """, (company_id, cryptorank_slug, announced_date, round_stage))
            
            result = cursor.fetchone()
            if result:
                # Update existing round
                round_id = result['round_id']
                
                cursor.execute("""
                    UPDATE company_funding_round
                    SET
                        amount_usd = COALESCE(%s, amount_usd),
                        valuation_usd = COALESCE(%s, valuation_usd),
                        investors = %s,
                        updated_at = NOW()
                    WHERE round_id = %s
                """, (
                    round_data.get('amount_usd'),
                    round_data.get('valuation_usd'),
                    json.dumps(investor_ids) if investor_ids else '[]',
                    round_id
                ))
                
                return round_id
        
        # Create new round
        round_id = uuid4()
        
        cursor.execute("""
            INSERT INTO company_funding_round (
                round_id,
                company_id,
                round_type,
                round_stage,
                announced_date,
                amount_usd,
                valuation_usd,
                investors,
                cryptorank_slug,
                source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING round_id
        """, (
            round_id,
            company_id,
            round_data.get('round_type'),
            round_stage,
            announced_date,
            round_data.get('amount_usd'),
            round_data.get('valuation_usd'),
            json.dumps(investor_ids) if investor_ids else '[]',
            cryptorank_slug,
            'cryptorank'
        ))
        
        result = cursor.fetchone()
        return result['round_id'] if result else round_id
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        
        # Remove protocol
        domain = url.replace('https://', '').replace('http://', '').replace('www.', '')
        
        # Remove path
        domain = domain.split('/')[0]
        
        return domain.lower()


def main():
    """Test the ingestion module"""
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python funding_ingestion.py <scraped_data.json>")
        sys.exit(1)
    
    # Load scraped data
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
    
    # Initialize ingestion
    ingestion = FundingIngestion()
    
    # Store funding list
    if 'funding_list' in data:
        stats = ingestion.store_funding_list(data['funding_list'])
        print(f"✅ Ingestion complete: {stats}")
    
    # Store company data
    elif 'company_data' in data:
        result = ingestion.store_funding_round(data['company_data'])
        print(f"✅ Company data stored: {result}")


if __name__ == '__main__':
    main()


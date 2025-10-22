#!/usr/bin/env python3
"""
Crypto Ecosystem Importer

Imports ecosystem data from Electric Capital's crypto-ecosystems export
and matches to companies in our database.

Usage:
    # Import all ecosystems
    python3 crypto_ecosystem_importer.py /tmp/all_ecosystems.jsonl
    
    # Import only priority ecosystems
    python3 crypto_ecosystem_importer.py /tmp/all_ecosystems.jsonl --priority-only
    
    # Dry run (don't write to database)
    python3 crypto_ecosystem_importer.py /tmp/all_ecosystems.jsonl --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import re

sys.path.insert(0, str(Path(__file__).parent))

from config import Config, get_db_connection
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Priority ecosystems to import first
PRIORITY_ECOSYSTEMS = {
    # Major protocols
    'ethereum', 'uniswap', 'avalanche', 'solana', 'polygon', 'arbitrum',
    'optimism', 'base', 'polkadot', 'cosmos', 'near', 'sui', 'aptos',
    
    # VC portfolios (we'll look for these patterns)
    'paradigm', 'a16z', 'coinbase', 'haun', 'variant', 'dragonfly',
    'polychain', 'pantera', 'multicoin', 'electric capital',
    
    # Exchanges/Infrastructure
    'binance', 'kraken', 'gemini', 'circle', 'chainlink', 'the graph',
    
    # DeFi protocols
    'aave', 'compound', 'makerdao', 'curve', 'balancer', 'yearn',
    'synthetix', 'lido', 'rocket pool',
    
    # NFT/Gaming
    'opensea', 'blur', 'rarible', 'ens', 'lens protocol',
}


class EcosystemImporter:
    """Imports ecosystem data and matches to companies"""
    
    def __init__(self, conn, dry_run: bool = False):
        self.conn = conn
        self.cursor = conn.cursor()
        self.dry_run = dry_run
        
        # Stats
        self.stats = {
            'total_repos': 0,
            'unique_ecosystems': 0,
            'ecosystems_imported': 0,
            'repos_linked': 0,
            'companies_matched': 0,
            'skipped_duplicate_repos': 0,
        }
        
        # Cache
        self.ecosystem_cache = {}  # name -> ecosystem_id
        self.company_cache = {}  # normalized_name -> company_id
        self.repo_cache = {}  # full_name -> repo_id
        
        # Load existing data
        self._load_companies()
        self._load_ecosystems()
        self._load_repos()
    
    def _load_companies(self):
        """Load existing companies into cache"""
        logger.info("Loading companies from database...")
        self.cursor.execute("""
            SELECT company_id::text, company_name, company_domain, 
                   LOWER(company_name) as normalized_name
            FROM company
        """)
        
        for row in self.cursor.fetchall():
            normalized = self._normalize_name(row['company_name'])
            if normalized:
                self.company_cache[normalized] = {
                    'id': row['company_id'],
                    'name': row['company_name'],
                    'domain': row['company_domain']
                }
        
        logger.info(f"Loaded {len(self.company_cache)} companies")
    
    def _load_ecosystems(self):
        """Load existing ecosystems into cache"""
        self.cursor.execute("""
            SELECT ecosystem_id::text, ecosystem_name, normalized_name
            FROM crypto_ecosystem
        """)
        
        for row in self.cursor.fetchall():
            self.ecosystem_cache[row['ecosystem_name']] = row['ecosystem_id']
        
        logger.info(f"Loaded {len(self.ecosystem_cache)} existing ecosystems")
    
    def _load_repos(self):
        """Load existing repositories into cache"""
        self.cursor.execute("""
            SELECT repo_id::text, full_name, owner_username, repo_name
            FROM github_repository
        """)
        
        for row in self.cursor.fetchall():
            self.repo_cache[row['full_name'].lower()] = row['repo_id']
        
        logger.info(f"Loaded {len(self.repo_cache)} existing repos")
    
    def _normalize_name(self, name: str) -> Optional[str]:
        """Normalize ecosystem/company name for matching"""
        if not name:
            return None
        
        # Convert to lowercase
        name = name.lower().strip()
        
        # Remove common suffixes
        name = re.sub(r'\s+(labs?|inc\.?|llc|ltd\.?|foundation|protocol|network|ventures?|capital|crypto)$', '', name)
        
        # Remove special characters but keep spaces
        name = re.sub(r'[^a-z0-9\s]', '', name)
        
        # Collapse multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name if name else None
    
    def _extract_owner_repo(self, repo_url: str) -> Optional[Tuple[str, str]]:
        """Extract owner and repo name from GitHub URL"""
        # Handle various GitHub URL formats
        match = re.search(r'github\.com[/:]([^/]+)/([^/\.]+)', repo_url)
        if match:
            owner = match.group(1)
            repo = match.group(2)
            return (owner, repo)
        return None
    
    def _is_priority_ecosystem(self, eco_name: str) -> bool:
        """Check if this ecosystem is in the priority list"""
        normalized = self._normalize_name(eco_name)
        if not normalized:
            return False
        
        # Check if any priority keyword appears in the ecosystem name
        for priority in PRIORITY_ECOSYSTEMS:
            if priority in normalized or normalized in priority:
                return True
        
        return False
    
    def _get_or_create_ecosystem(self, eco_name: str, ecosystem_type: Optional[str] = None) -> Optional[str]:
        """Get existing or create new ecosystem"""
        # Check cache first
        if eco_name in self.ecosystem_cache:
            return self.ecosystem_cache[eco_name]
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create ecosystem: {eco_name}")
            return None
        
        # Create new ecosystem
        normalized = self._normalize_name(eco_name)
        
        # Try to infer ecosystem type from name
        if not ecosystem_type:
            name_lower = eco_name.lower()
            if any(x in name_lower for x in ['ventures', 'capital', 'labs', 'fund']):
                ecosystem_type = 'vc_portfolio'
            elif any(x in name_lower for x in ['protocol', 'network', 'chain']):
                ecosystem_type = 'protocol'
            elif any(x in name_lower for x in ['exchange', 'dex', 'swap']):
                ecosystem_type = 'exchange'
            elif any(x in name_lower for x in ['nft', 'token', 'dao']):
                ecosystem_type = 'dao_nft'
            else:
                ecosystem_type = 'other'
        
        self.cursor.execute("""
            INSERT INTO crypto_ecosystem (ecosystem_name, normalized_name, ecosystem_type)
            VALUES (%s, %s, %s)
            RETURNING ecosystem_id::text
        """, (eco_name, normalized, ecosystem_type))
        
        ecosystem_id = self.cursor.fetchone()['ecosystem_id']
        self.ecosystem_cache[eco_name] = ecosystem_id
        self.stats['ecosystems_imported'] += 1
        
        logger.debug(f"Created ecosystem: {eco_name} ({ecosystem_id})")
        return ecosystem_id
    
    def _batch_create_repos(self, repos_list: List[Tuple[str, str]]) -> Dict[str, str]:
        """Batch create repositories and return mapping of full_name -> repo_id"""
        import time
        
        if not repos_list or self.dry_run:
            return {}
        
        # Prepare values for batch insert
        start_time = time.time()
        values_to_insert = []
        for owner, repo_name in repos_list:
            full_name = f"{owner}/{repo_name}"
            full_name_lower = full_name.lower()
            
            # Skip if already in cache
            if full_name_lower not in self.repo_cache:
                values_to_insert.append((full_name, owner, repo_name))
        
        if not values_to_insert:
            logger.info(f"    All {len(repos_list):,} repos already in cache")
            return {}
        
        logger.info(f"    Inserting {len(values_to_insert):,} new repos (skipped {len(repos_list) - len(values_to_insert):,} cached)...")
        
        # Batch insert in chunks to avoid memory issues
        from psycopg2.extras import execute_values
        CHUNK_SIZE = 1000
        
        for i in range(0, len(values_to_insert), CHUNK_SIZE):
            chunk = values_to_insert[i:i + CHUNK_SIZE]
            if i % 5000 == 0 and i > 0:
                logger.info(f"      Progress: {i:,}/{len(values_to_insert):,} repos inserted...")
            
            self.cursor.execute("BEGIN")
            execute_values(
                self.cursor,
                """
                INSERT INTO github_repository (full_name, owner_username, repo_name)
                VALUES %s
                ON CONFLICT (full_name) DO NOTHING
                """,
                chunk,
                template="(%s, %s, %s)"
            )
            self.cursor.execute("COMMIT")
        
        insert_time = time.time() - start_time
        logger.info(f"    ✅ Inserted {len(values_to_insert):,} repos in {insert_time:.1f}s ({len(values_to_insert)/insert_time:.0f} repos/sec)")
        
        # Now fetch all repo IDs for the inserted/existing repos
        logger.info(f"    Fetching repo IDs...")
        fetch_start = time.time()
        full_names = [v[0].lower() for v in values_to_insert]
        self.cursor.execute("""
            SELECT repo_id::text, LOWER(full_name) as full_name_lower
            FROM github_repository
            WHERE LOWER(full_name) = ANY(%s)
        """, (full_names,))
        
        new_mappings = {}
        for row in self.cursor.fetchall():
            self.repo_cache[row['full_name_lower']] = row['repo_id']
            new_mappings[row['full_name_lower']] = row['repo_id']
        
        fetch_time = time.time() - fetch_start
        logger.info(f"    ✅ Fetched {len(new_mappings):,} repo IDs in {fetch_time:.1f}s")
        
        return new_mappings
    
    def _link_ecosystem_repo(self, ecosystem_id: str, repo_id: str, tags: List[str]):
        """Link ecosystem to repository"""
        if self.dry_run:
            return
        
        self.cursor.execute("""
            INSERT INTO ecosystem_repository (ecosystem_id, repo_id, tags)
            VALUES (%s::uuid, %s::uuid, %s)
            ON CONFLICT (ecosystem_id, repo_id) DO UPDATE SET
                tags = EXCLUDED.tags,
                updated_at = NOW()
        """, (ecosystem_id, repo_id, tags))
        
        self.stats['repos_linked'] += 1
    
    def _match_company_to_ecosystem(self, ecosystem_id: str, eco_name: str):
        """Try to match ecosystem to a company"""
        normalized = self._normalize_name(eco_name)
        if not normalized:
            return
        
        # Check if we have a matching company
        if normalized in self.company_cache:
            company = self.company_cache[normalized]
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would link company '{company['name']}' to ecosystem '{eco_name}'")
                return
            
            # Link company to ecosystem
            self.cursor.execute("""
                INSERT INTO company_ecosystem (company_id, ecosystem_id, relationship_type, confidence_score, source)
                VALUES (%s::uuid, %s::uuid, %s, %s, %s)
                ON CONFLICT (company_id, ecosystem_id, relationship_type) DO UPDATE SET
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = NOW()
            """, (company['id'], ecosystem_id, 'owner', 0.85, 'crypto-ecosystems-name-match'))
            
            self.stats['companies_matched'] += 1
            logger.info(f"✅ Matched company '{company['name']}' to ecosystem '{eco_name}'")
    
    def import_ecosystems(self, jsonl_file: Path, priority_only: bool = False):
        """Import ecosystems from JSONL file"""
        logger.info(f"Starting import from {jsonl_file}")
        logger.info(f"Priority only: {priority_only}")
        logger.info(f"Dry run: {self.dry_run}")
        
        # First pass: collect all unique ecosystems
        ecosystems_data = defaultdict(list)
        
        with open(jsonl_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 10000 == 0:
                    logger.info(f"Processing line {line_num:,}...")
                
                try:
                    entry = json.loads(line)
                    eco_name = entry.get('eco_name')
                    repo_url = entry.get('repo_url')
                    tags = entry.get('tags', [])
                    branch = entry.get('branch', [])
                    
                    if not eco_name or not repo_url:
                        continue
                    
                    self.stats['total_repos'] += 1
                    
                    # Filter by priority if requested
                    if priority_only and not self._is_priority_ecosystem(eco_name):
                        continue
                    
                    ecosystems_data[eco_name].append({
                        'repo_url': repo_url,
                        'tags': tags,
                        'branch': branch
                    })
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
                    continue
        
        self.stats['unique_ecosystems'] = len(ecosystems_data)
        logger.info(f"Found {self.stats['unique_ecosystems']:,} unique ecosystems")
        logger.info(f"Processing {len(ecosystems_data):,} ecosystems...")
        
        # Second pass: import ecosystems and repos
        for eco_num, (eco_name, repos) in enumerate(ecosystems_data.items(), 1):
            logger.info(f"Processing ecosystem {eco_num}/{len(ecosystems_data)}: {eco_name} ({len(repos):,} repos)")
            
            # Create ecosystem
            ecosystem_id = self._get_or_create_ecosystem(eco_name)
            if not ecosystem_id:
                continue
            
            # Try to match to company
            self._match_company_to_ecosystem(ecosystem_id, eco_name)
            
            # Collect all repos to create in batch
            repos_to_create = []
            repo_tags_map = {}  # full_name_lower -> tags
            
            for repo_data in repos:
                repo_url = repo_data['repo_url']
                tags = repo_data['tags']
                
                # Extract owner/repo
                parts = self._extract_owner_repo(repo_url)
                if not parts:
                    continue
                
                owner, repo_name = parts
                full_name_lower = f"{owner}/{repo_name}".lower()
                
                repos_to_create.append((owner, repo_name))
                repo_tags_map[full_name_lower] = tags
            
            # Batch create repos
            logger.info(f"  Creating {len(repos_to_create):,} repos...")
            self._batch_create_repos(repos_to_create)
            
            # Now link all repos to ecosystem (batch)
            import time
            link_start = time.time()
            logger.info(f"  Linking repos to ecosystem...")
            links_to_create = []
            for full_name_lower, tags in repo_tags_map.items():
                repo_id = self.repo_cache.get(full_name_lower)
                if repo_id:
                    links_to_create.append((ecosystem_id, repo_id, tags))
            
            if links_to_create and not self.dry_run:
                from psycopg2.extras import execute_values
                execute_values(
                    self.cursor,
                    """
                    INSERT INTO ecosystem_repository (ecosystem_id, repo_id, tags)
                    VALUES %s
                    ON CONFLICT (ecosystem_id, repo_id) DO UPDATE SET
                        tags = EXCLUDED.tags,
                        updated_at = NOW()
                    """,
                    links_to_create,
                    template="(%s::uuid, %s::uuid, %s)"
                )
                self.stats['repos_linked'] += len(links_to_create)
            
            link_time = time.time() - link_start
            logger.info(f"  ✅ Linked {len(links_to_create):,} repos to {eco_name} in {link_time:.1f}s")
            
            # Commit after each ecosystem to avoid long transactions
            if not self.dry_run:
                self.conn.commit()
                logger.info(f"  Committed ecosystem {eco_name}")
        
        if not self.dry_run:
            self.conn.commit()
            logger.info("✅ Committed all changes")
    
    def print_stats(self):
        """Print import statistics"""
        print("\n" + "=" * 70)
        print("📊 IMPORT STATISTICS")
        print("=" * 70)
        print(f"Total repos in export: {self.stats['total_repos']:,}")
        print(f"Unique ecosystems found: {self.stats['unique_ecosystems']:,}")
        print(f"Ecosystems imported: {self.stats['ecosystems_imported']:,}")
        print(f"Repos linked to ecosystems: {self.stats['repos_linked']:,}")
        print(f"Companies matched to ecosystems: {self.stats['companies_matched']:,}")
        print(f"Skipped (duplicate repos): {self.stats['skipped_duplicate_repos']:,}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Import crypto ecosystems from Electric Capital export',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('jsonl_file', type=Path, help='Path to exported JSONL file')
    parser.add_argument('--priority-only', action='store_true', 
                        help='Import only priority ecosystems')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run (don\'t write to database)')
    
    args = parser.parse_args()
    
    if not args.jsonl_file.exists():
        logger.error(f"File not found: {args.jsonl_file}")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    conn = get_db_connection(use_pool=False)
    
    try:
        importer = EcosystemImporter(conn, dry_run=args.dry_run)
        importer.import_ecosystems(args.jsonl_file, priority_only=args.priority_only)
        importer.print_stats()
        
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        conn.rollback()
        sys.exit(1)
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()


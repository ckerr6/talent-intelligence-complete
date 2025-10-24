#!/usr/bin/env python3
"""
Electric Capital Crypto Ecosystems Taxonomy Parser

Downloads and parses the Electric Capital crypto-ecosystems taxonomy
to populate our database with crypto ecosystems and their repositories.

Usage:
    python3 scripts/github/parse_electric_capital_taxonomy.py --download
    python3 scripts/github/parse_electric_capital_taxonomy.py --parse exports.jsonl
    python3 scripts/github/parse_electric_capital_taxonomy.py --full  # Download + parse
    python3 scripts/github/parse_electric_capital_taxonomy.py --priority-only  # Only priority ecosystems
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config, get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Priority ecosystems (Tier 1-2)
PRIORITY_ECOSYSTEMS = {
    # Tier 1: Highest priority
    'ethereum': 1,
    'base': 1,
    'optimism': 1,
    'arbitrum': 1,
    'uniswap': 1,
    'paradigm': 1,
    
    # Tier 2: High priority
    'polygon': 2,
    'avalanche': 2,
    'solana': 2,
    'near': 2,
    'sui': 2,
    'aptos': 2,
    'cosmos': 2,
    'polkadot': 2,
    'aave': 2,
    'compound': 2,
    'makerdao': 2,
    'maker': 2,
    'curve': 2,
    'balancer': 2,
    'yearn': 2,
    'synthetix': 2,
    'lido': 2,
    'rocket pool': 2,
    'opensea': 2,
    'blur': 2,
    'rarible': 2,
    'ens': 2,
    'ethereum name service': 2,
    'lens protocol': 2,
    'chainlink': 2,
    'the graph': 2,
    'circle': 2,
    'coinbase': 2,
    'binance': 2,
    'kraken': 2,
    'gemini': 2,
}


class TaxonomyParser:
    """Parse Electric Capital crypto-ecosystems taxonomy"""
    
    def __init__(self, conn=None):
        self.conn = conn or get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'ecosystems_created': 0,
            'ecosystems_updated': 0,
            'repos_linked': 0,
            'repos_created': 0,
            'repos_skipped': 0,
            'start_time': time.time()
        }
        
        # Cache
        self.ecosystem_cache = {}  # name -> ecosystem_id
        self.repo_cache = {}  # full_name -> repo_id
        self.discovery_source_id = None
        
        logger.info("🚀 Taxonomy Parser initialized")
    
    def normalize_ecosystem_name(self, name: str) -> str:
        """Normalize ecosystem name for matching"""
        if not name:
            return ''
        
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in [' labs', ' lab', ' network', ' protocol', ' foundation', 
                       ' (', 'inc.', 'llc', 'ltd.']:
            if suffix in name:
                name = name.split(suffix)[0].strip()
        
        return name
    
    def get_priority_score(self, eco_name: str) -> int:
        """Get priority score for ecosystem (1=highest, 5=lowest)"""
        normalized = self.normalize_ecosystem_name(eco_name)
        return PRIORITY_ECOSYSTEMS.get(normalized, 3)  # Default to tier 3
    
    def get_or_create_discovery_source(self) -> UUID:
        """Get or create the Electric Capital taxonomy discovery source"""
        if self.discovery_source_id:
            return self.discovery_source_id
        
        self.cursor.execute("""
            INSERT INTO discovery_source (
                source_type,
                source_name,
                source_url,
                priority_tier,
                metadata
            ) VALUES (
                'electric_capital_taxonomy',
                'Electric Capital Crypto Ecosystems',
                'https://github.com/electric-capital/crypto-ecosystems',
                1,
                '{"description": "Comprehensive crypto ecosystem taxonomy", "parser_version": "1.0"}'::jsonb
            )
            ON CONFLICT (source_name, source_type) 
            DO UPDATE SET updated_at = NOW()
            RETURNING source_id
        """)
        
        self.discovery_source_id = self.cursor.fetchone()['source_id']
        self.conn.commit()
        
        logger.info(f"✓ Discovery source: {self.discovery_source_id}")
        return self.discovery_source_id
    
    def load_caches(self):
        """Load existing ecosystems and repos into cache"""
        logger.info("Loading existing data into cache...")
        
        # Load ecosystems
        self.cursor.execute("""
            SELECT ecosystem_id, ecosystem_name, normalized_name
            FROM crypto_ecosystem
        """)
        
        for row in self.cursor.fetchall():
            self.ecosystem_cache[row['normalized_name']] = row['ecosystem_id']
            # Also cache by name
            self.ecosystem_cache[row['ecosystem_name'].lower()] = row['ecosystem_id']
        
        logger.info(f"  Loaded {len(self.ecosystem_cache)} ecosystems")
        
        # Load repos
        self.cursor.execute("""
            SELECT repo_id, full_name
            FROM github_repository
        """)
        
        for row in self.cursor.fetchall():
            self.repo_cache[row['full_name'].lower()] = row['repo_id']
        
        logger.info(f"  Loaded {len(self.repo_cache)} repositories")
    
    def create_or_update_ecosystem(
        self, 
        eco_name: str, 
        parent_name: Optional[str] = None,
        tags: List[str] = None
    ) -> UUID:
        """Create or update an ecosystem"""
        normalized = self.normalize_ecosystem_name(eco_name)
        priority = self.get_priority_score(eco_name)
        
        # Check cache first
        cache_key = normalized or eco_name.lower()
        if cache_key in self.ecosystem_cache:
            # Update priority if better
            self.cursor.execute("""
                UPDATE crypto_ecosystem
                SET priority_score = LEAST(priority_score, %s),
                    taxonomy_source = 'electric_capital_taxonomy',
                    tags = COALESCE(tags, '{}') || %s::text[],
                    updated_at = NOW()
                WHERE ecosystem_id = %s
                RETURNING ecosystem_id
            """, (priority, tags or [], self.ecosystem_cache[cache_key]))
            
            result = self.cursor.fetchone()
            if result:
                self.stats['ecosystems_updated'] += 1
                return result['ecosystem_id']
        
        # Find parent ecosystem if specified
        parent_id = None
        if parent_name:
            parent_normalized = self.normalize_ecosystem_name(parent_name)
            parent_id = self.ecosystem_cache.get(parent_normalized)
        
        # Create new ecosystem
        try:
            self.cursor.execute("""
                INSERT INTO crypto_ecosystem (
                    ecosystem_name,
                    normalized_name,
                    parent_ecosystem_id,
                    taxonomy_source,
                    priority_score,
                    tags,
                    metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ecosystem_name) 
                DO UPDATE SET
                    normalized_name = EXCLUDED.normalized_name,
                    priority_score = LEAST(crypto_ecosystem.priority_score, EXCLUDED.priority_score),
                    taxonomy_source = EXCLUDED.taxonomy_source,
                    tags = COALESCE(crypto_ecosystem.tags, '{}') || EXCLUDED.tags,
                    updated_at = NOW()
                RETURNING ecosystem_id
            """, (
                eco_name,
                normalized,
                parent_id,
                'electric_capital_taxonomy',
                priority,
                tags or [],
                json.dumps({'source': 'electric_capital_taxonomy', 'priority': priority})
            ))
            
            ecosystem_id = self.cursor.fetchone()['ecosystem_id']
            self.ecosystem_cache[cache_key] = ecosystem_id
            self.stats['ecosystems_created'] += 1
            
            return ecosystem_id
            
        except Exception as e:
            logger.error(f"Error creating ecosystem {eco_name}: {e}")
            self.conn.rollback()
            return None
    
    def link_repo_to_ecosystem(
        self, 
        repo_url: str, 
        ecosystem_id: UUID,
        tags: List[str] = None
    ) -> bool:
        """Create or link a repository to an ecosystem"""
        
        # Parse GitHub URL
        if not repo_url.startswith('https://github.com/'):
            return False
        
        # Extract owner/repo
        try:
            parts = repo_url.replace('https://github.com/', '').strip('/').split('/')
            if len(parts) < 2:
                return False
            
            owner, repo_name = parts[0], parts[1]
            full_name = f"{owner}/{repo_name}"
            
        except Exception as e:
            logger.warning(f"Invalid repo URL {repo_url}: {e}")
            return False
        
        # Check if repo exists
        repo_id = self.repo_cache.get(full_name.lower())
        
        if not repo_id:
            # Create minimal repository entry
            try:
                self.cursor.execute("""
                    INSERT INTO github_repository (
                        full_name,
                        repo_name,
                        owner_username,
                        discovery_source_id,
                        ecosystem_ids
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING repo_id
                """, (
                    full_name,
                    repo_name,
                    owner,
                    self.get_or_create_discovery_source(),
                    [ecosystem_id]
                ))
                
                repo_id = self.cursor.fetchone()['repo_id']
                self.repo_cache[full_name.lower()] = repo_id
                self.stats['repos_created'] += 1
                
            except Exception as e:
                logger.warning(f"Error creating repo {full_name}: {e}")
                self.conn.rollback()
                return False
        else:
            # Add ecosystem to existing repo
            try:
                self.cursor.execute("""
                    UPDATE github_repository
                    SET ecosystem_ids = COALESCE(ecosystem_ids, '{}') || %s::uuid[]
                    WHERE repo_id = %s
                      AND NOT (%s = ANY(COALESCE(ecosystem_ids, '{}')))
                """, ([ecosystem_id], repo_id, ecosystem_id))
                
            except Exception as e:
                logger.warning(f"Error linking repo {full_name} to ecosystem: {e}")
                return False
        
        self.stats['repos_linked'] += 1
        return True
    
    def parse_jsonl_export(self, jsonl_file: Path, priority_only: bool = False):
        """Parse Electric Capital JSONL export file"""
        logger.info(f"📖 Parsing {jsonl_file}")
        
        if not jsonl_file.exists():
            logger.error(f"File not found: {jsonl_file}")
            return
        
        # Load caches
        self.load_caches()
        source_id = self.get_or_create_discovery_source()
        
        # Group by ecosystem
        ecosystems = defaultdict(lambda: {
            'name': None,
            'branches': set(),
            'repos': [],
            'tags': set()
        })
        
        line_count = 0
        with open(jsonl_file, 'r') as f:
            for line in f:
                line_count += 1
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    eco_name = entry.get('eco_name')
                    repo_url = entry.get('repo_url')
                    branches = entry.get('branch', [])
                    tags = entry.get('tags', [])
                    
                    if not eco_name or not repo_url:
                        continue
                    
                    # Filter by priority if requested
                    if priority_only:
                        priority = self.get_priority_score(eco_name)
                        if priority > 2:  # Only tier 1 and 2
                            continue
                    
                    ecosystems[eco_name]['name'] = eco_name
                    ecosystems[eco_name]['repos'].append(repo_url)
                    ecosystems[eco_name]['branches'].update(branches if branches else [])
                    ecosystems[eco_name]['tags'].update(tags if tags else [])
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_count}: {e}")
                    continue
        
        logger.info(f"  Parsed {line_count} lines, found {len(ecosystems)} unique ecosystems")
        
        # Process ecosystems
        logger.info("🏗️  Creating/updating ecosystems...")
        
        processed = 0
        for eco_name, data in ecosystems.items():
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"  Progress: {processed}/{len(ecosystems)} ecosystems")
                self.conn.commit()
            
            # Create main ecosystem
            ecosystem_id = self.create_or_update_ecosystem(
                eco_name,
                tags=list(data['tags'])
            )
            
            if not ecosystem_id:
                continue
            
            # Create sub-ecosystems (branches)
            for branch in data['branches']:
                if branch and branch != eco_name:
                    self.create_or_update_ecosystem(
                        branch,
                        parent_name=eco_name,
                        tags=list(data['tags'])
                    )
            
            # Link repositories
            for repo_url in data['repos']:
                self.link_repo_to_ecosystem(repo_url, ecosystem_id, list(data['tags']))
        
        self.conn.commit()
        logger.info("✅ Parsing complete!")
        self.print_stats()
    
    def download_taxonomy(self, output_file: Path = None) -> Path:
        """Download Electric Capital taxonomy export"""
        logger.info("📥 Downloading Electric Capital taxonomy...")
        
        if output_file is None:
            output_file = Path(tempfile.gettempdir()) / 'electric_capital_exports.jsonl'
        
        # Clone the repo in a temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / 'crypto-ecosystems'
            
            logger.info(f"  Cloning to {repo_dir}...")
            result = subprocess.run(
                ['git', 'clone', '--depth=1', 
                 'https://github.com/electric-capital/crypto-ecosystems.git',
                 str(repo_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to clone repo: {result.stderr}")
                return None
            
            logger.info("  Running export script...")
            
            # Check if run.sh exists and is executable
            run_script = repo_dir / 'run.sh'
            if not run_script.exists():
                logger.error(f"Export script not found at {run_script}")
                return None
            
            # Run the export
            result = subprocess.run(
                [str(run_script), 'export', str(output_file)],
                cwd=str(repo_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Export failed: {result.stderr}")
                return None
            
            logger.info(f"✅ Downloaded to {output_file}")
            
            return output_file
    
    def print_stats(self):
        """Print statistics"""
        elapsed = time.time() - self.stats['start_time']
        
        logger.info("=" * 60)
        logger.info("📊 TAXONOMY IMPORT STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Ecosystems created:    {self.stats['ecosystems_created']:,}")
        logger.info(f"Ecosystems updated:    {self.stats['ecosystems_updated']:,}")
        logger.info(f"Repositories created:  {self.stats['repos_created']:,}")
        logger.info(f"Repositories linked:   {self.stats['repos_linked']:,}")
        logger.info(f"Repositories skipped:  {self.stats['repos_skipped']:,}")
        logger.info(f"")
        logger.info(f"Time elapsed:          {elapsed:.1f}s")
        logger.info("=" * 60)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Parse Electric Capital crypto-ecosystems taxonomy'
    )
    parser.add_argument(
        '--download',
        action='store_true',
        help='Download the taxonomy export'
    )
    parser.add_argument(
        '--parse',
        type=str,
        metavar='FILE',
        help='Parse a JSONL export file'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Download and parse (full workflow)'
    )
    parser.add_argument(
        '--priority-only',
        action='store_true',
        help='Only import priority ecosystems (tier 1-2)'
    )
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Output file for download (default: temp file)'
    )
    
    args = parser.parse_args()
    
    taxonomy_parser = TaxonomyParser()
    
    try:
        if args.full or args.download:
            # Download
            output_path = Path(args.output) if args.output else None
            export_file = taxonomy_parser.download_taxonomy(output_path)
            
            if not export_file:
                logger.error("Download failed")
                return 1
            
            if args.full:
                # Also parse
                taxonomy_parser.parse_jsonl_export(export_file, args.priority_only)
        
        elif args.parse:
            # Just parse
            export_file = Path(args.parse)
            taxonomy_parser.parse_jsonl_export(export_file, args.priority_only)
        
        else:
            parser.print_help()
            return 1
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        return 1
    
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1
    
    finally:
        taxonomy_parser.close()


if __name__ == '__main__':
    sys.exit(main())


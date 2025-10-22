#!/usr/bin/env python3
"""
Company Deduplication and Merge Script
======================================
Identifies and merges duplicate company records in PostgreSQL talent database

Features:
- Finds duplicates by name similarity and domain matching
- Handles ecosystem nuances (Labs vs Foundation can be separate entities)
- Merges employment records to canonical company
- Updates company records with missing domains
- Preserves all data during merge
- Full audit trail

Author: AI Assistant
Date: October 22, 2025
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from config import get_db_connection, Config

# Import data quality filters
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from data_quality_filters import should_skip_company_deduplication

# Setup logging
log_filename = f"company_deduplication_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Known company domain mappings
KNOWN_DOMAINS = {
    '0x': '0x.org',
    '0x labs': '0x.org',
    '0x protocol': '0x.org',
    '1inch': '1inch.io',
    '1inch network': '1inch.io',
    'aave': 'aave.com',
    'aave labs': 'aave.com',
    'alchemy': 'alchemy.com',
    'alchemy insights': 'alchemy.com',
    'aptos': 'aptos.dev',  # Generic Aptos → Labs
    'aptos labs': 'aptos.dev',
    # Note: Aptos Foundation is separate but may share domain
    'bitgo': 'bitgo.com',
    'blackbird': 'blackbird.xyz',
    'coinbase': 'coinbase.com',
    'coindesk': 'coindesk.com',
    'eigenlabs': 'eigenlayer.xyz',
    'eigen labs': 'eigenlayer.xyz',
    'polygon': 'polygon.technology',
    'polygon labs': 'polygon.technology',
    'uniswap': 'uniswap.org',  # Generic Uniswap → Labs
    'uniswap labs': 'uniswap.org',
    # Note: Uniswap Foundation is separate
}

# Companies that should NOT be merged even if similar names
# Format: (company1_normalized, company2_normalized)
KEEP_SEPARATE = [
    ('uniswap labs', 'uniswap foundation'),
    ('aptos labs', 'aptos foundation'),
    # Add more as discovered
]

def should_keep_separate(name1: str, name2: str) -> bool:
    """Check if two companies should be kept separate"""
    name1_norm = name1.lower().strip()
    name2_norm = name2.lower().strip()
    
    for pair in KEEP_SEPARATE:
        if (name1_norm == pair[0] and name2_norm == pair[1]) or \
           (name1_norm == pair[1] and name2_norm == pair[0]):
            return True
    
    return False

class CompanyDeduplicator:
    def __init__(self, dry_run=True):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = False  # Use transactions for safety
        self.cursor = self.conn.cursor()
        self.dry_run = dry_run
        
        self.stats = {
            'companies_analyzed': 0,
            'duplicates_found': 0,
            'companies_merged': 0,
            'employment_records_moved': 0,
            'domains_updated': 0,
            'companies_deleted': 0,
            'kept_separate': 0,
            'errors': []
        }
        
        mode = "DRY RUN" if dry_run else "LIVE RUN"
        logger.info("="*80)
        logger.info(f"COMPANY DEDUPLICATION ({mode})")
        logger.info("="*80)
        logger.info(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}")
        logger.info(f"Log file: {log_filename}")
        logger.info("")
        
        print(f"\n{'='*80}")
        print(f"COMPANY DEDUPLICATION ({mode})")
        print(f"{'='*80}")
        print(f"Log file: {log_filename}\n")
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching"""
        if not name:
            return ""
        
        name = name.lower().strip()
        
        # Remove common suffixes INCLUDING Labs (but we'll check Foundation separately)
        suffixes = [
            r'\s+(labs?|inc\.?|llc|corp\.?|corporation|ltd\.?|limited|'
            r'network|protocol|technologies|tech|group)$'
        ]
        for suffix in suffixes:
            name = re.sub(suffix, '', name, flags=re.IGNORECASE)
        
        # Remove special characters but keep spaces
        name = re.sub(r'[^\w\s]', '', name)
        
        return name.strip()
    
    def find_duplicate_groups(self) -> List[List[Dict]]:
        """Find groups of duplicate companies"""
        logger.info("Searching for duplicate companies...")
        print("🔍 Searching for duplicate companies...\n")
        
        # Get all companies with their employment counts
        logger.info("Querying database for all companies...")
        self.cursor.execute("""
            SELECT 
                c.company_id::text,
                c.company_name,
                c.company_domain,
                c.linkedin_url,
                c.website_url,
                COUNT(e.employment_id) as employee_count,
                c.founded_year,
                c.size_bucket
            FROM company c
            LEFT JOIN employment e ON c.company_id = e.company_id
            GROUP BY c.company_id, c.company_name, c.company_domain, 
                     c.linkedin_url, c.website_url, c.founded_year, c.size_bucket
            HAVING c.company_name IS NOT NULL
            ORDER BY c.company_name
        """)
        
        companies = [dict(row) for row in self.cursor.fetchall()]
        self.stats['companies_analyzed'] = len(companies)
        logger.info(f"Found {len(companies):,} companies in database")
        print(f"   Analyzed {len(companies):,} companies\n")
        
        # DATA QUALITY FILTER: Skip suffix-only and invalid companies
        companies_before_filter = len(companies)
        companies = [c for c in companies if not should_skip_company_deduplication(c['company_name'])]
        skipped_count = companies_before_filter - len(companies)
        
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} companies with invalid/suffix-only names")
            print(f"   ⚠️  Skipped {skipped_count} companies with invalid names (suffix-only, too short, etc.)")
            print(f"   Remaining: {len(companies):,} companies for deduplication\n")
        
        # Group by normalized name
        name_groups = {}
        for company in companies:
            normalized = self.normalize_company_name(company['company_name'])
            if normalized not in name_groups:
                name_groups[normalized] = []
            name_groups[normalized].append(company)
        
        # Find groups with duplicates, but filter out those that should be kept separate
        duplicate_groups = []
        for group in name_groups.values():
            if len(group) > 1:
                # Filter out pairs that should be kept separate
                filtered_group = self._filter_separate_entities(group)
                if len(filtered_group) > 1:
                    duplicate_groups.append(filtered_group)
        
        return duplicate_groups
    
    def _filter_separate_entities(self, group: List[Dict]) -> List[Dict]:
        """Remove companies from group that should be kept separate"""
        # If group has BOTH "Labs" and "Foundation" variants, split them
        has_labs = any('labs' in c['company_name'].lower() for c in group)
        has_foundation = any('foundation' in c['company_name'].lower() for c in group)
        
        if has_labs and has_foundation:
            # This group has both Labs and Foundation - need to separate
            base_name = self.normalize_company_name(group[0]['company_name'])
            
            # Check if this matches our known pairs
            for c1 in group:
                for c2 in group:
                    if c1 != c2 and should_keep_separate(c1['company_name'], c2['company_name']):
                        self.stats['kept_separate'] += 1
                        print(f"   ℹ️  Keeping separate: '{c1['company_name']}' and '{c2['company_name']}'")
                        
                        # Return only the non-Foundation companies to merge
                        # Foundation stays separate
                        non_foundation = [c for c in group if 'foundation' not in c['company_name'].lower()]
                        return non_foundation if len(non_foundation) > 1 else []
            
            # Not in our known list, but still has both - be conservative and skip
            print(f"   ℹ️  Found Labs + Foundation for '{base_name}' - keeping all separate")
            self.stats['kept_separate'] += len(group) - 1
            return []
        
        return group
    
    def choose_canonical_company(self, group: List[Dict]) -> Dict:
        """Choose the best/canonical company from a duplicate group"""
        
        # Scoring criteria (higher is better):
        # 1. Has real domain (not .placeholder) = +1000
        # 2. Has more employees = +employee_count
        # 3. Has LinkedIn URL = +100
        # 4. Has website = +50
        # 5. Has founded year = +10
        # 6. Prefer "Labs" over generic name = +20
        
        scores = []
        for company in group:
            score = 0
            
            # Real domain vs placeholder
            if company['company_domain'] and not company['company_domain'].endswith('.placeholder'):
                score += 1000
            
            # Employee count
            score += company['employee_count']
            
            # Has LinkedIn
            if company['linkedin_url']:
                score += 100
            
            # Has website
            if company['website_url']:
                score += 50
            
            # Has founded year
            if company['founded_year']:
                score += 10
            
            # Prefer "Labs" variant (more specific)
            if 'labs' in company['company_name'].lower():
                score += 20
            
            scores.append((score, company))
        
        # Return company with highest score
        scores.sort(reverse=True, key=lambda x: x[0])
        return scores[0][1]
    
    def merge_companies(self, canonical: Dict, duplicates: List[Dict]) -> bool:
        """Merge duplicate companies into canonical company"""
        
        canonical_id = canonical['company_id']
        canonical_name = canonical['company_name']
        
        try:
            for duplicate in duplicates:
                dup_id = duplicate['company_id']
                dup_name = duplicate['company_name']
                dup_employees = duplicate['employee_count']
                
                logger.info(f"Merging '{dup_name}' ({dup_employees} employees) → '{canonical_name}'")
                print(f"   Merging '{dup_name}' ({dup_employees} employees)")
                print(f"       → into '{canonical_name}'")
                
                if not self.dry_run:
                    # Move employment records
                    self.cursor.execute("""
                        UPDATE employment
                        SET company_id = %s::uuid
                        WHERE company_id = %s::uuid
                    """, (canonical_id, dup_id))
                    
                    moved = self.cursor.rowcount
                    self.stats['employment_records_moved'] += moved
                    logger.info(f"  Moved {moved} employment records from {dup_name} to {canonical_name}")
                    print(f"       ✅ Moved {moved} employment records")
                    
                    # Delete duplicate company
                    self.cursor.execute("""
                        DELETE FROM company
                        WHERE company_id = %s::uuid
                    """, (dup_id,))
                    
                    self.stats['companies_deleted'] += 1
                    logger.info(f"  Deleted duplicate company: {dup_name} (ID: {dup_id})")
                else:
                    print(f"       [DRY RUN] Would move {dup_employees} employment records")
                
                self.stats['companies_merged'] += 1
            
            return True
            
        except Exception as e:
            error_msg = f"Error merging {canonical_name}: {e}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            print(f"       ❌ Error: {e}")
            if not self.dry_run:
                self.conn.rollback()
            return False
    
    def update_missing_domains(self):
        """Update companies with known domains"""
        print("\n🌐 Updating missing domains...\n")
        
        updated_count = 0
        
        for company_name_lower, domain in KNOWN_DOMAINS.items():
            try:
                # Find companies matching this name
                self.cursor.execute("""
                    SELECT company_id::text, company_name, company_domain
                    FROM company
                    WHERE LOWER(TRIM(company_name)) = %s
                       OR (company_domain LIKE %s)
                """, (company_name_lower, f'{company_name_lower.replace(" ", "")}%placeholder'))
                
                results = self.cursor.fetchall()
                
                for row in results:
                    current_domain = row['company_domain']
                    
                    # Only update if domain is placeholder or NULL
                    if not current_domain or current_domain.endswith('.placeholder'):
                        print(f"   Updating '{row['company_name']}' → {domain}")
                        
                        if not self.dry_run:
                            try:
                                self.cursor.execute("""
                                    UPDATE company
                                    SET company_domain = %s
                                    WHERE company_id = %s::uuid
                                    AND (company_domain IS NULL OR company_domain LIKE '%.placeholder')
                                """, (domain, row['company_id']))
                                
                                if self.cursor.rowcount > 0:
                                    self.conn.commit()
                                    updated_count += 1
                                    self.stats['domains_updated'] += 1
                            except Exception as e:
                                # Rollback this transaction and continue
                                self.conn.rollback()
                                print(f"       ⚠️  Could not update (domain already in use): {str(e)[:80]}")
                        else:
                            print(f"       [DRY RUN] Would update domain to {domain}")
                            updated_count += 1
            except Exception as e:
                # If there's an error with the SELECT, rollback and continue
                self.conn.rollback()
                print(f"   ⚠️  Error processing {company_name_lower}: {str(e)[:80]}")
                continue
        
        if updated_count == 0:
            print("   No domains need updating")
        else:
            print(f"\n   {'Would update' if self.dry_run else 'Updated'} {updated_count} domains")
    
    def process(self):
        """Main processing function"""
        
        logger.info("Starting deduplication process...")
        
        # Step 1: Update missing domains
        logger.info("Step 1: Updating missing domains")
        self.update_missing_domains()
        
        # Step 2: Find duplicate groups
        logger.info("Step 2: Finding duplicate company groups")
        duplicate_groups = self.find_duplicate_groups()
        
        if not duplicate_groups:
            logger.info("No duplicates found!")
            print("✅ No duplicates found!\n")
            self.print_summary()
            return
        
        self.stats['duplicates_found'] = len(duplicate_groups)
        logger.info(f"Found {len(duplicate_groups)} duplicate groups to process")
        
        print(f"\nFound {len(duplicate_groups)} groups of duplicates:\n")
        
        # Step 3: Process each group
        logger.info("Step 3: Processing duplicate groups")
        for i, group in enumerate(duplicate_groups, 1):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(duplicate_groups)} groups processed ({i/len(duplicate_groups)*100:.1f}%)")
                logger.info(f"  Stats so far: {self.stats['companies_merged']} merged, {self.stats['employment_records_moved']} employment records moved")
            
            print(f"\n{'─'*80}")
            print(f"Group {i}/{len(duplicate_groups)}:")
            print(f"{'─'*80}")
            
            # Log the group
            group_names = [f"{c['company_name']} ({c['employee_count']} emp)" for c in group]
            logger.info(f"Group {i}: {', '.join(group_names)}")
            
            # Show all companies in group
            for company in group:
                print(f"   • {company['company_name']} "
                      f"({company['employee_count']} employees, "
                      f"domain: {company['company_domain'] or 'NONE'})")
            
            # Choose canonical
            canonical = self.choose_canonical_company(group)
            duplicates = [c for c in group if c['company_id'] != canonical['company_id']]
            
            logger.info(f"  Canonical: {canonical['company_name']} ({canonical['employee_count']} employees)")
            
            print(f"\n   ✓ CANONICAL: {canonical['company_name']} "
                  f"({canonical['employee_count']} employees)")
            
            if duplicates:
                print(f"   ✗ DUPLICATES ({len(duplicates)}):")
                
                # Merge duplicates into canonical
                success = self.merge_companies(canonical, duplicates)
                
                if not self.dry_run and success:
                    self.conn.commit()
                    logger.info(f"  Group {i} merge committed successfully")
                    print(f"   ✅ Merge committed")
                elif not success:
                    logger.error(f"  Group {i} merge FAILED")
        
        # Final summary
        logger.info("Deduplication process complete, generating summary...")
        self.print_summary()
    
    def print_summary(self):
        """Print final summary"""
        mode = "DRY RUN" if self.dry_run else "LIVE RUN"
        
        logger.info("="*80)
        logger.info(f"DEDUPLICATION COMPLETE ({mode})")
        logger.info("="*80)
        logger.info("")
        logger.info("STATISTICS:")
        logger.info(f"  Companies Analyzed: {self.stats['companies_analyzed']:,}")
        logger.info(f"  Duplicate Groups Found: {self.stats['duplicates_found']}")
        logger.info(f"  Companies Kept Separate: {self.stats['kept_separate']} (Labs vs Foundation)")
        logger.info(f"  Companies Merged: {self.stats['companies_merged']}")
        logger.info(f"  Employment Records Moved: {self.stats['employment_records_moved']:,}")
        logger.info(f"  Domains Updated: {self.stats['domains_updated']}")
        logger.info(f"  Companies Deleted: {self.stats['companies_deleted']}")
        
        print(f"\n{'='*80}")
        print(f"DEDUPLICATION COMPLETE ({mode})")
        print(f"{'='*80}\n")
        
        print(f"📊 STATISTICS:")
        print(f"   Companies Analyzed: {self.stats['companies_analyzed']:,}")
        print(f"   Duplicate Groups Found: {self.stats['duplicates_found']}")
        print(f"   Companies Kept Separate: {self.stats['kept_separate']} (Labs vs Foundation)")
        print(f"   Companies Merged: {self.stats['companies_merged']}")
        print(f"   Employment Records Moved: {self.stats['employment_records_moved']:,}")
        print(f"   Domains Updated: {self.stats['domains_updated']}")
        print(f"   Companies Deleted: {self.stats['companies_deleted']}")
        
        if self.stats['errors']:
            logger.warning(f"ERRORS: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.error(f"  {error}")
            
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"   - {error}")
        
        # Show final counts
        if not self.dry_run:
            self.cursor.execute("SELECT COUNT(*) as count FROM company")
            total_companies = self.cursor.fetchone()['count']
            logger.info(f"Final Company Count: {total_companies:,}")
            print(f"\n📈 Final Company Count: {total_companies:,}")
        
        logger.info(f"Log file saved: {log_filename}")
        print(f"\n📄 Full log saved to: {log_filename}")
        print(f"\n{'='*80}\n")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deduplicate companies in PostgreSQL talent database')
    parser.add_argument('--live', action='store_true', 
                       help='Perform actual merge (default is dry-run)')
    parser.add_argument('--no-confirm', action='store_true',
                       help='Skip confirmation prompt (use with caution!)')
    
    args = parser.parse_args()
    
    # Confirmation for live run
    if args.live and not args.no_confirm:
        print(f"\n⚠️  WARNING: You are about to perform a LIVE merge operation!")
        print(f"This will:")
        print(f"  - Merge duplicate companies")
        print(f"  - Move employment records")
        print(f"  - Delete duplicate company records")
        print(f"  - Update company domains")
        print(f"\nIMPORTANT NOTES:")
        print(f"  - Uniswap Labs and Uniswap Foundation will be kept separate")
        print(f"  - Aptos Labs and Aptos Foundation will be kept separate")
        print(f"  - Polygon and Polygon Labs will be merged (same company)")
        print(f"  - Generic names (Uniswap, Aptos) will merge to Labs variant")
        print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
        
        response = input(f"\nProceed with LIVE merge? (type 'MERGE' to confirm): ")
        if response != 'MERGE':
            print("❌ Operation cancelled")
            return 0
    
    try:
        deduplicator = CompanyDeduplicator(dry_run=not args.live)
        deduplicator.process()
        deduplicator.close()
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


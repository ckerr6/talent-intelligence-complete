#!/usr/bin/env python3
"""
Clay CSV Import Script for People Data
=======================================
Imports people from Clay export CSV format and enriches existing profiles

VERIFIED COMPATIBLE WITH:
- PostgreSQL 'talent' database schema (post-migration Oct 2025)
- person table (UNIQUE constraint on linkedin_url)
- company table
- employment table
- migration_log tracking

Clay CSV Format:
- Find people (ignored)
- Current Company
- First Name
- Last Name
- Full Name
- Job Title
- Location
- Company Domain
- LinkedIn Profile

Author: AI Assistant
Date: October 22, 2025
"""

import sys
import csv
from pathlib import Path
from datetime import datetime
import re
from typing import Optional, Dict, List
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import get_db_connection, Config

# Import data quality filters
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from data_quality_filters import is_valid_company_name, get_company_validation_message

# Import logging and employment utilities
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from logging_utils import Logger
from imports.employment_utils import EmploymentDataExtractor, EmploymentRecordManager

# Import migration utilities
try:
    from migration_scripts.migration_utils import (
        normalize_linkedin_url,
        log_migration_event
    )
except ImportError:
    print("⚠️  Warning: Could not import migration_utils, using fallback functions")
    
    def normalize_linkedin_url(url: str) -> Optional[str]:
        """Fallback LinkedIn URL normalization"""
        if not url or not url.strip():
            return None
        url = url.lower().strip()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        url = url.rstrip('/')
        match = re.search(r'linkedin\.com/in/([^/?]+)', url)
        if match:
            return f'linkedin.com/in/{match.group(1)}'
        return None
    
    def log_migration_event(conn, migration_name: str, phase: str, status: str,
                            records_processed: int = 0, records_created: int = 0,
                            records_updated: int = 0, records_skipped: int = 0,
                            error_message: str = None, metadata: dict = None):
        """Fallback migration logging"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO migration_log 
                (migration_name, migration_phase, status, records_processed, records_created,
                 records_updated, records_skipped, error_message, completed_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (migration_name, phase, status, records_processed, records_created,
                  records_updated, records_skipped, error_message,
                  json.dumps(metadata) if metadata else None))
            conn.commit()
        except Exception as e:
            print(f"⚠️  Warning: Could not log migration event: {e}")

# CSV Configuration
CSV_PATH = "/Users/charlie.kerr/Desktop/Imports for TI Final/clay_find_people_crypto.csv"

class ClayPeopleImporter:
    def __init__(self, verbose=True):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = True  # Use autocommit to avoid transaction issues
        self.cursor = self.conn.cursor()
        
        # Initialize logger and employment utilities
        self.logger = Logger("clay_people_import", verbose=verbose)
        self.employment_manager = EmploymentRecordManager(self.cursor, self.logger)
        self.employment_extractor = EmploymentDataExtractor()
        
        # Statistics tracking
        self.stats = {
            'total_rows': 0,
            'profiles_enriched': 0,
            'profiles_created': 0,
            'employment_records_added': 0,
            'companies_matched': 0,
            'companies_created': 0,
            'skipped_no_linkedin': 0,
            'skipped_duplicate_linkedin': 0,
            'skipped_invalid': 0,
            'errors': []
        }
        
        # Caches for performance
        self.person_cache = {}  # normalized_linkedin_url -> person_id
        self.company_cache = {}  # company_name_lower -> company_id
        
        print("📦 Loading existing data into cache...")
        self._load_caches()
        print(f"   ✅ Loaded {len(self.person_cache):,} people, {len(self.company_cache):,} companies\n")
    
    def _load_caches(self):
        """Pre-load existing data for faster lookups"""
        # Load people by normalized LinkedIn URL
        self.cursor.execute("""
            SELECT normalized_linkedin_url, person_id::text
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.person_cache[row['normalized_linkedin_url']] = row['person_id']
        
        # Load companies by name
        self.cursor.execute("""
            SELECT LOWER(TRIM(company_name)) as name_lower, company_id::text
            FROM company
            WHERE company_name IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.company_cache[row['name_lower']] = row['company_id']
    
    def find_existing_person(self, row: Dict) -> Optional[str]:
        """Find if person already exists in database by LinkedIn URL"""
        linkedin_url = row.get('LinkedIn Profile', '').strip()
        
        if not linkedin_url:
            return None
        
        # Try LinkedIn URL match (check cache first)
        normalized = normalize_linkedin_url(linkedin_url)
        if normalized and normalized in self.person_cache:
            return self.person_cache[normalized]
        
        return None
    
    def find_or_create_company(self, company_name: str, company_domain: str = None) -> Optional[str]:
        """Find existing company or create new one"""
        if not company_name or not company_name.strip():
            return None
        
        company_name = company_name.strip()
        
        # DATA QUALITY CHECK: Validate company name
        if not is_valid_company_name(company_name):
            error_msg = get_company_validation_message(company_name)
            self.stats['errors'].append(f"Invalid company name skipped: {error_msg}")
            return None
        name_key = company_name.lower()
        
        # Check cache
        if name_key in self.company_cache:
            return self.company_cache[name_key]
        
        # Check database
        self.cursor.execute("""
            SELECT company_id::text
            FROM company
            WHERE LOWER(TRIM(company_name)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (company_name,))
        
        result = self.cursor.fetchone()
        if result:
            company_id = result['company_id']
            self.company_cache[name_key] = company_id
            self.stats['companies_matched'] += 1
            return company_id
        
        # Create new company
        # Domain must be unique, so create placeholder if none provided
        if company_domain and company_domain.strip():
            domain = company_domain.strip().lower()
        else:
            # Generate placeholder domain from company name
            domain_placeholder = re.sub(r'[^a-z0-9]+', '', company_name.lower())[:50] + '.placeholder'
            domain = domain_placeholder
        
        try:
            self.cursor.execute("""
                INSERT INTO company (company_id, company_name, company_domain)
                VALUES (gen_random_uuid(), %s, %s)
                ON CONFLICT (company_domain) DO UPDATE
                SET company_name = EXCLUDED.company_name
                RETURNING company_id::text
            """, (company_name, domain))
            
            result = self.cursor.fetchone()
            if result:
                company_id = result['company_id']
                self.company_cache[name_key] = company_id
                self.stats['companies_created'] += 1
                return company_id
        except Exception as e:
            self.stats['errors'].append(f"Error creating company {company_name}: {e}")
            return None
        
        return None
    
    def enrich_existing_profile(self, person_id: str, row: Dict):
        """Enrich an existing profile with new data (preserve existing)"""
        updated = False
        
        # Update basic info ONLY if currently NULL (preserve existing data)
        updates = []
        params = []
        
        if row.get('First Name'):
            updates.append("first_name = COALESCE(first_name, %s)")
            params.append(row['First Name'].strip())
        
        if row.get('Last Name'):
            updates.append("last_name = COALESCE(last_name, %s)")
            params.append(row['Last Name'].strip())
        
        if row.get('Full Name'):
            updates.append("full_name = COALESCE(full_name, %s)")
            params.append(row['Full Name'].strip())
        
        if row.get('Location'):
            updates.append("location = COALESCE(location, %s)")
            params.append(row['Location'].strip())
        
        if row.get('Job Title'):
            updates.append("headline = COALESCE(headline, %s)")
            params.append(row['Job Title'].strip())
        
        # Always update refreshed_at when enriching
        updates.append("refreshed_at = NOW()")
        
        if updates:
            params.append(person_id)
            sql = f"""
                UPDATE person
                SET {', '.join(updates)}
                WHERE person_id = %s::uuid
            """
            try:
                self.cursor.execute(sql, params)
                if self.cursor.rowcount > 0:
                    updated = True
            except Exception as e:
                self.stats['errors'].append(f"Error updating person {person_id}: {e}")
        
        # Add employment record with date support
        if row.get('Current Company'):
            company_id = self.employment_manager.find_or_create_company(
                row['Current Company'],
                self.company_cache
            )
            
            if company_id:
                # Extract title and dates
                title = row.get('Job Title') or row.get('Title')
                
                # Clay typically has current employment, so check for date fields
                date_range = row.get('Date Range') or row.get('Employment Dates')
                start_date, end_date = None, None
                
                if date_range:
                    start_date, end_date = self.employment_extractor.parse_date_range(date_range)
                else:
                    # Try individual date columns
                    if row.get('Start Date'):
                        start_date, _ = self.employment_extractor.parse_date_range(row['Start Date'])
                    if row.get('End Date'):
                        _, end_date = self.employment_extractor.parse_date_range(row['End Date'])
                
                # Add the employment record
                if self.employment_manager.add_employment_record(
                    person_id=person_id,
                    company_id=company_id,
                    title=title,
                    start_date=start_date,
                    end_date=end_date,
                    location=row.get('Location') or row.get('Job Location'),
                    source_text_ref='clay_import',
                    source_confidence=0.85,  # Clay data is typically high quality
                    check_duplicates=True
                ):
                    self.stats['employment_records_added'] += 1
                    updated = True
        
        if updated:
            self.stats['profiles_enriched'] += 1
            self.logger.info(f"Enriched profile for person {person_id[:8]}...")
    
    def create_new_profile(self, row: Dict):
        """Create a new profile from CSV row"""
        try:
            # Get data from Clay CSV format
            full_name = row.get('Full Name', '').strip()
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            linkedin_url = row.get('LinkedIn Profile', '').strip()
            
            # Build full name from parts if not provided
            if not full_name and (first_name or last_name):
                full_name = f"{first_name or ''} {last_name or ''}".strip()
            
            # Validate required fields
            if not linkedin_url:
                self.stats['skipped_no_linkedin'] += 1
                return
            
            if not full_name:
                self.stats['skipped_invalid'] += 1
                return
            
            # Normalize LinkedIn URL
            normalized_linkedin = normalize_linkedin_url(linkedin_url)
            
            # Insert person (handle UNIQUE constraint on linkedin_url)
            try:
                self.cursor.execute("""
                    INSERT INTO person (
                        person_id, full_name, first_name, last_name, 
                        linkedin_url, normalized_linkedin_url,
                        location, headline
                    )
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (linkedin_url) DO NOTHING
                    RETURNING person_id::text
                """, (
                    full_name,
                    first_name or None,
                    last_name or None,
                    linkedin_url,
                    normalized_linkedin,
                    row.get('Location') or None,
                    row.get('Job Title') or None
                ))
                
                result = self.cursor.fetchone()
                if not result:
                    # Conflict - person already exists with this LinkedIn URL
                    self.stats['skipped_duplicate_linkedin'] += 1
                    return
                
                person_id = result['person_id']
                
            except Exception as e:
                self.stats['errors'].append(f"Error creating person {full_name}: {e}")
                self.stats['skipped_invalid'] += 1
                return
            
            # Cache it
            if normalized_linkedin:
                self.person_cache[normalized_linkedin] = person_id
            
            # Add employment with date support
            if row.get('Current Company'):
                company_id = self.employment_manager.find_or_create_company(
                    row['Current Company'],
                    self.company_cache
                )
                
                if company_id:
                    # Extract title and dates
                    title = row.get('Job Title') or row.get('Title')
                    
                    # Clay typically has current employment, check for date fields
                    date_range = row.get('Date Range') or row.get('Employment Dates')
                    start_date, end_date = None, None
                    
                    if date_range:
                        start_date, end_date = self.employment_extractor.parse_date_range(date_range)
                    else:
                        # Try individual date columns
                        if row.get('Start Date'):
                            start_date, _ = self.employment_extractor.parse_date_range(row['Start Date'])
                        if row.get('End Date'):
                            _, end_date = self.employment_extractor.parse_date_range(row['End Date'])
                    
                    # Add the employment record
                    if self.employment_manager.add_employment_record(
                        person_id=person_id,
                        company_id=company_id,
                        title=title,
                        start_date=start_date,
                        end_date=end_date,
                        location=row.get('Location') or row.get('Job Location'),
                        source_text_ref='clay_import',
                        source_confidence=0.85,
                        check_duplicates=False  # New profile, no need to check
                    ):
                        self.stats['employment_records_added'] += 1
            
            self.stats['profiles_created'] += 1
            self.logger.success(f"✓ Created profile: {full_name}")
            
        except Exception as e:
            self.stats['errors'].append(f"Error processing row: {e}")
            self.stats['skipped_invalid'] += 1
    
    def process_csv(self):
        """Main processing loop"""
        print(f"\n{'='*80}")
        print(f"CLAY CSV IMPORT - PEOPLE DATA")
        print(f"{'='*80}")
        print(f"\nSource: {CSV_PATH}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
        
        # Read and process CSV
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            batch_size = 100
            batch_count = 0
            
            for row in reader:
                self.stats['total_rows'] += 1
                
                # Skip completely empty rows
                if not any(v and str(v).strip() for v in row.values()):
                    self.stats['skipped_invalid'] += 1
                    continue
                
                # Skip rows without LinkedIn Profile
                linkedin_url = row.get('LinkedIn Profile', '').strip()
                if not linkedin_url:
                    self.stats['skipped_no_linkedin'] += 1
                    continue
                
                # Check if person exists
                person_id = self.find_existing_person(row)
                
                if person_id:
                    # Enrich existing profile
                    self.enrich_existing_profile(person_id, row)
                else:
                    # Create new profile
                    self.create_new_profile(row)
                
                # Progress update
                batch_count += 1
                if batch_count >= batch_size:
                    print(f"   Processed {self.stats['total_rows']:,} rows... "
                          f"({self.stats['profiles_created']} created, "
                          f"{self.stats['profiles_enriched']} enriched)", flush=True)
                    batch_count = 0
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate and display import report"""
        print(f"\n{'='*80}")
        print(f"IMPORT COMPLETE - FINAL REPORT")
        print(f"{'='*80}")
        print(f"\nSource File: {CSV_PATH}")
        
        print(f"\n📊 PROCESSING STATISTICS:")
        print(f"   Total Rows Processed: {self.stats['total_rows']:,}")
        print(f"\n👥 PEOPLE:")
        print(f"   ✅ Profiles Created: {self.stats['profiles_created']:,}")
        print(f"   🔄 Profiles Enriched: {self.stats['profiles_enriched']:,}")
        print(f"   ⏭️  Skipped (No LinkedIn): {self.stats['skipped_no_linkedin']:,}")
        print(f"   ⏭️  Skipped (Duplicate): {self.stats['skipped_duplicate_linkedin']:,}")
        print(f"   ⏭️  Skipped (Invalid): {self.stats['skipped_invalid']:,}")
        
        print(f"\n🏢 COMPANIES:")
        print(f"   ✅ Companies Created: {self.stats['companies_created']:,}")
        print(f"   🔄 Companies Matched: {self.stats['companies_matched']:,}")
        
        print(f"\n💼 EMPLOYMENT:")
        print(f"   ✅ Employment Records Added: {self.stats['employment_records_added']:,}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for i, error in enumerate(self.stats['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more errors")
        
        # Query database for final counts
        print(f"\n📈 DATABASE TOTALS (After Import):")
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM person")
            total_people = self.cursor.fetchone()['count']
            print(f"   Total People: {total_people:,}")
            
            self.cursor.execute("SELECT COUNT(*) as count FROM company")
            total_companies = self.cursor.fetchone()['count']
            print(f"   Total Companies: {total_companies:,}")
            
            self.cursor.execute("SELECT COUNT(*) as count FROM employment")
            total_employment = self.cursor.fetchone()['count']
            print(f"   Total Employment Records: {total_employment:,}")
        except Exception as e:
            print(f"   ⚠️  Could not retrieve totals: {e}")
        
        print(f"\n{'='*80}\n")
        
        # Write report to file
        report_filename = f"clay_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(f"Clay CSV Import Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {CSV_PATH}\n\n")
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key != 'errors':
                    f.write(f"  {key}: {value}\n")
            if self.stats['errors']:
                f.write(f"\nErrors:\n")
                for error in self.stats['errors']:
                    f.write(f"  - {error}\n")
        
        print(f"📄 Full report saved to: {report_filename}")
        
        # Log to migration_log table
        try:
            log_migration_event(
                self.conn,
                migration_name='clay_csv_import',
                phase='import',
                status='completed',
                records_processed=self.stats['total_rows'],
                records_created=self.stats['profiles_created'],
                records_updated=self.stats['profiles_enriched'],
                records_skipped=(self.stats['skipped_no_linkedin'] + 
                               self.stats['skipped_duplicate_linkedin'] + 
                               self.stats['skipped_invalid']),
                metadata={
                    'source_file': CSV_PATH,
                    'companies_created': self.stats['companies_created'],
                    'employment_added': self.stats['employment_records_added']
                }
            )
        except Exception as e:
            print(f"⚠️  Could not log to migration_log: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main execution"""
    # Check if CSV exists
    if not Path(CSV_PATH).exists():
        print(f"❌ CSV file not found: {CSV_PATH}")
        return 1
    
    # Count rows
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        row_count = sum(1 for line in f) - 1  # -1 for header
    
    print(f"\n{'='*80}")
    print(f"CLAY CSV IMPORT - PRE-FLIGHT CHECK")
    print(f"{'='*80}")
    print(f"\n📄 CSV file found: {row_count:,} rows")
    print(f"⚠️  This will import/enrich up to {row_count:,} people into your database")
    print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
    
    # Show current database state
    try:
        conn = get_db_connection(use_pool=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM person")
        current_people = cursor.fetchone()['count']
        print(f"\nCurrent Database State:")
        print(f"   People: {current_people:,}")
        conn.close()
    except Exception as e:
        print(f"\n⚠️  Could not query database: {e}")
    
    print(f"\n⚠️  IMPORTANT: This will:")
    print(f"   - Create NEW people if LinkedIn Profile doesn't exist")
    print(f"   - ENRICH existing people with new data (preserves existing)")
    print(f"   - Match/create companies from 'Current Company' field")
    print(f"   - Add employment relationships")
    print(f"   - SKIP duplicates (ON CONFLICT DO NOTHING)")
    print(f"   - LOG all operations to migration_log table")
    
    response = input(f"\nProceed with import? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        return 0
    
    try:
        importer = ClayPeopleImporter()
        importer.process_csv()
        importer.generate_report()
        importer.close()
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Import interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


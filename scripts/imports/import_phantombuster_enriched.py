#!/usr/bin/env python3
"""
PhantomBuster Enriched Import Script
====================================
Imports people from PhantomBuster enrichment with full employment history

VERIFIED COMPATIBLE WITH:
- PostgreSQL 'talent' database schema
- person table (UNIQUE constraint on linkedin_url)
- employment table (full history with dates)
- education table (school information with degrees and dates)
- github_profile table (for contribution checks)
- github_contribution table (for deletion logic)

CSV Format:
- person_id, full_name, first_name, last_name, linkedin_url
- linkedinJobTitle, linkedinJobDateRange, linkedinJobLocation, companyName
- linkedinPreviousJobTitle, linkedinPreviousJobDateRange, previousCompanyName
- linkedinSchoolName, linkedinSchoolDegree, linkedinSchoolDateRange
- error (for profile deletion logic)

CRITICAL DELETION LOGIC:
- If error = "No Linkedin profile found for <slug>"
  - Check if person has GitHub contributions to tracked companies
  - If YES: Flag for manual review (don't delete)
  - If NO: Delete person record (CASCADE deletes all related data)

Author: AI Assistant
Date: October 23, 2025
"""

import sys
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import json as json_lib
from dateutil import parser as date_parser
from datetime import date

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import get_db_connection, Config

# Import data quality filters
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_quality_filters import is_valid_company_name, get_company_validation_message

# Import migration utilities
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'migration_scripts'))
    from migration_utils import (
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
                  json_lib.dumps(metadata) if metadata else None))
            conn.commit()
        except Exception as e:
            print(f"⚠️  Warning: Could not log migration event: {e}")

# CSV Configuration
CSV_PATH = "/Users/charlie.kerr/Desktop/Imports for TI Final/PhantomBuster_enriched.csv"

class PhantomBusterImporter:
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = True  # Use autocommit to avoid transaction issues
        self.cursor = self.conn.cursor()
        
        # Statistics tracking
        self.stats = {
            'total_rows': 0,
            'profiles_enriched': 0,
            'profiles_deleted': 0,
            'profiles_flagged_for_review': 0,
            'employment_records_added': 0,
            'education_records_added': 0,
            'companies_matched': 0,
            'companies_created': 0,
            'skipped_no_error_profile': 0,
            'skipped_invalid': 0,
            'errors': [],
            'deleted_person_ids': [],
            'flagged_person_ids': [],
            'enriched_people_sample': [],
            'companies_created_list': []
        }
        
        # Caches for performance (deduplication pattern)
        self.person_cache = {}  # normalized_linkedin_url -> person_id
        self.person_id_cache = {}  # person_id -> person data
        self.company_cache = {}  # company_name_lower -> company_id
        
        print("📦 Loading existing data into cache...")
        self._load_caches()
        print(f"   ✅ Loaded {len(self.person_cache):,} people, {len(self.company_cache):,} companies\n")
    
    def _load_caches(self):
        """Pre-load existing data for faster lookups (deduplication pattern)"""
        # Load people by normalized LinkedIn URL
        self.cursor.execute("""
            SELECT person_id::text, normalized_linkedin_url, full_name
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.person_cache[row['normalized_linkedin_url']] = row['person_id']
            self.person_id_cache[row['person_id']] = {'full_name': row['full_name']}
        
        # Also load by person_id for CSV matching
        self.cursor.execute("""
            SELECT person_id::text, normalized_linkedin_url, full_name
            FROM person
        """)
        for row in self.cursor.fetchall():
            pid = row['person_id']
            if pid not in self.person_id_cache:
                self.person_id_cache[pid] = {}
            self.person_id_cache[pid]['full_name'] = row['full_name']
            if row['normalized_linkedin_url']:
                self.person_id_cache[pid]['normalized_linkedin_url'] = row['normalized_linkedin_url']
        
        # Load companies by name (case-insensitive deduplication)
        self.cursor.execute("""
            SELECT LOWER(TRIM(company_name)) as name_lower, company_id::text
            FROM company
            WHERE company_name IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.company_cache[row['name_lower']] = row['company_id']
    
    def parse_date_range(self, date_range_str: str) -> Tuple[Optional[date], Optional[date]]:
        """
        Parse PhantomBuster date range like "Nov 2022 - May 2023" or "May 2021 - Present"
        Returns (start_date, end_date)
        Note: end_date will be None for current positions (e.g., "May 2021 - Present")
        """
        if not date_range_str or not date_range_str.strip():
            return None, None
        
        date_range_str = date_range_str.strip()
        
        # Check if current
        is_current = 'present' in date_range_str.lower()
        
        # Split by dash
        parts = date_range_str.split('-')
        if len(parts) != 2:
            return None, None
        
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        
        # Parse start date
        start_date = None
        try:
            parsed = date_parser.parse(start_str, fuzzy=True)
            # Use first day of month
            start_date = date(parsed.year, parsed.month, 1)
        except:
            pass
        
        # Parse end date (None for current positions)
        end_date = None
        if not is_current:
            try:
                parsed = date_parser.parse(end_str, fuzzy=True)
                # Use last day of month (approximate)
                end_date = date(parsed.year, parsed.month, 28)  # Safe approximation
            except:
                pass
        
        return start_date, end_date
    
    def parse_education_date_range(self, date_range_str: str) -> Tuple[Optional[date], Optional[date]]:
        """
        Parse education date range like "2013 - 2016"
        Returns (start_date, end_date)
        """
        if not date_range_str or not date_range_str.strip():
            return None, None
        
        date_range_str = date_range_str.strip()
        
        # Split by dash
        parts = date_range_str.split('-')
        if len(parts) != 2:
            return None, None
        
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        
        # Try to extract years
        start_year = None
        end_year = None
        
        try:
            start_year = int(re.search(r'\d{4}', start_str).group())
            start_date = date(start_year, 1, 1)
        except:
            start_date = None
        
        try:
            end_year = int(re.search(r'\d{4}', end_str).group())
            end_date = date(end_year, 12, 31)
        except:
            end_date = None
        
        return start_date, end_date
    
    def find_existing_person(self, row: Dict) -> Optional[str]:
        """Find if person already exists in database (deduplication)"""
        # First try by person_id from CSV (this CSV has person_id from our DB)
        csv_person_id = row.get('person_id', '').strip()
        if csv_person_id and csv_person_id in self.person_id_cache:
            return csv_person_id
        
        # Fallback to LinkedIn URL match
        linkedin_url = row.get('linkedin_url', '').strip()
        if not linkedin_url:
            return None
        
        # Try LinkedIn URL match (check cache first - O(1) lookup)
        normalized = normalize_linkedin_url(linkedin_url)
        if normalized and normalized in self.person_cache:
            return self.person_cache[normalized]
        
        return None
    
    def find_or_create_company(self, company_name: str) -> Optional[str]:
        """Find existing company or create new one (follows deduplication pattern)"""
        if not company_name or not company_name.strip():
            return None
        
        company_name = company_name.strip()
        
        # DATA QUALITY CHECK: Validate company name (prevents suffix-only companies)
        if not is_valid_company_name(company_name):
            error_msg = get_company_validation_message(company_name)
            self.stats['errors'].append(f"Invalid company name skipped: {error_msg}")
            return None
        
        # Case-insensitive deduplication
        name_key = company_name.lower()
        
        # Check cache (O(1) lookup)
        if name_key in self.company_cache:
            return self.company_cache[name_key]
        
        # Check database (case-insensitive)
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
        # Domain must be unique, so create placeholder
        domain_placeholder = re.sub(r'[^a-z0-9]+', '', company_name.lower())[:50] + '.placeholder'
        
        try:
            self.cursor.execute("""
                INSERT INTO company (company_id, company_name, company_domain)
                VALUES (gen_random_uuid(), %s, %s)
                ON CONFLICT (company_domain) DO UPDATE
                SET company_name = EXCLUDED.company_name
                RETURNING company_id::text
            """, (company_name, domain_placeholder))
            
            result = self.cursor.fetchone()
            if result:
                company_id = result['company_id']
                self.company_cache[name_key] = company_id
                self.stats['companies_created'] += 1
                if len(self.stats['companies_created_list']) < 20:
                    self.stats['companies_created_list'].append(company_name)
                return company_id
        except Exception as e:
            self.stats['errors'].append(f"Error creating company {company_name}: {e}")
            return None
        
        return None
    
    def has_github_contributions(self, person_id: str) -> bool:
        """Check if person has GitHub contributions to tracked companies"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as count
                FROM github_contribution gc
                JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
                WHERE gp.person_id = %s::uuid
                LIMIT 1
            """, (person_id,))
            
            result = self.cursor.fetchone()
            return result and result['count'] > 0
        except Exception as e:
            self.stats['errors'].append(f"Error checking GitHub contributions for {person_id}: {e}")
            return False
    
    def delete_person(self, person_id: str, reason: str):
        """Delete person record (CASCADE will delete all related data)"""
        try:
            person_name = self.person_id_cache.get(person_id, {}).get('full_name', 'Unknown')
            
            # Log what we're deleting
            print(f"   🗑️  Deleting: {person_name} (ID: {person_id[:8]}...) - {reason}")
            
            # Delete person (CASCADE will clean up all related tables)
            self.cursor.execute("""
                DELETE FROM person
                WHERE person_id = %s::uuid
            """, (person_id,))
            
            if self.cursor.rowcount > 0:
                self.stats['profiles_deleted'] += 1
                self.stats['deleted_person_ids'].append(person_id)
                
                # Remove from cache
                if person_id in self.person_id_cache:
                    del self.person_id_cache[person_id]
        except Exception as e:
            self.stats['errors'].append(f"Error deleting person {person_id}: {e}")
    
    def flag_for_review(self, person_id: str, reason: str):
        """Flag person for manual review (has GitHub contributions but no LinkedIn)"""
        try:
            person_name = self.person_id_cache.get(person_id, {}).get('full_name', 'Unknown')
            
            print(f"   🚩 Flagging for review: {person_name} (ID: {person_id[:8]}...) - {reason}")
            
            # Add note to person_notes table (if exists)
            try:
                self.cursor.execute("""
                    INSERT INTO person_notes (person_id, note, created_at)
                    VALUES (%s::uuid, %s, NOW())
                """, (person_id, f"FLAGGED: {reason}"))
            except Exception:
                # Table might not exist, that's okay
                pass
            
            self.stats['profiles_flagged_for_review'] += 1
            self.stats['flagged_person_ids'].append({
                'person_id': person_id,
                'name': person_name,
                'reason': reason
            })
        except Exception as e:
            self.stats['errors'].append(f"Error flagging person {person_id}: {e}")
    
    def add_employment(self, person_id: str, company_name: str, title: str, 
                      date_range: str, location: str = None):
        """Add employment record with date parsing"""
        if not company_name:
            return
        
        company_id = self.find_or_create_company(company_name)
        if not company_id:
            return
        
        # Parse dates (end_date = None means current position)
        start_date, end_date = self.parse_date_range(date_range)
        
        try:
            # Check if similar employment already exists
            self.cursor.execute("""
                SELECT employment_id
                FROM employment
                WHERE person_id = %s::uuid
                AND company_id = %s::uuid
                AND (start_date = %s OR (start_date IS NULL AND %s IS NULL))
                LIMIT 1
            """, (person_id, company_id, start_date, start_date))
            
            if not self.cursor.fetchone():
                # Insert employment (end_date = NULL means current)
                self.cursor.execute("""
                    INSERT INTO employment (
                        employment_id, person_id, company_id, title, 
                        start_date, end_date, location, date_precision
                    )
                    VALUES (
                        gen_random_uuid(), %s::uuid, %s::uuid, %s,
                        %s, %s, %s, 'month_year'
                    )
                    RETURNING employment_id
                """, (person_id, company_id, title, start_date, end_date, location))
                
                if self.cursor.fetchone():
                    self.stats['employment_records_added'] += 1
        except Exception as e:
            self.stats['errors'].append(f"Error adding employment {company_name}: {e}")
    
    def add_education(self, person_id: str, school_name: str, degree: str = None, date_range: str = None):
        """Add education record with date parsing"""
        if not school_name or not school_name.strip():
            return
        
        school_name = school_name.strip()
        
        # Parse dates
        start_date, end_date = None, None
        if date_range:
            start_date, end_date = self.parse_education_date_range(date_range)
        
        try:
            # Check if already exists
            self.cursor.execute("""
                SELECT education_id
                FROM education
                WHERE person_id = %s::uuid
                AND LOWER(TRIM(school_name)) = LOWER(TRIM(%s))
                LIMIT 1
            """, (person_id, school_name))
            
            if not self.cursor.fetchone():
                self.cursor.execute("""
                    INSERT INTO education (
                        education_id, person_id, school_name, degree,
                        start_date, end_date, date_precision
                    )
                    VALUES (
                        gen_random_uuid(), %s::uuid, %s, %s, %s, %s, 'year'
                    )
                """, (person_id, school_name, degree, start_date, end_date))
                
                if self.cursor.rowcount > 0:
                    self.stats['education_records_added'] += 1
        except Exception as e:
            self.stats['errors'].append(f"Error adding education {school_name}: {e}")
    
    def enrich_profile(self, person_id: str, row: Dict):
        """Enrich existing profile with full employment and education history"""
        updated = False
        
        # Update basic info ONLY if currently NULL (preserve existing data)
        updates = []
        params = []
        
        if row.get('firstName'):
            updates.append("first_name = COALESCE(first_name, %s)")
            params.append(row['firstName'].strip())
        
        if row.get('lastName'):
            updates.append("last_name = COALESCE(last_name, %s)")
            params.append(row['lastName'].strip())
        
        if row.get('full_name'):
            updates.append("full_name = COALESCE(full_name, %s)")
            params.append(row['full_name'].strip())
        
        if row.get('location'):
            updates.append("location = COALESCE(location, %s)")
            params.append(row['location'].strip())
        
        if row.get('linkedinHeadline'):
            updates.append("headline = COALESCE(headline, %s)")
            params.append(row['linkedinHeadline'].strip())
        
        if row.get('linkedinDescription'):
            updates.append("description = COALESCE(description, %s)")
            params.append(row['linkedinDescription'].strip())
        
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
        
        # Add current employment
        if row.get('companyName') and row.get('linkedinJobTitle'):
            self.add_employment(
                person_id,
                row['companyName'],
                row['linkedinJobTitle'],
                row.get('linkedinJobDateRange', ''),
                row.get('linkedinJobLocation')
            )
            updated = True
        
        # Add previous employment
        if row.get('previousCompanyName') and row.get('linkedinPreviousJobTitle'):
            self.add_employment(
                person_id,
                row['previousCompanyName'],
                row['linkedinPreviousJobTitle'],
                row.get('linkedinPreviousJobDateRange', ''),
                row.get('linkedinPreviousJobLocation')
            )
            updated = True
        
        # Add current education
        if row.get('linkedinSchoolName'):
            self.add_education(
                person_id,
                row['linkedinSchoolName'],
                row.get('linkedinSchoolDegree'),
                row.get('linkedinSchoolDateRange')
            )
            updated = True
        
        # Add previous education
        if row.get('linkedinPreviousSchoolName'):
            self.add_education(
                person_id,
                row['linkedinPreviousSchoolName'],
                row.get('linkedinPreviousSchoolDegree'),
                row.get('linkedinPreviousSchoolDateRange')
            )
            updated = True
        
        if updated:
            self.stats['profiles_enriched'] += 1
            person_name = self.person_id_cache.get(person_id, {}).get('full_name', 'Unknown')
            if len(self.stats['enriched_people_sample']) < 10:
                self.stats['enriched_people_sample'].append(person_name)
    
    def process_row(self, row: Dict):
        """Process a single CSV row"""
        # Check for deletion logic first
        error = row.get('error', '') or ''
        error = error.strip() if error else ''
        
        if error and 'no linkedin profile found' in error.lower():
            # Person should potentially be deleted
            person_id = self.find_existing_person(row)
            
            if person_id:
                # Check if has GitHub contributions
                if self.has_github_contributions(person_id):
                    # Flag for review - don't delete
                    self.flag_for_review(
                        person_id,
                        f"No LinkedIn profile but has GitHub contributions"
                    )
                else:
                    # Safe to delete
                    self.delete_person(person_id, "No LinkedIn profile found")
            else:
                # Person not in our database, skip
                self.stats['skipped_no_error_profile'] += 1
            
            return
        
        # Not a deletion case - proceed with enrichment
        person_id = self.find_existing_person(row)
        
        if person_id:
            # Enrich existing profile
            self.enrich_profile(person_id, row)
        else:
            # Person not found - this shouldn't happen often since CSV came from our DB
            # But skip rather than create new
            self.stats['skipped_no_error_profile'] += 1
    
    def process_csv(self):
        """Main processing loop"""
        print(f"\n{'='*80}")
        print(f"PHANTOMBUSTER ENRICHED CSV IMPORT")
        print(f"{'='*80}")
        print(f"\nSource: {CSV_PATH}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
        
        # Get database counts before import
        self.cursor.execute("SELECT COUNT(*) as count FROM person")
        people_before = self.cursor.fetchone()['count']
        self.cursor.execute("SELECT COUNT(*) as count FROM employment")
        employment_before = self.cursor.fetchone()['count']
        self.cursor.execute("SELECT COUNT(*) as count FROM education")
        education_before = self.cursor.fetchone()['count']
        
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
                
                # Process row (enrichment or deletion)
                self.process_row(row)
                
                # Progress update
                batch_count += 1
                if batch_count >= batch_size:
                    print(f"   Processed {self.stats['total_rows']:,} rows... "
                          f"({self.stats['profiles_enriched']} enriched, "
                          f"{self.stats['profiles_deleted']} deleted, "
                          f"{self.stats['profiles_flagged_for_review']} flagged)", flush=True)
                    batch_count = 0
        
        # Get database counts after import
        self.cursor.execute("SELECT COUNT(*) as count FROM person")
        people_after = self.cursor.fetchone()['count']
        self.cursor.execute("SELECT COUNT(*) as count FROM employment")
        employment_after = self.cursor.fetchone()['count']
        self.cursor.execute("SELECT COUNT(*) as count FROM education")
        education_after = self.cursor.fetchone()['count']
        
        self.stats['people_before'] = people_before
        self.stats['people_after'] = people_after
        self.stats['employment_before'] = employment_before
        self.stats['employment_after'] = employment_after
        self.stats['education_before'] = education_before
        self.stats['education_after'] = education_after
        
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
        print(f"   🔄 Profiles Enriched: {self.stats['profiles_enriched']:,}")
        print(f"   🗑️  Profiles Deleted: {self.stats['profiles_deleted']:,}")
        print(f"   🚩 Profiles Flagged for Review: {self.stats['profiles_flagged_for_review']:,}")
        print(f"   ⏭️  Skipped (Not in DB): {self.stats['skipped_no_error_profile']:,}")
        print(f"   ⏭️  Skipped (Invalid): {self.stats['skipped_invalid']:,}")
        
        if self.stats['enriched_people_sample']:
            print(f"\n   Sample of enriched profiles:")
            for name in self.stats['enriched_people_sample']:
                print(f"      • {name}")
        
        if self.stats['deleted_person_ids']:
            print(f"\n   ⚠️  Deleted person IDs (first 10):")
            for pid in self.stats['deleted_person_ids'][:10]:
                print(f"      • {pid}")
            if len(self.stats['deleted_person_ids']) > 10:
                print(f"      ... and {len(self.stats['deleted_person_ids']) - 10} more")
        
        if self.stats['flagged_person_ids']:
            print(f"\n   🚩 Flagged for review:")
            for item in self.stats['flagged_person_ids'][:10]:
                print(f"      • {item['name']} (ID: {item['person_id'][:8]}...) - {item['reason']}")
            if len(self.stats['flagged_person_ids']) > 10:
                print(f"      ... and {len(self.stats['flagged_person_ids']) - 10} more")
        
        print(f"\n🏢 COMPANIES:")
        print(f"   ✅ Companies Created: {self.stats['companies_created']:,}")
        print(f"   🔄 Companies Matched: {self.stats['companies_matched']:,}")
        
        if self.stats['companies_created_list']:
            print(f"\n   Sample of new companies:")
            for company in self.stats['companies_created_list'][:10]:
                print(f"      • {company}")
            if len(self.stats['companies_created_list']) > 10:
                print(f"      ... and {len(self.stats['companies_created_list']) - 10} more")
        
        print(f"\n💼 EMPLOYMENT:")
        print(f"   ✅ Employment Records Added: {self.stats['employment_records_added']:,}")
        
        print(f"\n🎓 EDUCATION:")
        print(f"   ✅ Education Records Added: {self.stats['education_records_added']:,}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for i, error in enumerate(self.stats['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more errors")
        
        # Database totals
        print(f"\n📈 DATABASE TOTALS:")
        print(f"   People: {self.stats['people_before']:,} → {self.stats['people_after']:,} "
              f"({self.stats['people_after'] - self.stats['people_before']:+,})")
        print(f"   Employment: {self.stats['employment_before']:,} → {self.stats['employment_after']:,} "
              f"(+{self.stats['employment_after'] - self.stats['employment_before']:,})")
        print(f"   Education: {self.stats['education_before']:,} → {self.stats['education_after']:,} "
              f"(+{self.stats['education_after'] - self.stats['education_before']:,})")
        
        print(f"\n{'='*80}\n")
        
        # Write report to file
        report_filename = f"reports/phantombuster_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = Path(__file__).parent.parent.parent / report_filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"PhantomBuster Import Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {CSV_PATH}\n\n")
            
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key not in ['errors', 'deleted_person_ids', 'flagged_person_ids', 
                              'enriched_people_sample', 'companies_created_list']:
                    f.write(f"  {key}: {value}\n")
            
            if self.stats['deleted_person_ids']:
                f.write(f"\nDeleted Person IDs ({len(self.stats['deleted_person_ids'])}):\n")
                for pid in self.stats['deleted_person_ids']:
                    f.write(f"  - {pid}\n")
            
            if self.stats['flagged_person_ids']:
                f.write(f"\nFlagged for Review ({len(self.stats['flagged_person_ids'])}):\n")
                for item in self.stats['flagged_person_ids']:
                    f.write(f"  - {item['name']} (ID: {item['person_id']}) - {item['reason']}\n")
            
            if self.stats['errors']:
                f.write(f"\nErrors:\n")
                for error in self.stats['errors']:
                    f.write(f"  - {error}\n")
        
        print(f"📄 Full report saved to: {report_filename}")
        
        # Log to migration_log table
        try:
            log_migration_event(
                self.conn,
                migration_name='phantombuster_enriched_import',
                phase='import',
                status='completed',
                records_processed=self.stats['total_rows'],
                records_created=0,  # No new people created, only enriched
                records_updated=self.stats['profiles_enriched'],
                records_skipped=(self.stats['skipped_no_error_profile'] + 
                               self.stats['skipped_invalid']),
                metadata={
                    'source_file': CSV_PATH,
                    'profiles_deleted': self.stats['profiles_deleted'],
                    'profiles_flagged': self.stats['profiles_flagged_for_review'],
                    'companies_created': self.stats['companies_created'],
                    'employment_added': self.stats['employment_records_added'],
                    'education_added': self.stats['education_records_added']
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
    print(f"PHANTOMBUSTER ENRICHED IMPORT - PRE-FLIGHT CHECK")
    print(f"{'='*80}")
    print(f"\n📄 CSV file found: {row_count:,} rows")
    print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
    
    # Show current database state
    try:
        conn = get_db_connection(use_pool=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM person")
        current_people = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM employment")
        current_employment = cursor.fetchone()['count']
        print(f"\nCurrent Database State:")
        print(f"   People: {current_people:,}")
        print(f"   Employment Records: {current_employment:,}")
        conn.close()
    except Exception as e:
        print(f"\n⚠️  Could not query database: {e}")
    
    print(f"\n⚠️  CRITICAL IMPORT FEATURES:")
    print(f"   ✅ Enrich existing people with full employment history")
    print(f"   ✅ Parse date ranges (e.g., 'Nov 2022 - May 2023')")
    print(f"   ✅ Add education with degrees and dates")
    print(f"   🗑️  DELETE profiles with 'No Linkedin profile found' error")
    print(f"   🚩 BUT FLAG for review if they have GitHub contributions")
    print(f"   ✅ Data quality validation (no suffix-only companies)")
    print(f"   ✅ Deduplication via caching and constraints")
    
    print(f"\n⚠️  DELETION WARNING:")
    print(f"   This import will DELETE profiles that:")
    print(f"   - Have error 'No Linkedin profile found for <slug>'")
    print(f"   - Do NOT have GitHub contributions to tracked companies")
    print(f"   - CASCADE delete will remove ALL related data (emails, employment, etc.)")
    
    response = input(f"\nProceed with import (including deletions)? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        return 0
    
    try:
        importer = PhantomBusterImporter()
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


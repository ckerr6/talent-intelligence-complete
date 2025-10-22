#!/usr/bin/env python3
"""
CSV Import and Profile Enrichment Script
=========================================
Imports people from dedupe_PB_test.csv and enriches existing profiles

VERIFIED COMPATIBLE WITH:
- PostgreSQL 'talent' database schema (post-migration Oct 2025)
- person_email table (unique on person_id + lower(email))
- github_profile table (unique on github_username)  
- person.linkedin_url (UNIQUE constraint)
- migration_log tracking
- migration_utils.py helper functions

Author: AI Assistant
Date: October 21, 2025
Verified Against: Project structure, migration scripts, existing patterns
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

# Import migration utilities
try:
    from migration_scripts.migration_utils import (
        normalize_linkedin_url,
        normalize_email,
        validate_email,
        infer_email_type,
        log_migration_event,
        print_progress
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
    
    def normalize_email(email: str) -> Optional[str]:
        """Fallback email normalization"""
        if not email or not email.strip():
            return None
        email = email.lower().strip()
        if '@' not in email:
            return None
        return email
    
    def validate_email(email: str) -> bool:
        """Fallback email validation"""
        return bool(email and '@' in email and '.' in email.split('@')[1])
    
    def infer_email_type(email: str, github_email: str = None) -> str:
        """Fallback email type inference"""
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        for domain in personal_domains:
            if email.lower().endswith(f'@{domain}'):
                return 'personal'
        return 'work'
    
    def log_migration_event(conn, migration_name: str, phase: str, status: str,
                            records_processed: int = 0, records_created: int = 0,
                            records_updated: int = 0, records_skipped: int = 0,
                            error_message: str = None, metadata: dict = None):
        """Fallback migration logging"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO migration_log 
            (migration_name, migration_phase, status, records_processed, records_created,
             records_updated, records_skipped, error_message, completed_at, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (migration_name, phase, status, records_processed, records_created,
              records_updated, records_skipped, error_message,
              json.dumps(metadata) if metadata else None))
        conn.commit()
    
    def print_progress(current: int, total: int, prefix: str = 'Progress'):
        """Fallback progress printer"""
        if total == 0:
            return
        percent = current / total * 100
        if current % 100 == 0 or current == total:
            print(f'{prefix}: {current:,}/{total:,} ({percent:.1f}%)', flush=True)

# CSV Configuration
CSV_PATH = "/Users/charlie.kerr/DataBlend1021/dedupe_PB_test.csv"

class ProfileImporter:
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)  # Direct connection for transaction control
        self.conn.autocommit = True  # Use autocommit to avoid transaction issues
        self.cursor = self.conn.cursor()
        
        # Statistics tracking
        self.stats = {
            'total_rows': 0,
            'profiles_enriched': 0,
            'profiles_created': 0,
            'github_only_profiles': 0,
            'linkedin_only_profiles': 0,
            'profiles_needing_enrichment': 0,
            'github_matched_existing': 0,
            'github_matched_new': 0,
            'github_conflicts': 0,
            'emails_added': 0,
            'employment_records_added': 0,
            'skipped_invalid': 0,
            'skipped_duplicate_linkedin': 0,
            'errors': []
        }
        
        # Caches for performance
        self.person_cache = {}  # normalized_linkedin_url -> person_id
        self.github_cache = {}  # github_username -> (person_id, github_profile_id)
        self.company_cache = {}  # company_name_lower -> company_id
        
        self._load_caches()
    
    def _load_caches(self):
        """Pre-load existing data for faster lookups"""
        print("📦 Loading database caches...")
        
        try:
            # Load existing people by normalized LinkedIn URL
            self.cursor.execute("""
                SELECT person_id::text, normalized_linkedin_url
                FROM person
                WHERE normalized_linkedin_url IS NOT NULL AND normalized_linkedin_url != ''
            """)
            for row in self.cursor.fetchall():
                self.person_cache[row['normalized_linkedin_url']] = row['person_id']
            
            print(f"   ✓ Loaded {len(self.person_cache):,} people by LinkedIn")
        except Exception as e:
            print(f"   ❌ Error loading people cache: {e}")
            raise
        
        # Load existing GitHub profiles
        self.cursor.execute("""
            SELECT github_profile_id::text, person_id::text, LOWER(github_username) as github_username
            FROM github_profile
            WHERE github_username IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.github_cache[row['github_username']] = (
                row['person_id'],
                row['github_profile_id']
            )
        
        print(f"   ✓ Loaded {len(self.github_cache):,} GitHub profiles")
        
        # Load existing companies
        self.cursor.execute("""
            SELECT company_id::text, company_name
            FROM company
            WHERE company_name IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            name_key = row['company_name'].lower().strip()
            self.company_cache[name_key] = row['company_id']
        
        print(f"   ✓ Loaded {len(self.company_cache):,} companies\n")
    
    def extract_github_username(self, url: str) -> Optional[str]:
        """Extract GitHub username from URL"""
        if not url or not url.strip():
            return None
        
        url = url.strip()
        url = re.sub(r'^https?://(www\.)?', '', url)
        
        match = re.search(r'github\.com/([^/?#]+)', url)
        if match:
            username = match.group(1)
            # Skip organization-like paths
            if username not in ['orgs', 'organizations', 'repos', 'settings', 'tab', 'overview', 'from']:
                return username
        
        return None
    
    def split_emails(self, email_string: str) -> List[str]:
        """Split multiple emails by semicolon and validate"""
        if not email_string or not email_string.strip():
            return []
        
        emails = []
        for email in email_string.split(';'):
            email = email.strip()
            if validate_email(email):
                emails.append(normalize_email(email))
        
        return emails
    
    def find_existing_person(self, row: Dict) -> Optional[str]:
        """Find if person already exists in database"""
        
        # 1. Try LinkedIn URL match (most reliable - check cache first)
        if row.get('LinkedIn URL'):
            normalized = normalize_linkedin_url(row['LinkedIn URL'])
            if normalized and normalized in self.person_cache:
                return self.person_cache[normalized]
        
        # 2. Try GitHub username match
        if row.get('GitHub URL'):
            github_username = self.extract_github_username(row['GitHub URL'])
            if github_username:
                github_lower = github_username.lower()
                if github_lower in self.github_cache:
                    person_id, _ = self.github_cache[github_lower]
                    if person_id:  # Only if GitHub profile is linked to a person
                        return person_id
        
        # Skip name+company lookup to avoid transaction issues
        # Rely only on LinkedIn/GitHub matching which uses cache
        
        return None
    
    def find_or_create_company(self, company_name: str) -> Optional[str]:
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
            return company_id
        
        # Create new company (generate UUID, use placeholder domain)
        # Domain must be unique, so create from company name
        import re
        domain_placeholder = re.sub(r'[^a-z0-9]+', '', company_name.lower())[:50] + '.placeholder'
        
        self.cursor.execute("""
            INSERT INTO company (company_id, company_name, company_domain)
            VALUES (gen_random_uuid(), %s, %s)
            ON CONFLICT (company_domain) DO UPDATE
            SET company_name = EXCLUDED.company_name
            RETURNING company_id::text
        """, (company_name, domain_placeholder))
        
        company_id = self.cursor.fetchone()['company_id']
        self.company_cache[name_key] = company_id
        
        return company_id
    
    def enrich_existing_profile(self, person_id: str, row: Dict):
        """Enrich an existing profile with new data"""
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
            self.cursor.execute(sql, params)
            if self.cursor.rowcount > 0:
                updated = True
        
        # Add emails (ON CONFLICT DO NOTHING handles duplicates)
        emails = self.split_emails(row.get('Emails', ''))
        for i, email in enumerate(emails):
            if email:
                try:
                    email_type = infer_email_type(email)
                    self.cursor.execute("""
                        INSERT INTO person_email (person_id, email, email_type, is_primary, source, verified)
                        VALUES (%s::uuid, %s, %s, %s, 'csv_datablend_oct2024', FALSE)
                        ON CONFLICT (person_id, lower(email)) DO NOTHING
                        RETURNING email_id
                    """, (person_id, email, email_type, i == 0))
                    
                    result = self.cursor.fetchone()
                    if result:
                        self.stats['emails_added'] += 1
                        updated = True
                except Exception as e:
                    self.stats['errors'].append(f"Error adding email {email}: {e}")
        
        # Add/link GitHub profile
        if row.get('GitHub URL'):
            github_username = self.extract_github_username(row['GitHub URL'])
            if github_username:
                try:
                    github_lower = github_username.lower()
                    
                    # Check if GitHub username already exists
                    if github_lower in self.github_cache:
                        existing_person_id, github_profile_id = self.github_cache[github_lower]
                        
                        if existing_person_id is None:
                            # Unmatched GitHub profile - link it to this person
                            self.cursor.execute("""
                                UPDATE github_profile
                                SET person_id = %s::uuid, source = 'csv_datablend_oct2024'
                                WHERE github_profile_id = %s::uuid
                                RETURNING github_profile_id
                            """, (person_id, github_profile_id))
                            
                            if self.cursor.fetchone():
                                self.stats['github_matched_existing'] += 1
                                self.github_cache[github_lower] = (person_id, github_profile_id)
                                updated = True
                        elif existing_person_id != person_id:
                            # Conflict: GitHub already linked to different person
                            self.stats['github_conflicts'] += 1
                    else:
                        # Create new GitHub profile
                        self.cursor.execute("""
                            INSERT INTO github_profile (person_id, github_username, source)
                            VALUES (%s::uuid, %s, 'csv_datablend_oct2024')
                            ON CONFLICT (github_username) DO NOTHING
                            RETURNING github_profile_id::text
                        """, (person_id, github_username))
                        
                        result = self.cursor.fetchone()
                        if result:
                            self.stats['github_matched_existing'] += 1
                            self.github_cache[github_lower] = (person_id, result['github_profile_id'])
                            updated = True
                        
                except Exception as e:
                    self.stats['errors'].append(f"Error adding GitHub {github_username}: {e}")
        
        # Add employment record if doesn't exist
        if row.get('Company'):
            company_id = self.find_or_create_company(row['Company'])
            if company_id:
                try:
                    # Check if employment already exists
                    self.cursor.execute("""
                        SELECT employment_id
                        FROM employment
                        WHERE person_id = %s::uuid 
                        AND company_id = %s::uuid
                        LIMIT 1
                    """, (person_id, company_id))
                    
                    if not self.cursor.fetchone():
                        # Insert employment
                        self.cursor.execute("""
                            INSERT INTO employment (employment_id, person_id, company_id, title)
                            VALUES (gen_random_uuid(), %s::uuid, %s::uuid, %s)
                            RETURNING employment_id
                        """, (person_id, company_id, row.get('Job Title')))
                        
                        if self.cursor.fetchone():
                            self.stats['employment_records_added'] += 1
                            updated = True
                except Exception as e:
                    self.stats['errors'].append(f"Error adding employment: {e}")
        
        if updated:
            self.stats['profiles_enriched'] += 1
    
    def create_new_profile(self, row: Dict):
        """Create a new profile from CSV row - accepts LinkedIn OR GitHub"""
        try:
            # Get all available identifiers
            full_name = row.get('Full Name', '').strip()
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            linkedin_url = row.get('LinkedIn URL', '').strip()
            github_url = row.get('GitHub URL', '').strip()
            
            # Build full name from parts if not provided
            if not full_name and (first_name or last_name):
                full_name = f"{first_name or ''} {last_name or ''}".strip()
            
            # Generate placeholder name if completely missing
            is_placeholder_name = False
            needs_enrichment = False
            
            if not full_name:
                # Create placeholder from LinkedIn or GitHub
                if linkedin_url:
                    # Extract username from LinkedIn URL
                    linkedin_username = linkedin_url.rstrip('/').split('/')[-1].replace('-', ' ').title()
                    full_name = f"[LinkedIn] {linkedin_username}"
                    is_placeholder_name = True
                    needs_enrichment = True
                elif github_url:
                    github_username = self.extract_github_username(github_url)
                    if github_username:
                        full_name = f"[GitHub] {github_username}"
                        is_placeholder_name = True
                        needs_enrichment = True
                    else:
                        full_name = "[Unknown Profile]"
                        is_placeholder_name = True
                        needs_enrichment = True
                else:
                    # Should not reach here, but handle gracefully
                    self.stats['skipped_invalid'] += 1
                    return
            
            # Normalize LinkedIn URL
            normalized_linkedin = normalize_linkedin_url(linkedin_url) if linkedin_url else None
            
            # Track profile type
            if not linkedin_url and github_url:
                self.stats['github_only_profiles'] += 1
            elif linkedin_url and not github_url:
                self.stats['linkedin_only_profiles'] += 1
            
            if needs_enrichment:
                self.stats['profiles_needing_enrichment'] += 1
            
            # Insert person (handle UNIQUE constraint on linkedin_url)
            try:
                # For GitHub-only profiles, LinkedIn URL will be NULL
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
                    linkedin_url or None,
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
            
            # Add emails
            emails = self.split_emails(row.get('Emails', ''))
            for i, email in enumerate(emails):
                if email:
                    try:
                        email_type = infer_email_type(email)
                        self.cursor.execute("""
                            INSERT INTO person_email (person_id, email, email_type, is_primary, source, verified)
                            VALUES (%s::uuid, %s, %s, %s, 'csv_datablend_oct2024', FALSE)
                        """, (person_id, email, email_type, i == 0))
                        self.stats['emails_added'] += 1
                    except Exception as e:
                        self.stats['errors'].append(f"Error adding email {email}: {e}")
            
            # Add GitHub profile
            if row.get('GitHub URL'):
                github_username = self.extract_github_username(row['GitHub URL'])
                if github_username:
                    try:
                        self.cursor.execute("""
                            INSERT INTO github_profile (person_id, github_username, source)
                            VALUES (%s::uuid, %s, 'csv_datablend_oct2024')
                            ON CONFLICT (github_username) DO NOTHING
                            RETURNING github_profile_id::text
                        """, (person_id, github_username))
                        
                        result = self.cursor.fetchone()
                        if result:
                            self.stats['github_matched_new'] += 1
                            self.github_cache[github_username.lower()] = (person_id, result['github_profile_id'])
                    except Exception as e:
                        self.stats['errors'].append(f"Error adding GitHub {github_username}: {e}")
            
            # Add employment
            if row.get('Company'):
                company_id = self.find_or_create_company(row['Company'])
                if company_id:
                    try:
                        self.cursor.execute("""
                            INSERT INTO employment (employment_id, person_id, company_id, title)
                            VALUES (gen_random_uuid(), %s::uuid, %s::uuid, %s)
                        """, (person_id, company_id, row.get('Job Title')))
                        self.stats['employment_records_added'] += 1
                    except Exception as e:
                        self.stats['errors'].append(f"Error adding employment: {e}")
            
            self.stats['profiles_created'] += 1
            
        except Exception as e:
            self.stats['errors'].append(f"Error creating profile for {row.get('Full Name', 'unknown')}: {e}")
            self.stats['skipped_invalid'] += 1
    
    def process_csv(self):
        """Main processing loop"""
        print(f"\n{'='*80}")
        print(f"CSV IMPORT AND PROFILE ENRICHMENT")
        print(f"{'='*80}")
        print(f"\nSource: {CSV_PATH}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
        
        # Skip logging for now to avoid transaction issues
        # Will log at the end
        
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
                
                # Only requirement: LinkedIn URL OR GitHub URL
                linkedin_url = row.get('LinkedIn URL', '').strip()
                github_url = row.get('GitHub URL', '').strip()
                
                if not linkedin_url and not github_url:
                    self.stats['skipped_invalid'] += 1
                    continue
                
                # Check if person exists
                person_id = self.find_existing_person(row)
                
                if person_id:
                    # Enrich existing profile
                    self.enrich_existing_profile(person_id, row)
                else:
                    # Create new profile (even with just LinkedIn or GitHub)
                    self.create_new_profile(row)
                
                # Progress update
                batch_count += 1
                if batch_count >= batch_size:
                    batch_count = 0
                    
                    # Progress update
                    if self.stats['total_rows'] % 1000 == 0:
                        print_progress(
                            self.stats['total_rows'],
                            self.stats['total_rows'],  # We don't know total yet
                            f"Processed {self.stats['total_rows']:,} rows"
                        )
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate comprehensive import report"""
        print(f"\n{'='*80}")
        print(f"IMPORT REPORT")
        print(f"{'='*80}")
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Source File: {CSV_PATH}")
        
        print(f"\n📊 PROCESSING STATISTICS:")
        print(f"   Total Rows Processed: {self.stats['total_rows']:,}")
        print(f"   Skipped (Invalid/Empty): {self.stats['skipped_invalid']:,}")
        print(f"   Skipped (Duplicate LinkedIn): {self.stats['skipped_duplicate_linkedin']:,}")
        print(f"   Valid Records: {self.stats['total_rows'] - self.stats['skipped_invalid'] - self.stats['skipped_duplicate_linkedin']:,}")
        
        print(f"\n👤 PROFILE CHANGES:")
        print(f"   Existing Profiles Enriched: {self.stats['profiles_enriched']:,}")
        print(f"   New Profiles Created: {self.stats['profiles_created']:,}")
        print(f"   Total Profiles Affected: {self.stats['profiles_enriched'] + self.stats['profiles_created']:,}")
        
        print(f"\n🆕 NEW PROFILE TYPES:")
        print(f"   GitHub-Only Profiles: {self.stats['github_only_profiles']:,}")
        print(f"   LinkedIn-Only Profiles: {self.stats['linkedin_only_profiles']:,}")
        print(f"   Profiles Marked for Enrichment: {self.stats['profiles_needing_enrichment']:,}")
        
        print(f"\n📧 EMAIL ADDITIONS:")
        print(f"   Emails Added: {self.stats['emails_added']:,}")
        
        print(f"\n💼 EMPLOYMENT RECORDS:")
        print(f"   Employment Records Added: {self.stats['employment_records_added']:,}")
        
        print(f"\n🔗 GITHUB MATCHING:")
        print(f"   GitHub Profiles Linked to Existing People: {self.stats['github_matched_existing']:,}")
        print(f"   GitHub Profiles Added to New People: {self.stats['github_matched_new']:,}")
        print(f"   GitHub Conflicts (already linked): {self.stats['github_conflicts']:,}")
        print(f"   Total GitHub Matches: {self.stats['github_matched_existing'] + self.stats['github_matched_new']:,}")
        
        # Calculate enrichment rate
        valid_records = self.stats['total_rows'] - self.stats['skipped_invalid'] - self.stats['skipped_duplicate_linkedin']
        if valid_records > 0:
            enrichment_rate = (self.stats['profiles_enriched'] / valid_records) * 100
            creation_rate = (self.stats['profiles_created'] / valid_records) * 100
            
            print(f"\n📈 ENRICHMENT METRICS:")
            print(f"   Enrichment Rate: {enrichment_rate:.1f}%")
            print(f"   New Profile Rate: {creation_rate:.1f}%")
        
        # Get updated database stats
        self.cursor.execute("""
            SELECT 
                COUNT(DISTINCT person_id) as total_people,
                COUNT(DISTINCT CASE WHEN linkedin_url IS NOT NULL THEN person_id END) as with_linkedin
            FROM person
        """)
        db_stats = self.cursor.fetchone()
        
        self.cursor.execute("SELECT COUNT(*) as cnt FROM person_email")
        email_count = self.cursor.fetchone()['cnt']
        
        self.cursor.execute("SELECT COUNT(*) as cnt FROM github_profile WHERE person_id IS NOT NULL")
        github_count = self.cursor.fetchone()['cnt']
        
        print(f"\n🗄️  UPDATED DATABASE TOTALS:")
        print(f"   Total People: {db_stats['total_people']:,}")
        print(f"   With LinkedIn: {db_stats['with_linkedin']:,}")
        print(f"   Total Emails: {email_count:,}")
        print(f"   Total GitHub Profiles (matched): {github_count:,}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ENCOUNTERED: {len(self.stats['errors'])}")
            print(f"   (Showing first 20)")
            for error in self.stats['errors'][:20]:
                print(f"   - {error}")
        
        print(f"\n{'='*80}")
        print(f"✅ IMPORT COMPLETE")
        print(f"{'='*80}\n")
        
        # Log completion (with error handling)
        try:
            log_migration_event(
                self.conn,
                'csv_datablend_import',
                'csv_import',
                'completed',
                records_processed=self.stats['total_rows'],
                records_created=self.stats['profiles_created'],
                records_updated=self.stats['profiles_enriched'],
                records_skipped=self.stats['skipped_invalid'] + self.stats['skipped_duplicate_linkedin'],
                metadata=self.stats
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not log migration completion: {e}")
        
        # Save detailed report to file
        report_file = Path(__file__).parent / f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(f"CSV Import Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Source: {CSV_PATH}\n\n")
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key != 'errors':
                    f.write(f"  {key}: {value}\n")
            f.write(f"\nErrors ({len(self.stats['errors'])}):\n")
            for error in self.stats['errors']:
                f.write(f"  - {error}\n")
        
        print(f"📄 Detailed report saved to: {report_file}\n")
    
    def close(self):
        """Clean up database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main execution"""
    # Check if CSV exists
    if not Path(CSV_PATH).exists():
        print(f"❌ CSV file not found: {CSV_PATH}")
        return 1
    
    # Count rows
    with open(CSV_PATH, 'r') as f:
        row_count = sum(1 for line in f) - 1  # -1 for header
    
    print(f"\n📄 CSV file found: {row_count:,} rows")
    print(f"⚠️  This will import/enrich up to {row_count:,} people into your database")
    print(f"\nDatabase: {Config.PG_DATABASE}@{Config.PG_HOST}")
    print(f"\n⚠️  IMPORTANT: This will:")
    print(f"   - Create NEW people if LinkedIn URL doesn't exist")
    print(f"   - ENRICH existing people with emails, GitHub, employment")
    print(f"   - SKIP duplicates (ON CONFLICT DO NOTHING)")
    print(f"   - LOG all operations to migration_log table")
    
    response = input(f"\nProceed with import? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        return 0
    
    try:
        importer = ProfileImporter()
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


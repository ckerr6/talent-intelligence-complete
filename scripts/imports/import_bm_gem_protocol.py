#!/usr/bin/env python3
"""
BM Gem Protocol Import Script
==============================
Imports people from BM_Gem_Protocol_BE_FE.csv with full contact info

VERIFIED COMPATIBLE WITH:
- PostgreSQL 'talent' database schema
- person table (UNIQUE constraint on linkedin_url)
- person_email table (multiple emails per person)
- github_profile table (GitHub profiles)
- twitter_profile table (Twitter/X profiles)
- education table (school information)
- employment table (job history)
- company table (companies)

CSV Format:
- Primary Email, First Name, Last Name, Company, School
- LinkedIn, Title, Location, All Emails (JSON array)
- Twitter/X, Website/Blog, Github

Author: AI Assistant
Date: October 23, 2025
"""

import sys
import csv
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import json as json_lib

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
        normalize_email,
        validate_email,
        infer_email_type,
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
CSV_PATH = "/Users/charlie.kerr/Desktop/Imports for TI Final/BM_Gem_Protocol_BE_FE.csv"

class BMGemImporter:
    def __init__(self, csv_path=None):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = True  # Use autocommit to avoid transaction issues
        self.cursor = self.conn.cursor()
        self.csv_path = csv_path or CSV_PATH
        
        # Statistics tracking
        self.stats = {
            'total_rows': 0,
            'profiles_enriched': 0,
            'profiles_created': 0,
            'employment_records_added': 0,
            'education_records_added': 0,
            'emails_added': 0,
            'github_profiles_added': 0,
            'twitter_profiles_added': 0,
            'companies_matched': 0,
            'companies_created': 0,
            'skipped_no_linkedin': 0,
            'skipped_duplicate_linkedin': 0,
            'skipped_invalid': 0,
            'errors': [],
            'created_people_sample': [],
            'companies_created_list': []
        }
        
        # Caches for performance (deduplication pattern)
        self.person_cache = {}  # normalized_linkedin_url -> person_id
        self.company_cache = {}  # company_name_lower -> company_id
        
        print("📦 Loading existing data into cache...")
        self._load_caches()
        print(f"   ✅ Loaded {len(self.person_cache):,} people, {len(self.company_cache):,} companies\n")
    
    def _load_caches(self):
        """Pre-load existing data for faster lookups (deduplication pattern)"""
        # Load people by normalized LinkedIn URL
        self.cursor.execute("""
            SELECT normalized_linkedin_url, person_id::text
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.person_cache[row['normalized_linkedin_url']] = row['person_id']
        
        # Load companies by name (case-insensitive deduplication)
        self.cursor.execute("""
            SELECT LOWER(TRIM(company_name)) as name_lower, company_id::text
            FROM company
            WHERE company_name IS NOT NULL
        """)
        for row in self.cursor.fetchall():
            self.company_cache[row['name_lower']] = row['company_id']
    
    def parse_email_array(self, email_str: str) -> List[str]:
        """Parse the All Emails field which is a JSON-like array"""
        if not email_str or not email_str.strip():
            return []
        
        email_str = email_str.strip()
        
        # Try to parse as JSON
        try:
            emails = json.loads(email_str)
            if isinstance(emails, list):
                return [e.strip() for e in emails if e and e.strip()]
        except json.JSONDecodeError:
            pass
        
        # Fallback: try to extract emails with regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, email_str)
        return emails if emails else []
    
    def extract_github_username(self, github_url: str) -> Optional[str]:
        """Extract GitHub username from URL"""
        if not github_url or not github_url.strip():
            return None
        
        github_url = github_url.strip()
        
        # Handle various GitHub URL formats
        # https://github.com/username
        # github.com/username
        # www.github.com/username
        match = re.search(r'github\.com/([a-zA-Z0-9_-]+)', github_url, re.IGNORECASE)
        if match:
            username = match.group(1)
            # Filter out common non-username paths
            if username.lower() not in ['explore', 'trending', 'features', 'enterprise']:
                return username
        
        return None
    
    def extract_twitter_username(self, twitter_url: str) -> Optional[str]:
        """Extract Twitter/X username from URL"""
        if not twitter_url or not twitter_url.strip():
            return None
        
        twitter_url = twitter_url.strip()
        
        # Handle various Twitter/X URL formats
        # https://twitter.com/username
        # https://x.com/username
        # twitter.com/username
        match = re.search(r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)', twitter_url, re.IGNORECASE)
        if match:
            username = match.group(1)
            # Filter out common non-username paths
            if username.lower() not in ['home', 'explore', 'notifications', 'messages', 'settings']:
                return username
        
        return None
    
    def find_existing_person(self, row: Dict) -> Optional[str]:
        """Find if person already exists in database by LinkedIn URL (deduplication)"""
        linkedin_url = row.get('LinkedIn', '').strip()
        
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
                self.stats['companies_created_list'].append(company_name)
                return company_id
        except Exception as e:
            self.stats['errors'].append(f"Error creating company {company_name}: {e}")
            return None
        
        return None
    
    def add_emails(self, person_id: str, primary_email: str, all_emails_str: str):
        """Add emails to person_email table"""
        emails_to_add = set()
        
        # Add primary email
        if primary_email and primary_email.strip():
            normalized = normalize_email(primary_email.strip())
            if normalized and validate_email(normalized):
                emails_to_add.add((normalized, True))  # is_primary=True
        
        # Parse and add all emails
        all_emails = self.parse_email_array(all_emails_str)
        for email in all_emails:
            normalized = normalize_email(email)
            if normalized and validate_email(normalized):
                # Only mark as primary if it's the primary email
                is_primary = (normalized == normalize_email(primary_email.strip()) if primary_email else False)
                emails_to_add.add((normalized, is_primary))
        
        # Insert emails (ON CONFLICT for deduplication)
        for email, is_primary in emails_to_add:
            try:
                email_type = infer_email_type(email)
                
                self.cursor.execute("""
                    INSERT INTO person_email (person_id, email, email_type, is_primary)
                    VALUES (%s::uuid, %s, %s, %s)
                    ON CONFLICT (person_id, LOWER(email)) DO NOTHING
                """, (person_id, email, email_type, is_primary))
                
                if self.cursor.rowcount > 0:
                    self.stats['emails_added'] += 1
            except Exception as e:
                self.stats['errors'].append(f"Error adding email {email}: {e}")
    
    def add_github_profile(self, person_id: str, github_url: str, website_blog: str = None):
        """Add GitHub profile"""
        username = self.extract_github_username(github_url)
        if not username:
            return
        
        try:
            # Check if already exists
            self.cursor.execute("""
                SELECT github_profile_id
                FROM github_profile
                WHERE github_username = %s
                LIMIT 1
            """, (username,))
            
            existing = self.cursor.fetchone()
            
            if existing:
                # Update person_id if NULL
                self.cursor.execute("""
                    UPDATE github_profile
                    SET person_id = %s::uuid,
                        blog = COALESCE(blog, %s)
                    WHERE github_username = %s
                    AND person_id IS NULL
                """, (person_id, website_blog, username))
            else:
                # Insert new profile (ON CONFLICT for unique username)
                self.cursor.execute("""
                    INSERT INTO github_profile (person_id, github_username, blog, source)
                    VALUES (%s::uuid, %s, %s, 'bm_gem_import')
                    ON CONFLICT (github_username) DO UPDATE
                    SET person_id = COALESCE(github_profile.person_id, EXCLUDED.person_id),
                        blog = COALESCE(github_profile.blog, EXCLUDED.blog)
                    RETURNING github_profile_id
                """, (person_id, username, website_blog))
                
                if self.cursor.fetchone():
                    self.stats['github_profiles_added'] += 1
        except Exception as e:
            self.stats['errors'].append(f"Error adding GitHub profile {username}: {e}")
    
    def add_twitter_profile(self, person_id: str, twitter_url: str):
        """Add Twitter/X profile"""
        username = self.extract_twitter_username(twitter_url)
        if not username:
            return
        
        try:
            # Generate twitter_id from username hash (simple approach)
            twitter_id = abs(hash(username.lower())) % (10 ** 15)
            
            self.cursor.execute("""
                INSERT INTO twitter_profile (twitter_id, person_id, username)
                VALUES (%s, %s::uuid, %s)
                ON CONFLICT (twitter_id) DO UPDATE
                SET person_id = COALESCE(twitter_profile.person_id, EXCLUDED.person_id),
                    username = EXCLUDED.username
            """, (twitter_id, person_id, username))
            
            if self.cursor.rowcount > 0:
                self.stats['twitter_profiles_added'] += 1
        except Exception as e:
            self.stats['errors'].append(f"Error adding Twitter profile {username}: {e}")
    
    def add_education(self, person_id: str, school_name: str):
        """Add education record"""
        if not school_name or not school_name.strip():
            return
        
        school_name = school_name.strip()
        
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
                    INSERT INTO education (education_id, person_id, school_name)
                    VALUES (gen_random_uuid(), %s::uuid, %s)
                """, (person_id, school_name))
                
                if self.cursor.rowcount > 0:
                    self.stats['education_records_added'] += 1
        except Exception as e:
            self.stats['errors'].append(f"Error adding education {school_name}: {e}")
    
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
        
        # Build full name if not exists
        if not row.get('Full Name') and (row.get('First Name') or row.get('Last Name')):
            full_name = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()
            if full_name:
                updates.append("full_name = COALESCE(full_name, %s)")
                params.append(full_name)
        
        if row.get('Location'):
            updates.append("location = COALESCE(location, %s)")
            params.append(row['Location'].strip())
        
        if row.get('Title'):
            updates.append("headline = COALESCE(headline, %s)")
            params.append(row['Title'].strip())
        
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
        
        # Add emails
        self.add_emails(person_id, row.get('Primary Email', ''), row.get('All Emails', ''))
        
        # Add employment record if company exists
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
                        # Insert employment (end_date = NULL means current)
                        self.cursor.execute("""
                            INSERT INTO employment (employment_id, person_id, company_id, title)
                            VALUES (gen_random_uuid(), %s::uuid, %s::uuid, %s)
                            RETURNING employment_id
                        """, (person_id, company_id, row.get('Title')))
                        
                        if self.cursor.fetchone():
                            self.stats['employment_records_added'] += 1
                            updated = True
                except Exception as e:
                    self.stats['errors'].append(f"Error adding employment: {e}")
        
        # Add GitHub profile
        if row.get('Github'):
            self.add_github_profile(person_id, row['Github'], row.get('Website / Blog'))
            updated = True
        
        # Add Twitter profile
        if row.get('Twiiter / X'):  # Note: typo in CSV header
            self.add_twitter_profile(person_id, row['Twiiter / X'])
            updated = True
        
        # Add education
        if row.get('School'):
            self.add_education(person_id, row['School'])
            updated = True
        
        if updated:
            self.stats['profiles_enriched'] += 1
    
    def create_new_profile(self, row: Dict):
        """Create a new profile from CSV row"""
        try:
            # Get data from CSV
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            linkedin_url = row.get('LinkedIn', '').strip()
            
            # Build full name
            full_name = f"{first_name} {last_name}".strip()
            
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
                    row.get('Title') or None
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
            
            # Cache it (deduplication)
            if normalized_linkedin:
                self.person_cache[normalized_linkedin] = person_id
            
            # Track sample
            if len(self.stats['created_people_sample']) < 10:
                self.stats['created_people_sample'].append(full_name)
            
            # Add emails
            self.add_emails(person_id, row.get('Primary Email', ''), row.get('All Emails', ''))
            
            # Add employment
            if row.get('Company'):
                company_id = self.find_or_create_company(row['Company'])
                
                if company_id:
                    try:
                        # Insert employment (end_date = NULL means current)
                        self.cursor.execute("""
                            INSERT INTO employment (employment_id, person_id, company_id, title)
                            VALUES (gen_random_uuid(), %s::uuid, %s::uuid, %s)
                        """, (person_id, company_id, row.get('Title')))
                        self.stats['employment_records_added'] += 1
                    except Exception as e:
                        self.stats['errors'].append(f"Error adding employment: {e}")
            
            # Add GitHub profile
            if row.get('Github'):
                self.add_github_profile(person_id, row['Github'], row.get('Website / Blog'))
            
            # Add Twitter profile
            if row.get('Twiiter / X'):  # Note: typo in CSV header
                self.add_twitter_profile(person_id, row['Twiiter / X'])
            
            # Add education
            if row.get('School'):
                self.add_education(person_id, row['School'])
            
            self.stats['profiles_created'] += 1
            
        except Exception as e:
            self.stats['errors'].append(f"Error processing row: {e}")
            self.stats['skipped_invalid'] += 1
    
    def process_csv(self):
        """Main processing loop"""
        print(f"\n{'='*80}")
        print(f"BM GEM PROTOCOL CSV IMPORT")
        print(f"{'='*80}")
        print(f"\nSource: {self.csv_path}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
        
        # Get database counts before import
        self.cursor.execute("SELECT COUNT(*) as count FROM person")
        people_before = self.cursor.fetchone()['count']
        self.cursor.execute("SELECT COUNT(*) as count FROM company")
        companies_before = self.cursor.fetchone()['count']
        
        # Read and process CSV
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            batch_size = 100
            batch_count = 0
            
            for row in reader:
                self.stats['total_rows'] += 1
                
                # Skip completely empty rows
                if not any(v and str(v).strip() for v in row.values()):
                    self.stats['skipped_invalid'] += 1
                    continue
                
                # Skip rows without LinkedIn
                linkedin_url = row.get('LinkedIn', '').strip()
                if not linkedin_url:
                    self.stats['skipped_no_linkedin'] += 1
                    continue
                
                # Check if person exists (deduplication)
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
        
        # Get database counts after import
        self.cursor.execute("SELECT COUNT(*) as count FROM person")
        people_after = self.cursor.fetchone()['count']
        self.cursor.execute("SELECT COUNT(*) as count FROM company")
        companies_after = self.cursor.fetchone()['count']
        
        self.stats['people_before'] = people_before
        self.stats['people_after'] = people_after
        self.stats['companies_before'] = companies_before
        self.stats['companies_after'] = companies_after
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate and display import report"""
        print(f"\n{'='*80}")
        print(f"IMPORT COMPLETE - FINAL REPORT")
        print(f"{'='*80}")
        print(f"\nSource File: {self.csv_path}")
        
        print(f"\n📊 PROCESSING STATISTICS:")
        print(f"   Total Rows Processed: {self.stats['total_rows']:,}")
        
        print(f"\n👥 PEOPLE:")
        print(f"   ✅ Profiles Created: {self.stats['profiles_created']:,}")
        print(f"   🔄 Profiles Enriched: {self.stats['profiles_enriched']:,}")
        print(f"   ⏭️  Skipped (No LinkedIn): {self.stats['skipped_no_linkedin']:,}")
        print(f"   ⏭️  Skipped (Duplicate): {self.stats['skipped_duplicate_linkedin']:,}")
        print(f"   ⏭️  Skipped (Invalid): {self.stats['skipped_invalid']:,}")
        
        if self.stats['created_people_sample']:
            print(f"\n   Sample of new profiles:")
            for name in self.stats['created_people_sample']:
                print(f"      • {name}")
        
        print(f"\n🏢 COMPANIES:")
        print(f"   ✅ Companies Created: {self.stats['companies_created']:,}")
        print(f"   🔄 Companies Matched: {self.stats['companies_matched']:,}")
        
        if self.stats['companies_created_list'][:10]:
            print(f"\n   Sample of new companies:")
            for company in self.stats['companies_created_list'][:10]:
                print(f"      • {company}")
            if len(self.stats['companies_created_list']) > 10:
                print(f"      ... and {len(self.stats['companies_created_list']) - 10} more")
        
        print(f"\n💼 EMPLOYMENT:")
        print(f"   ✅ Employment Records Added: {self.stats['employment_records_added']:,}")
        
        print(f"\n🎓 EDUCATION:")
        print(f"   ✅ Education Records Added: {self.stats['education_records_added']:,}")
        
        print(f"\n📧 CONTACT INFO:")
        print(f"   ✅ Emails Added: {self.stats['emails_added']:,}")
        
        print(f"\n🔗 SOCIAL PROFILES:")
        print(f"   ✅ GitHub Profiles Added: {self.stats['github_profiles_added']:,}")
        print(f"   ✅ Twitter Profiles Added: {self.stats['twitter_profiles_added']:,}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for i, error in enumerate(self.stats['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more errors")
        
        # Database totals
        print(f"\n📈 DATABASE TOTALS:")
        print(f"   People: {self.stats['people_before']:,} → {self.stats['people_after']:,} "
              f"(+{self.stats['people_after'] - self.stats['people_before']:,})")
        print(f"   Companies: {self.stats['companies_before']:,} → {self.stats['companies_after']:,} "
              f"(+{self.stats['companies_after'] - self.stats['companies_before']:,})")
        
        print(f"\n{'='*80}\n")
        
        # Write report to file
        report_filename = f"reports/bm_gem_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = Path(__file__).parent.parent.parent / report_filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"BM Gem Protocol Import Report\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {self.csv_path}\n\n")
            f.write(f"Statistics:\n")
            for key, value in self.stats.items():
                if key not in ['errors', 'created_people_sample', 'companies_created_list']:
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
                migration_name='bm_gem_protocol_import',
                phase='import',
                status='completed',
                records_processed=self.stats['total_rows'],
                records_created=self.stats['profiles_created'],
                records_updated=self.stats['profiles_enriched'],
                records_skipped=(self.stats['skipped_no_linkedin'] + 
                               self.stats['skipped_duplicate_linkedin'] + 
                               self.stats['skipped_invalid']),
                metadata={
                    'source_file': self.csv_path,
                    'companies_created': self.stats['companies_created'],
                    'employment_added': self.stats['employment_records_added'],
                    'emails_added': self.stats['emails_added'],
                    'github_profiles': self.stats['github_profiles_added'],
                    'twitter_profiles': self.stats['twitter_profiles_added'],
                    'education_records': self.stats['education_records_added']
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
    # Accept CSV path as command line argument
    csv_path = CSV_PATH  # Default
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    # Check if CSV exists
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return 1
    
    # Count rows
    with open(csv_path, 'r', encoding='utf-8') as f:
        row_count = sum(1 for line in f) - 1  # -1 for header
    
    print(f"\n{'='*80}")
    print(f"BM GEM PROTOCOL IMPORT - PRE-FLIGHT CHECK")
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
    
    print(f"\n⚠️  IMPORT FEATURES:")
    print(f"   - Match existing people by LinkedIn URL")
    print(f"   - Parse multiple emails from 'All Emails' array")
    print(f"   - Extract GitHub usernames from URLs")
    print(f"   - Extract Twitter/X usernames from URLs")
    print(f"   - Store education (schools)")
    print(f"   - Create employment records")
    print(f"   - Data quality validation (no suffix-only companies)")
    print(f"   - Deduplication via caching and constraints")
    
    response = input(f"\nProceed with import? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        return 0
    
    try:
        importer = BMGemImporter(csv_path)
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


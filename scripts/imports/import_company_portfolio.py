#!/usr/bin/env python3
"""
Import company data from VC portfolio CSV
Only adds new data and fills gaps - never overwrites existing data
"""

import csv
import re
from pathlib import Path
from datetime import datetime
from config import get_db_connection, Config

CSV_PATH = "/Users/charlie.kerr/Downloads/Portfolios-vc_portfolio_companies-Default-view-export-1761086233689.csv"

class CompanyImporter:
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'total_rows': 0,
            'duplicates_skipped': 0,
            'companies_found': 0,
            'companies_enriched': 0,
            'companies_created': 0,
            'companies_already_complete': 0,
            'websites_added': 0,
            'linkedin_added': 0,
            'github_added': 0,
            'employee_count_added': 0,
            'skipped_invalid': 0,
            'errors': []
        }
        
        # Cache for deduplication
        self.processed_companies = set()
        self.company_cache = {}  # name_lower -> company_id
        
        print("📦 Loading existing companies...", flush=True)
        self._load_company_cache()
        print(f"✅ Ready to process CSV!\n", flush=True)
    
    def _load_company_cache(self):
        """Load existing companies for matching"""
        import time
        start = time.time()
        self.cursor.execute("""
            SELECT 
                company_id::text, 
                LOWER(company_name) as name_lower, 
                company_name,
                LOWER(REGEXP_REPLACE(company_name, '[^a-zA-Z0-9]', '', 'g')) as name_normalized
            FROM company
            WHERE company_name IS NOT NULL
        """)
        
        self.company_cache_normalized = {}  # normalized -> company_id
        
        for row in self.cursor.fetchall():
            company_id = row['company_id']
            name_lower = row['name_lower']
            name_normalized = row['name_normalized']
            
            # Store both exact lowercase and normalized versions
            self.company_cache[name_lower] = company_id
            if name_normalized:
                self.company_cache_normalized[name_normalized] = company_id
        
        elapsed = time.time() - start
        print(f"   ✓ Loaded {len(self.company_cache):,} existing companies in {elapsed:.1f}s", flush=True)
    
    def extract_github_org(self, github_value):
        """Extract clean GitHub org name from various formats"""
        if not github_value or not isinstance(github_value, str):
            return None
        
        github_value = github_value.strip()
        
        # Skip invalid values
        if (not github_value or 
            github_value.lower() == 'no organization found' or
            github_value.startswith('No official') or
            github_value.startswith('The company') or
            len(github_value) > 200):  # Skip long AI-generated text
            return None
        
        # Extract from URL
        if 'github.com/' in github_value:
            # Match github.com/orgname pattern
            match = re.search(r'github\.com/([a-zA-Z0-9_-]+)', github_value)
            if match:
                org_name = match.group(1)
                # Filter out personal accounts that look like orgs
                if org_name.lower() not in ['settings', 'notifications', 'explore']:
                    return org_name
        
        return None
    
    def normalize_website(self, website):
        """Normalize website URL"""
        if not website:
            return None
        
        website = website.strip()
        
        # Add https:// if missing
        if not website.startswith('http://') and not website.startswith('https://'):
            website = 'https://' + website
        
        # Remove trailing slash
        website = website.rstrip('/')
        
        return website if len(website) > 10 else None
    
    def normalize_linkedin_url(self, linkedin_url):
        """Normalize LinkedIn company URL"""
        if not linkedin_url:
            return None
        
        linkedin_url = linkedin_url.strip()
        
        # Ensure it's a company URL
        if 'linkedin.com/company/' in linkedin_url:
            # Standardize format
            linkedin_url = linkedin_url.replace('http://', 'https://')
            linkedin_url = linkedin_url.rstrip('/')
            return linkedin_url
        
        return None
    
    def parse_employee_count(self, employee_count_str):
        """Parse employee count from string"""
        if not employee_count_str:
            return None
        
        try:
            # Handle direct numbers
            count = int(employee_count_str)
            return count if count > 0 else None
        except:
            return None
    
    def get_size_bucket(self, employee_count):
        """Convert employee count to size bucket"""
        if not employee_count:
            return None
        
        if employee_count <= 10:
            return "2-10 employees"
        elif employee_count <= 50:
            return "11-50 employees"
        elif employee_count <= 200:
            return "51-200 employees"
        elif employee_count <= 500:
            return "201-500 employees"
        elif employee_count <= 1000:
            return "501-1,000 employees"
        elif employee_count <= 5000:
            return "1,001-5,000 employees"
        elif employee_count <= 10000:
            return "5,001-10,000 employees"
        else:
            return "10,000+ employees"
    
    def add_github_repository(self, company_id, github_org):
        """Add GitHub organization to github_repository table"""
        try:
            # Check if this org already exists for this company by owner_username
            self.cursor.execute("""
                SELECT repo_id
                FROM github_repository
                WHERE company_id = %s::uuid
                AND LOWER(owner_username) = LOWER(%s)
                LIMIT 1
            """, (company_id, github_org))
            
            if not self.cursor.fetchone():
                # Create a placeholder repository entry for the org
                # Use ON CONFLICT to handle duplicate full_name gracefully
                self.cursor.execute("""
                    INSERT INTO github_repository (
                        repo_id,
                        company_id,
                        repo_name,
                        full_name,
                        owner_username
                    )
                    VALUES (
                        gen_random_uuid(),
                        %s::uuid,
                        %s,
                        %s,
                        %s
                    )
                    ON CONFLICT (full_name) DO UPDATE
                    SET company_id = EXCLUDED.company_id,
                        owner_username = EXCLUDED.owner_username
                    RETURNING repo_id
                """, (
                    company_id,
                    f"{github_org} (org)",
                    f"{github_org}/{github_org}",
                    github_org
                ))
                
                result = self.cursor.fetchone()
                if result:
                    self.stats['github_added'] += 1
                    return True  # Successfully added or updated
            return False  # Already exists for this company
        except Exception as e:
            self.stats['errors'].append(f"Error adding GitHub org {github_org}: {e}")
            return False
    
    def normalize_company_name(self, company_name):
        """Normalize company name for matching (remove special chars)"""
        if not company_name:
            return None
        # Remove all non-alphanumeric characters and lowercase
        return re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
    
    def find_existing_company(self, company_name):
        """Find existing company by name with fuzzy matching"""
        if not company_name:
            return None
        
        # Try exact lowercase match first
        name_lower = company_name.lower().strip()
        if name_lower in self.company_cache:
            return self.company_cache[name_lower]
        
        # Try normalized match (remove spaces, punctuation, etc.)
        name_normalized = self.normalize_company_name(company_name)
        if name_normalized and name_normalized in self.company_cache_normalized:
            return self.company_cache_normalized[name_normalized]
        
        return None
    
    def enrich_company(self, company_id, row):
        """Enrich existing company with new data (never overwrite)"""
        updates = []
        params = []
        updated = False
        enrichment_details = []
        company_name = row.get('Company', '')
        
        self.stats['companies_found'] += 1
        
        # Get current company data
        self.cursor.execute("""
            SELECT 
                company_name,
                website_url,
                linkedin_url,
                size_bucket
            FROM company
            WHERE company_id = %s::uuid
        """, (company_id,))
        
        current = self.cursor.fetchone()
        if not current:
            return
        
        # Only update NULL or empty fields
        website = self.normalize_website(row.get('Website'))
        if website and not current['website_url']:
            updates.append("website_url = %s")
            params.append(website)
            self.stats['websites_added'] += 1
            enrichment_details.append(f"website")
            updated = True
        
        linkedin = self.normalize_linkedin_url(row.get('Linkedin'))
        if linkedin and not current['linkedin_url']:
            updates.append("linkedin_url = %s")
            params.append(linkedin)
            self.stats['linkedin_added'] += 1
            enrichment_details.append(f"linkedin")
            updated = True
        
        # Add size_bucket from Employee Count
        employee_count = self.parse_employee_count(row.get('Employee Count'))
        size_from_csv = row.get('Size', '').strip()
        if (employee_count or size_from_csv) and not current['size_bucket']:
            size_bucket = size_from_csv if size_from_csv else self.get_size_bucket(employee_count)
            if size_bucket:
                updates.append("size_bucket = %s")
                params.append(size_bucket)
                self.stats['employee_count_added'] += 1
                enrichment_details.append(f"size")
                updated = True
        
        # Handle GitHub org in github_repository table
        github_org = self.extract_github_org(row.get('Github'))
        if github_org:
            if self.add_github_repository(company_id, github_org):
                enrichment_details.append(f"github:{github_org}")
        
        if updates or enrichment_details:
            if updates:
                sql = f"""
                    UPDATE company
                    SET {', '.join(updates)}
                    WHERE company_id = %s::uuid
                """
                params.append(company_id)
                
                try:
                    self.cursor.execute(sql, params)
                    self.stats['companies_enriched'] += 1
                except Exception as e:
                    self.stats['errors'].append(f"Error enriching {company_name}: {e}")
                    return
            
            # Log enrichment details
            if enrichment_details:
                print(f"   ✓ Enriched '{current['company_name']}': {', '.join(enrichment_details)}", flush=True)
        else:
            self.stats['companies_already_complete'] += 1
    
    def create_company(self, row):
        """Create new company record"""
        company_name = row.get('Company', '').strip()
        if not company_name:
            return
        
        website = self.normalize_website(row.get('Website'))
        linkedin = self.normalize_linkedin_url(row.get('Linkedin'))
        github_org = self.extract_github_org(row.get('Github'))
        employee_count = self.parse_employee_count(row.get('Employee Count'))
        size_from_csv = row.get('Size', '').strip()
        size_bucket = size_from_csv if size_from_csv else self.get_size_bucket(employee_count)
        
        # company_domain is required - use website or placeholder
        company_domain = ''
        if website:
            # Extract domain from website
            domain_match = re.search(r'https?://([^/]+)', website)
            if domain_match:
                company_domain = domain_match.group(1)
        
        if not company_domain:
            # Create placeholder domain from company name
            company_domain = company_name.lower().replace(' ', '').replace('&', 'and')[:50] + '.placeholder'
        
        try:
            self.cursor.execute("""
                INSERT INTO company (
                    company_id,
                    company_domain,
                    company_name,
                    website_url,
                    linkedin_url,
                    size_bucket
                )
                VALUES (
                    gen_random_uuid(),
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (company_domain) DO UPDATE
                SET company_name = EXCLUDED.company_name
                RETURNING company_id::text
            """, (
                company_domain,
                company_name,
                website,
                linkedin,
                size_bucket
            ))
            
            result = self.cursor.fetchone()
            if result:
                company_id = result['company_id']
                self.company_cache[company_name.lower()] = company_id
                self.stats['companies_created'] += 1
                
                new_fields = []
                if website:
                    self.stats['websites_added'] += 1
                    new_fields.append('website')
                if linkedin:
                    self.stats['linkedin_added'] += 1
                    new_fields.append('linkedin')
                if size_bucket:
                    self.stats['employee_count_added'] += 1
                    new_fields.append('size')
                
                # Add GitHub org to github_repository table
                if github_org:
                    if self.add_github_repository(company_id, github_org):
                        new_fields.append(f'github:{github_org}')
                
                print(f"   ✨ Created '{company_name}': {', '.join(new_fields) if new_fields else 'basic info'}", flush=True)
                    
        except Exception as e:
            self.stats['errors'].append(f"Error creating {company_name}: {e}")
    
    def process_csv(self):
        """Main processing loop"""
        print(f"\n{'='*80}")
        print("COMPANY DATA IMPORT")
        print(f"{'='*80}")
        print(f"\nSource: {CSV_PATH}")
        print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}\n")
        
        import time
        start_time = time.time()
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                self.stats['total_rows'] += 1
                
                company_name = row.get('Company', '').strip()
                
                # Log first row
                if self.stats['total_rows'] == 1:
                    print(f"🔍 Processing first company: {company_name}...", flush=True)
                
                # Skip empty rows
                if not company_name:
                    self.stats['skipped_invalid'] += 1
                    continue
                
                # Skip duplicates within this CSV
                if company_name.lower() in self.processed_companies:
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                self.processed_companies.add(company_name.lower())
                
                # Find or create company
                company_id = self.find_existing_company(company_name)
                
                if company_id:
                    # Enrich existing company
                    self.enrich_company(company_id, row)
                else:
                    # Create new company
                    self.create_company(row)
                
                # Progress update every 50 rows
                if self.stats['total_rows'] % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = self.stats['total_rows'] / elapsed if elapsed > 0 else 0
                    print(f"   [{self.stats['total_rows']:,} rows | {elapsed:.1f}s | {rate:.1f} rows/s] "
                          f"Enriched: {self.stats['companies_enriched']}, Created: {self.stats['companies_created']}, "
                          f"GitHub: {self.stats['github_added']}", flush=True)
        
        print(f"\n✅ Processing complete!")
    
    def generate_report(self):
        """Generate import report"""
        print(f"\n{'='*80}")
        print("IMPORT REPORT")
        print(f"{'='*80}")
        
        print(f"\n📊 PROCESSING STATISTICS:")
        print(f"   Total Rows: {self.stats['total_rows']:,}")
        print(f"   Duplicates Skipped: {self.stats['duplicates_skipped']:,}")
        print(f"   Invalid/Empty: {self.stats['skipped_invalid']:,}")
        print(f"   Unique Companies Processed: {len(self.processed_companies):,}")
        
        print(f"\n🏢 COMPANY CHANGES:")
        print(f"   Companies Found in Database: {self.stats['companies_found']:,}")
        print(f"   Companies Enriched with New Data: {self.stats['companies_enriched']:,}")
        print(f"   Companies Already Complete: {self.stats['companies_already_complete']:,}")
        print(f"   New Companies Created: {self.stats['companies_created']:,}")
        print(f"   Total Companies Affected: {self.stats['companies_enriched'] + self.stats['companies_created']:,}")
        
        print(f"\n📝 DATA ADDED:")
        print(f"   Websites: {self.stats['websites_added']:,}")
        print(f"   LinkedIn URLs: {self.stats['linkedin_added']:,}")
        print(f"   GitHub Orgs: {self.stats['github_added']:,}")
        print(f"   Employee Counts: {self.stats['employee_count_added']:,}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:  # Show first 10
                print(f"   - {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more")
        
        # Save report
        report_file = Path(__file__).parent / f"company_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(f"Company Import Report\n")
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
        
        print(f"\n📄 Detailed report saved to: {report_file}")
    
    def close(self):
        """Clean up"""
        if self.conn:
            self.conn.close()

def main():
    # Validate CSV exists
    if not Path(CSV_PATH).exists():
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return
    
    # Count rows
    with open(CSV_PATH, 'r') as f:
        row_count = sum(1 for line in f) - 1  # Subtract header
    
    print(f"\n📄 CSV file found: {row_count:,} rows")
    print(f"⚠️  Importing/enriching company data into your database")
    print(f"Database: {Config.PG_DATABASE}@{Config.PG_HOST}")
    print(f"\n📋 Import Strategy:")
    print(f"   - Enrich EXISTING companies with missing data (never overwrites)")
    print(f"   - Create NEW companies that don't exist")
    print(f"   - Handle duplicates and invalid GitHub URLs")
    print(f"   - Skip rows with empty company names")
    print(f"\n🚀 Starting import...")
    
    importer = CompanyImporter()
    
    try:
        importer.process_csv()
        importer.generate_report()
    except Exception as e:
        print(f"\n❌ Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        importer.close()

if __name__ == "__main__":
    main()


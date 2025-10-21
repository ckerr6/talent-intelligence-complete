#!/usr/bin/env python3
# ABOUTME: Phase 2 - Build company database from company CSV files
# ABOUTME: Processes company data, funding rounds, investors, and links to candidates

"""
Talent Intelligence Database Builder - Phase 2: Companies

This script:
1. Processes company CSV files from multiple sources
2. Deduplicates companies by name, website, LinkedIn
3. Creates company profiles with funding/investor info
4. Links candidates to companies via foreign keys
5. Normalizes company names for consistent matching

Run this AFTER Phase 1 (candidates database must exist)
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib
import json
import sys
import re
from typing import Dict, List, Optional, Tuple

# Configuration
BATCH_SIZE = 1000  # Process 1k companies at a time

class CompanyDatabaseBuilder:
    def __init__(self, db_path: str, source_dir: str):
        self.db_path = Path(db_path)
        self.source_dir = Path(source_dir)
        self.conn = None
        
        # Deduplication indexes
        self.name_index = {}  # normalized_name -> company_id
        self.website_index = {}  # domain -> company_id
        self.linkedin_index = {}  # linkedin_url -> company_id
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'rows_read': 0,
            'companies_created': 0,
            'duplicates_merged': 0,
            'funding_rounds_added': 0,
            'candidates_linked': 0
        }
        
        # Logging
        self.log_file = self.db_path.parent / "company_import_log.txt"
        self.log(f"=== Company Database Build Started: {datetime.now()} ===")
    
    def log(self, message: str):
        """Log to both console and file"""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def normalize_company_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize company name for matching"""
        if not name or not str(name).strip():
            return None
        
        name = str(name).lower().strip()
        
        # Remove common suffixes
        suffixes = [
            r'\s+inc\.?$', r'\s+incorporated$', r'\s+corp\.?$', 
            r'\s+corporation$', r'\s+llc\.?$', r'\s+ltd\.?$',
            r'\s+limited$', r'\s+co\.?$', r'\s+company$',
            r'\s+labs?$', r'\s+technologies$', r'\s+tech$'
        ]
        
        for suffix in suffixes:
            name = re.sub(suffix, '', name)
        
        # Remove special characters except spaces
        name = re.sub(r'[^\w\s]', '', name)
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        return name if name else None
    
    def extract_domain(self, url: Optional[str]) -> Optional[str]:
        """Extract domain from URL"""
        if not url or not str(url).strip():
            return None
        
        url = str(url).lower().strip()
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        
        # Extract domain (first part before /)
        domain = url.split('/')[0]
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        return domain if '.' in domain else None
    
    def normalize_linkedin_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize LinkedIn company URL"""
        if not url or not str(url).strip():
            return None
        
        url = str(url).lower().strip()
        
        # Extract company identifier
        pattern = r'linkedin\.com/company/([^/?]+)'
        match = re.search(pattern, url)
        
        if match:
            return f"linkedin.com/company/{match.group(1)}"
        
        return url if 'linkedin.com' in url else None
    
    def generate_company_id(self, record: Dict) -> str:
        """Generate stable company ID"""
        key = record.get('website') or record.get('linkedin_url') or \
              record.get('normalized_name') or str(record.get('name', '')).lower()
        
        return 'comp_' + hashlib.md5(key.encode()).hexdigest()[:12]
    
    def create_company_schema(self):
        """Create company-related tables"""
        self.log("\n📊 Creating company schema...")
        
        cursor = self.conn.cursor()
        
        # Companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                company_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                normalized_name TEXT,
                website TEXT,
                linkedin_url TEXT,
                github_org TEXT,
                twitter_handle TEXT,
                industry TEXT,
                description TEXT,
                employee_count INTEGER,
                founded_year INTEGER,
                headquarters_location TEXT,
                data_quality_score REAL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Company funding rounds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_funding_rounds (
                funding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                round_type TEXT,
                amount_usd REAL,
                currency TEXT,
                funding_date TEXT,
                investors TEXT,
                lead_investors TEXT,
                valuation_usd REAL,
                source TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """)
        
        # Company social profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_social_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                profile_url TEXT,
                username TEXT,
                follower_count INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(company_id),
                UNIQUE(company_id, platform)
            )
        """)
        
        # Add company_id to employment table
        cursor.execute("""
            ALTER TABLE employment ADD COLUMN company_id TEXT 
            REFERENCES companies(company_id)
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(normalized_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_website ON companies(website)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_linkedin ON companies(linkedin_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funding_company ON company_funding_rounds(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_social ON company_social_profiles(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employment_company_id ON employment(company_id)")
        
        self.conn.commit()
        self.log("✅ Company schema created")
    
    def find_existing_company(self, record: Dict) -> Optional[str]:
        """Find if company already exists"""
        # Check 1: LinkedIn URL (high confidence)
        linkedin = self.normalize_linkedin_url(record.get('linkedin_url'))
        if linkedin and linkedin in self.linkedin_index:
            return self.linkedin_index[linkedin]
        
        # Check 2: Website domain (high confidence)
        website = record.get('website')
        if website:
            domain = self.extract_domain(website)
            if domain and domain in self.website_index:
                return self.website_index[domain]
        
        # Check 3: Normalized name (medium confidence)
        name = self.normalize_company_name(record.get('name'))
        if name and name in self.name_index:
            return self.name_index[name]
        
        return None
    
    def merge_company_records(self, existing_id: str, new_record: Dict) -> Dict:
        """Merge new company data into existing record"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE company_id = ?", (existing_id,))
        existing = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
        
        merged = existing.copy()
        
        # Merge fields, preferring non-null values
        for field in new_record:
            new_val = new_record.get(field)
            existing_val = existing.get(field)
            
            if not new_val or (isinstance(new_val, str) and not new_val.strip()):
                continue
            
            if not existing_val or (isinstance(existing_val, str) and not existing_val.strip()):
                merged[field] = new_val
            elif len(str(new_val)) > len(str(existing_val)):
                merged[field] = new_val
        
        merged['updated_at'] = datetime.now().isoformat()
        
        return merged
    
    def update_company_indexes(self, company_id: str, record: Dict):
        """Update in-memory indexes"""
        name = self.normalize_company_name(record.get('name'))
        if name:
            self.name_index[name] = company_id
        
        website = record.get('website')
        if website:
            domain = self.extract_domain(website)
            if domain:
                self.website_index[domain] = company_id
        
        linkedin = self.normalize_linkedin_url(record.get('linkedin_url'))
        if linkedin:
            self.linkedin_index[linkedin] = company_id
    
    def insert_company(self, record: Dict):
        """Insert or update company"""
        company_id = self.generate_company_id(record)
        
        existing_id = self.find_existing_company(record)
        
        if existing_id:
            # Merge with existing
            self.stats['duplicates_merged'] += 1
            merged = self.merge_company_records(existing_id, record)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE companies 
                SET name=?, normalized_name=?, website=?, linkedin_url=?,
                    github_org=?, twitter_handle=?, industry=?, description=?,
                    employee_count=?, founded_year=?, headquarters_location=?,
                    updated_at=?
                WHERE company_id=?
            """, (
                merged.get('name'), merged.get('normalized_name'),
                merged.get('website'), merged.get('linkedin_url'),
                merged.get('github_org'), merged.get('twitter_handle'),
                merged.get('industry'), merged.get('description'),
                merged.get('employee_count'), merged.get('founded_year'),
                merged.get('headquarters_location'), merged.get('updated_at'),
                existing_id
            ))
            
            company_id = existing_id
        else:
            # Insert new company
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO companies (
                    company_id, name, normalized_name, website, linkedin_url,
                    github_org, twitter_handle, industry, description,
                    employee_count, founded_year, headquarters_location,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                record.get('name'),
                self.normalize_company_name(record.get('name')),
                record.get('website'),
                self.normalize_linkedin_url(record.get('linkedin_url')),
                record.get('github_org'),
                record.get('twitter_handle'),
                record.get('industry'),
                record.get('description'),
                record.get('employee_count'),
                record.get('founded_year'),
                record.get('headquarters_location'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            self.stats['companies_created'] += 1
        
        # Update indexes
        self.update_company_indexes(company_id, record)
        
        # Insert social profiles
        self.insert_company_social_profiles(company_id, record)
        
        # Insert funding data if present
        if record.get('funding_round') or record.get('investors'):
            self.insert_funding_round(company_id, record)
        
        return company_id
    
    def insert_company_social_profiles(self, company_id: str, record: Dict):
        """Insert company social media profiles"""
        cursor = self.conn.cursor()
        
        # LinkedIn
        linkedin = self.normalize_linkedin_url(record.get('linkedin_url'))
        if linkedin:
            cursor.execute("""
                INSERT OR REPLACE INTO company_social_profiles 
                (company_id, platform, profile_url)
                VALUES (?, 'linkedin', ?)
            """, (company_id, linkedin))
        
        # GitHub
        github = record.get('github_org') or record.get('github_url')
        if github:
            cursor.execute("""
                INSERT OR REPLACE INTO company_social_profiles 
                (company_id, platform, profile_url)
                VALUES (?, 'github', ?)
            """, (company_id, str(github).strip()))
        
        # Twitter
        twitter = record.get('twitter_handle') or record.get('twitter_url')
        if twitter:
            cursor.execute("""
                INSERT OR REPLACE INTO company_social_profiles 
                (company_id, platform, profile_url)
                VALUES (?, 'twitter', ?)
            """, (company_id, str(twitter).strip()))
    
    def insert_funding_round(self, company_id: str, record: Dict):
        """Insert funding round data"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO company_funding_rounds (
                company_id, round_type, amount_usd, funding_date,
                investors, lead_investors, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            record.get('funding_round') or record.get('round_type'),
            record.get('funding_amount') or record.get('amount'),
            record.get('funding_date') or record.get('date'),
            record.get('investors'),
            record.get('lead_investors'),
            record.get('source', 'csv_import')
        ))
        
        self.stats['funding_rounds_added'] += 1
    
    def process_csv_file(self, csv_path: Path):
        """Process a single company CSV file"""
        self.log(f"  Processing: {csv_path.name}")
        
        try:
            chunk_iter = pd.read_csv(
                csv_path,
                chunksize=BATCH_SIZE,
                low_memory=False,
                encoding='utf-8',
                on_bad_lines='skip'
            )
            
            for chunk_num, chunk in enumerate(chunk_iter):
                chunk.columns = chunk.columns.str.lower().str.strip()
                chunk = chunk.replace({np.nan: None})
                
                for _, row in chunk.iterrows():
                    self.stats['rows_read'] += 1
                    
                    record = row.to_dict()
                    
                    # Skip if no company name
                    if not record.get('name') and not record.get('company') and \
                       not record.get('company_name'):
                        continue
                    
                    # Normalize field names
                    if 'company' in record and not record.get('name'):
                        record['name'] = record['company']
                    elif 'company_name' in record and not record.get('name'):
                        record['name'] = record['company_name']
                    
                    # Insert/update company
                    self.insert_company(record)
                
                # Commit every batch
                self.conn.commit()
                
                if (chunk_num + 1) % 5 == 0:
                    self.log(f"    Processed {(chunk_num + 1) * BATCH_SIZE} rows...")
            
            self.stats['files_processed'] += 1
            
        except Exception as e:
            self.log(f"  ⚠️  Error processing {csv_path.name}: {str(e)}")
    
    def link_candidates_to_companies(self):
        """Link existing candidate employment records to company_id"""
        self.log("\n🔗 Linking candidates to companies...")
        
        cursor = self.conn.cursor()
        
        # Get all employment records without company_id
        cursor.execute("""
            SELECT employment_id, company_name 
            FROM employment 
            WHERE company_id IS NULL AND company_name IS NOT NULL
        """)
        
        employment_records = cursor.fetchall()
        linked_count = 0
        
        for emp_id, company_name in employment_records:
            # Try to find matching company
            normalized = self.normalize_company_name(company_name)
            
            if normalized and normalized in self.name_index:
                company_id = self.name_index[normalized]
                
                cursor.execute("""
                    UPDATE employment 
                    SET company_id = ? 
                    WHERE employment_id = ?
                """, (company_id, emp_id))
                
                linked_count += 1
        
        self.conn.commit()
        self.stats['candidates_linked'] = linked_count
        
        self.log(f"  ✅ Linked {linked_count} candidates to companies")
    
    def build(self):
        """Main execution"""
        if not self.db_path.exists():
            self.log("❌ Database not found! Run Phase 1 first.")
            sys.exit(1)
        
        self.log("\n🚀 Starting company database build...")
        self.log(f"Database: {self.db_path}")
        
        # Connect to database
        self.conn = sqlite3.connect(self.db_path)
        
        # Create schema
        self.create_company_schema()
        
        # Process company CSV files
        company_csvs = self.find_company_csvs()
        
        self.log(f"\n📥 Processing {len(company_csvs)} company CSV files...")
        for csv_path in company_csvs:
            self.process_csv_file(csv_path)
        
        # Link candidates to companies
        self.link_candidates_to_companies()
        
        # Generate reports
        self.generate_company_report()
        
        # Close database
        self.conn.close()
        
        self.log("\n✅ Company database build complete!")
    
    def find_company_csvs(self) -> List[Path]:
        """Find all company-related CSV files"""
        self.log("\n🔍 Scanning for company CSV files...")
        
        csv_files = []
        
        # Specific company CSV paths you provided
        company_paths = [
            "BM_Resources/google_sheets/sourcing_lists/2025-07-16-yc_companies (2).csv",
            "BM_Resources/google_sheets/sourcing_lists/Protocols w_ LinkedIn - Sheet1.csv",
            "BM_Resources/google_sheets/sourcing_lists/protocols_github - Protocol-Sourcing-List-Default-View-export-1733242082375.csv",
            "BM_Resources/google_sheets/sourcing_lists/sourcing_company_list - Sourcing — Company List 89026feb4624410b98b2d4d64027f189_all (1).csv",
            "BM_Resources/google_sheets/personal_projects/Copy of Electric_Capital_Pull - Electric_Capital_Report_Ecosystems.csv",
            "BM_Resources/Notion/Private & Shared 2/Sourcing Resources 1a235638d1a8802e94c2c39bbd27cc85/Sourcing — Company List 89026feb4624410b98b2d4d64027f189_all.csv",
            "BM_Resources/Notion/Private & Shared 2/Sourcing Resources 1a235638d1a8802e94c2c39bbd27cc85/Sourcing — Company List 89026feb4624410b98b2d4d64027f189.csv",
            "BM_Resources/Notion/Private & Shared 2/Sourcing Resources 1a235638d1a8802e94c2c39bbd27cc85/Sourcing — Github Repos 79e9fa8eb5ce4749b0e69240af764441_all.csv",
            "BM_Resources/Notion/Private & Shared 2/Sourcing Resources 1a235638d1a8802e94c2c39bbd27cc85/Sourcing — Github Repos 79e9fa8eb5ce4749b0e69240af764441.csv",
        ]
        
        for rel_path in company_paths:
            full_path = self.source_dir / rel_path
            if full_path.exists():
                csv_files.append(full_path)
        
        # Also look for other company-related CSVs
        for pattern in ['*company*.csv', '*companies*.csv', '*yc*.csv', '*protocol*.csv']:
            csv_files.extend(self.source_dir.rglob(pattern))
        
        # Deduplicate
        csv_files = list(set(csv_files))
        
        self.log(f"  Found {len(csv_files)} company CSV files")
        return csv_files
    
    def generate_company_report(self):
        """Generate company database report"""
        report_path = self.db_path.parent / "company_quality_report.txt"
        
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies WHERE website IS NOT NULL")
        with_website = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies WHERE linkedin_url IS NOT NULL")
        with_linkedin = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies WHERE github_org IS NOT NULL")
        with_github = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM company_funding_rounds")
        total_funding = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT company_id) FROM employment WHERE company_id IS NOT NULL")
        companies_with_candidates = cursor.fetchone()[0]
        
        report = f"""
=================================================================
COMPANY DATABASE REPORT
Generated: {datetime.now()}
=================================================================

PROCESSING STATISTICS
---------------------
Files Processed: {self.stats['files_processed']}
Total Rows Read: {self.stats['rows_read']:,}
Companies Created: {self.stats['companies_created']:,}
Duplicates Merged: {self.stats['duplicates_merged']:,}
Funding Rounds Added: {self.stats['funding_rounds_added']:,}
Candidates Linked: {self.stats['candidates_linked']:,}

DATABASE STATISTICS
-------------------
Total Unique Companies: {total_companies:,}
With Website: {with_website:,} ({with_website/total_companies*100:.1f}%)
With LinkedIn: {with_linkedin:,} ({with_linkedin/total_companies*100:.1f}%)
With GitHub: {with_github:,} ({with_github/total_companies*100:.1f}%)
With Funding Data: {total_funding:,} rounds
Companies with Linked Candidates: {companies_with_candidates:,}

=================================================================
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        self.log(report)
        self.log(f"\n📊 Company report saved to: {report_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python build_company_database.py <database_path> <source_directory>")
        print("Example: python build_company_database.py ./talent_intelligence.db '/Users/charlie.kerr/Documents/CK Docs'")
        sys.exit(1)
    
    db_path = sys.argv[1]
    source_dir = sys.argv[2]
    
    if not Path(db_path).exists():
        print("❌ Database not found! Run Phase 1 first (./RUN_ME.sh)")
        sys.exit(1)
    
    builder = CompanyDatabaseBuilder(db_path, source_dir)
    builder.build()
    
    print("\n" + "="*65)
    print("✅ SUCCESS! Company database ready.")
    print("="*65)
    print(f"\nDatabase file: {db_path}")
    print(f"Company report: {Path(db_path).parent}/company_quality_report.txt")
    print("\nTo query companies:")
    print(f"  sqlite3 {db_path}")
    print("  SELECT COUNT(*) FROM companies;")
    print("  SELECT * FROM companies LIMIT 5;")
    print()


if __name__ == "__main__":
    main()

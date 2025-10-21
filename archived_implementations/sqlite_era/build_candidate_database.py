#!/usr/bin/env python3
# ABOUTME: Main script to build clean candidate database from high-quality CSV data
# ABOUTME: Processes data in memory-efficient batches, handles deduplication, creates SQLite DB

"""
Talent Intelligence Database Builder - Phase 1: Candidates

This script:
1. Identifies high-quality candidate records (those with names + contact info)
2. Deduplicates intelligently based on email, LinkedIn, and name+company
3. Creates a clean SQLite database with proper relationships
4. Generates quality reports

Memory-efficient: Processes in 5000-record batches for M1 Pro with 16GB RAM
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib
import json
import sys
from typing import Dict, List, Tuple, Optional
import re

# Configuration
BATCH_SIZE = 5000  # Process 5k records at a time
MIN_QUALITY_THRESHOLD = 0.3  # Must have at least 30% of core fields filled

class DatabaseBuilder:
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.db_path = self.output_dir / "talent_intelligence.db"
        self.conn = None
        
        # Deduplication indexes for fast lookups
        self.email_index = {}  # email -> person_id
        self.linkedin_index = {}  # linkedin_url -> person_id
        self.name_company_index = {}  # (name, company) -> person_id
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'rows_read': 0,
            'high_quality_found': 0,
            'duplicates_merged': 0,
            'final_candidates': 0,
            'skipped_low_quality': 0
        }
        
        # Setup logging
        self.log_file = self.output_dir / "import_log.txt"
        self.log(f"=== Database Build Started: {datetime.now()} ===")
    
    def log(self, message: str):
        """Log message to both console and file"""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def create_database_schema(self):
        """Create SQLite database with optimized schema"""
        self.log("\n📊 Creating database schema...")
        
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Main people table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                person_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                primary_email TEXT,
                location TEXT,
                status TEXT DEFAULT 'active',
                data_quality_score REAL,
                created_at TEXT,
                updated_at TEXT,
                notes TEXT
            )
        """)
        
        # Social profiles (one person can have multiple platforms)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                profile_url TEXT,
                username TEXT,
                FOREIGN KEY (person_id) REFERENCES people(person_id),
                UNIQUE(person_id, platform)
            )
        """)
        
        # Email addresses (one person can have multiple emails)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                email_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT NOT NULL,
                email TEXT NOT NULL,
                email_type TEXT,
                is_primary INTEGER DEFAULT 0,
                FOREIGN KEY (person_id) REFERENCES people(person_id),
                UNIQUE(person_id, email)
            )
        """)
        
        # Employment (current and historical)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employment (
                employment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT NOT NULL,
                company_name TEXT,
                title TEXT,
                start_date TEXT,
                end_date TEXT,
                is_current INTEGER DEFAULT 0,
                FOREIGN KEY (person_id) REFERENCES people(person_id)
            )
        """)
        
        # Source tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT NOT NULL,
                source_file TEXT,
                source_type TEXT,
                ingestion_date TEXT,
                FOREIGN KEY (person_id) REFERENCES people(person_id)
            )
        """)
        
        # Create indexes for fast lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_email ON people(primary_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_name ON people(first_name, last_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_linkedin ON social_profiles(profile_url) WHERE platform='linkedin'")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_github ON social_profiles(profile_url) WHERE platform='github'")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails ON emails(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employment_current ON employment(person_id, is_current)")
        
        self.conn.commit()
        self.log("✅ Database schema created")
    
    def generate_person_id(self, record: Dict) -> str:
        """Generate stable person ID from key fields"""
        # Use email or LinkedIn as primary identifier, fall back to name
        key = record.get('primary_email') or record.get('linkedin_url') or \
              f"{record.get('first_name', '')}_{record.get('last_name', '')}".lower()
        
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def calculate_quality_score(self, record: Dict) -> float:
        """Calculate data quality score (0-1)"""
        weights = {
            'first_name': 0.15,
            'last_name': 0.15,
            'primary_email': 0.25,
            'linkedin_url': 0.20,
            'current_company': 0.10,
            'current_title': 0.10,
            'github_url': 0.05
        }
        
        score = 0.0
        for field, weight in weights.items():
            if record.get(field) and str(record[field]).strip():
                score += weight
        
        return round(score, 2)
    
    def normalize_linkedin_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize LinkedIn URLs for matching"""
        if not url:
            return None
        
        url = str(url).lower().strip()
        
        # Extract the profile identifier
        patterns = [
            r'linkedin\.com/in/([^/?]+)',
            r'linkedin\.com/pub/([^/?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return f"linkedin.com/in/{match.group(1)}"
        
        return url if 'linkedin.com' in url else None
    
    def normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize email addresses"""
        if not email:
            return None
        
        email = str(email).lower().strip()
        
        # Basic email validation
        if '@' in email and '.' in email:
            return email
        
        return None
    
    def find_existing_person(self, record: Dict) -> Optional[str]:
        """
        Find if this person already exists in our indexes
        Returns person_id if found, None otherwise
        """
        # Check 1: Email match (highest confidence)
        email = self.normalize_email(record.get('primary_email'))
        if email and email in self.email_index:
            return self.email_index[email]
        
        # Check 2: LinkedIn URL match (high confidence)
        linkedin = self.normalize_linkedin_url(record.get('linkedin_url'))
        if linkedin and linkedin in self.linkedin_index:
            return self.linkedin_index[linkedin]
        
        # Check 3: Name + Company match (medium confidence)
        first = str(record.get('first_name', '')).strip().lower()
        last = str(record.get('last_name', '')).strip().lower()
        company = str(record.get('current_company', '')).strip().lower()
        
        if first and last and company:
            key = f"{first}|{last}|{company}"
            if key in self.name_company_index:
                return self.name_company_index[key]
        
        return None
    
    def merge_records(self, existing_id: str, new_record: Dict) -> Dict:
        """
        Merge new record into existing record
        Strategy: Keep most complete data, prefer non-null values
        """
        # Fetch existing record from database
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM people WHERE person_id = ?", (existing_id,))
        existing = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
        
        merged = existing.copy()
        
        # Merge each field, preferring non-null values
        for field in new_record:
            new_val = new_record.get(field)
            existing_val = existing.get(field)
            
            # Skip if new value is null/empty
            if not new_val or (isinstance(new_val, str) and not new_val.strip()):
                continue
            
            # Use new value if existing is null/empty
            if not existing_val or (isinstance(existing_val, str) and not existing_val.strip()):
                merged[field] = new_val
            # If both have values, keep the longer/more complete one
            elif len(str(new_val)) > len(str(existing_val)):
                merged[field] = new_val
        
        # Update quality score
        merged['data_quality_score'] = self.calculate_quality_score(merged)
        merged['updated_at'] = datetime.now().isoformat()
        
        return merged
    
    def update_person_indexes(self, person_id: str, record: Dict):
        """Update in-memory indexes for fast deduplication"""
        email = self.normalize_email(record.get('primary_email'))
        if email:
            self.email_index[email] = person_id
        
        linkedin = self.normalize_linkedin_url(record.get('linkedin_url'))
        if linkedin:
            self.linkedin_index[linkedin] = person_id
        
        first = str(record.get('first_name', '')).strip().lower()
        last = str(record.get('last_name', '')).strip().lower()
        company = str(record.get('current_company', '')).strip().lower()
        
        if first and last and company:
            key = f"{first}|{last}|{company}"
            self.name_company_index[key] = person_id
    
    def is_high_quality_record(self, record: Dict) -> bool:
        """
        Determine if record is high-quality candidate data
        Must have: Name AND (Email OR LinkedIn) AND some company/title info
        """
        has_name = (record.get('first_name') or record.get('last_name'))
        has_contact = (record.get('primary_email') or record.get('linkedin_url'))
        has_context = (record.get('current_company') or record.get('current_title'))
        
        return bool(has_name and has_contact and has_context)
    
    def insert_person(self, record: Dict):
        """Insert a new person into the database"""
        person_id = self.generate_person_id(record)
        
        # Check if exists
        existing_id = self.find_existing_person(record)
        
        if existing_id:
            # Merge with existing
            self.stats['duplicates_merged'] += 1
            merged = self.merge_records(existing_id, record)
            
            # Update existing record
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE people 
                SET first_name=?, last_name=?, full_name=?, primary_email=?,
                    location=?, data_quality_score=?, updated_at=?, notes=?
                WHERE person_id=?
            """, (
                merged.get('first_name'), merged.get('last_name'), merged.get('full_name'),
                merged.get('primary_email'), merged.get('location'),
                merged.get('data_quality_score'), merged.get('updated_at'),
                merged.get('notes'), existing_id
            ))
            
            person_id = existing_id
        else:
            # Insert new person
            quality_score = self.calculate_quality_score(record)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO people (
                    person_id, first_name, last_name, full_name, primary_email,
                    location, data_quality_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                record.get('first_name'),
                record.get('last_name'),
                record.get('full_name'),
                self.normalize_email(record.get('primary_email')),
                record.get('location'),
                quality_score,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            self.stats['final_candidates'] += 1
        
        # Update indexes
        self.update_person_indexes(person_id, record)
        
        # Insert social profiles
        self.insert_social_profiles(person_id, record)
        
        # Insert employment
        self.insert_employment(person_id, record)
        
        # Insert additional emails
        self.insert_emails(person_id, record)
        
        return person_id
    
    def insert_social_profiles(self, person_id: str, record: Dict):
        """Insert social media profiles"""
        cursor = self.conn.cursor()
        
        # LinkedIn
        linkedin = self.normalize_linkedin_url(record.get('linkedin_url'))
        if linkedin:
            cursor.execute("""
                INSERT OR REPLACE INTO social_profiles (person_id, platform, profile_url)
                VALUES (?, 'linkedin', ?)
            """, (person_id, linkedin))
        
        # GitHub
        github = record.get('github_url')
        if github and str(github).strip():
            cursor.execute("""
                INSERT OR REPLACE INTO social_profiles (person_id, platform, profile_url)
                VALUES (?, 'github', ?)
            """, (person_id, str(github).strip()))
        
        # Twitter/X
        twitter = record.get('twitter_url')
        if twitter and str(twitter).strip():
            cursor.execute("""
                INSERT OR REPLACE INTO social_profiles (person_id, platform, profile_url)
                VALUES (?, 'twitter', ?)
            """, (person_id, str(twitter).strip()))
    
    def insert_employment(self, person_id: str, record: Dict):
        """Insert employment information"""
        company = record.get('current_company')
        title = record.get('current_title')
        
        if company or title:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO employment (person_id, company_name, title, is_current)
                VALUES (?, ?, ?, 1)
            """, (person_id, company, title))
    
    def insert_emails(self, person_id: str, record: Dict):
        """Insert email addresses"""
        cursor = self.conn.cursor()
        
        primary_email = self.normalize_email(record.get('primary_email'))
        if primary_email:
            cursor.execute("""
                INSERT OR REPLACE INTO emails (person_id, email, is_primary)
                VALUES (?, ?, 1)
            """, (person_id, primary_email))
        
        # Handle additional emails if they exist
        for i in range(2, 6):  # Check for Email_2 through Email_5
            email_field = f'Email_{i}' if i > 1 else 'Email'
            email = self.normalize_email(record.get(email_field))
            if email and email != primary_email:
                cursor.execute("""
                    INSERT OR IGNORE INTO emails (person_id, email, is_primary)
                    VALUES (?, ?, 0)
                """, (person_id, email))
    
    def process_csv_file(self, csv_path: Path):
        """Process a single CSV file in batches"""
        self.log(f"  Processing: {csv_path.name}")
        
        try:
            # Read CSV in chunks
            chunk_iter = pd.read_csv(
                csv_path,
                chunksize=BATCH_SIZE,
                low_memory=False,
                encoding='utf-8',
                on_bad_lines='skip'
            )
            
            for chunk_num, chunk in enumerate(chunk_iter):
                # Standardize column names
                chunk.columns = chunk.columns.str.lower().str.strip()
                
                # Replace NaN with None
                chunk = chunk.replace({np.nan: None})
                
                for _, row in chunk.iterrows():
                    self.stats['rows_read'] += 1
                    
                    record = row.to_dict()
                    
                    # Check if high quality
                    if self.is_high_quality_record(record):
                        self.stats['high_quality_found'] += 1
                        self.insert_person(record)
                    else:
                        self.stats['skipped_low_quality'] += 1
                
                # Commit every batch
                self.conn.commit()
                
                if (chunk_num + 1) % 5 == 0:
                    self.log(f"    Processed {(chunk_num + 1) * BATCH_SIZE} rows...")
            
            self.stats['files_processed'] += 1
            
        except Exception as e:
            self.log(f"  ⚠️  Error processing {csv_path.name}: {str(e)}")
    
    def find_candidate_csvs(self) -> List[Path]:
        """Find all CSV files that likely contain candidate data"""
        self.log("\n🔍 Scanning for candidate CSV files...")
        
        csv_files = []
        
        # Primary source: merged_output directory
        merged_output = self.source_dir / "merged_output"
        if merged_output.exists():
            for csv in merged_output.glob("*.csv"):
                # Skip GitHub-only files
                if 'github' in csv.name.lower() and 'contributor' in csv.name.lower():
                    continue
                csv_files.append(csv)
        
        # Secondary sources: CSV_Final_Organized
        csv_organized = self.source_dir / "CSV_Final_Organized"
        if csv_organized.exists():
            for csv in csv_organized.rglob("*.csv"):
                # Look for files with people-related names
                name_lower = csv.name.lower()
                if any(keyword in name_lower for keyword in ['master', 'candidate', 'contact', 'people', 'sourcing']):
                    csv_files.append(csv)
        
        self.log(f"  Found {len(csv_files)} candidate CSV files")
        return csv_files
    
    def build_database(self):
        """Main execution flow"""
        self.log("\n🚀 Starting database build process...")
        self.log(f"Source directory: {self.source_dir}")
        self.log(f"Output directory: {self.output_dir}")
        
        # Create schema
        self.create_database_schema()
        
        # Find and process CSV files
        csv_files = self.find_candidate_csvs()
        
        self.log(f"\n📥 Processing {len(csv_files)} CSV files...")
        for csv_path in csv_files:
            self.process_csv_file(csv_path)
        
        # Final commit
        self.conn.commit()
        
        # Generate reports
        self.generate_quality_report()
        self.generate_deduplication_report()
        self.generate_sample_queries()
        
        # Close database
        self.conn.close()
        
        self.log("\n✅ Database build complete!")
        self.log(f"Database location: {self.db_path}")
    
    def generate_quality_report(self):
        """Generate data quality report"""
        report_path = self.output_dir / "data_quality_report.txt"
        
        cursor = self.conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM people")
        total_people = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM people WHERE primary_email IS NOT NULL")
        with_email = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM social_profiles WHERE platform='linkedin'")
        with_linkedin = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM social_profiles WHERE platform='github'")
        with_github = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM employment WHERE is_current=1")
        with_current_job = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(data_quality_score) FROM people")
        avg_quality = cursor.fetchone()[0] or 0
        
        report = f"""
=================================================================
DATA QUALITY REPORT
Generated: {datetime.now()}
=================================================================

PROCESSING STATISTICS
---------------------
Files Processed: {self.stats['files_processed']}
Total Rows Read: {self.stats['rows_read']:,}
High-Quality Records Found: {self.stats['high_quality_found']:,}
Low-Quality Records Skipped: {self.stats['skipped_low_quality']:,}
Duplicates Merged: {self.stats['duplicates_merged']:,}

DATABASE STATISTICS
-------------------
Total Unique People: {total_people:,}
With Email: {with_email:,} ({with_email/total_people*100:.1f}%)
With LinkedIn: {with_linkedin:,} ({with_linkedin/total_people*100:.1f}%)
With GitHub: {with_github:,} ({with_github/total_people*100:.1f}%)
With Current Employment: {with_current_job:,} ({with_current_job/total_people*100:.1f}%)

Average Data Quality Score: {avg_quality:.2f} / 1.00

=================================================================
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        self.log(report)
    
    def generate_deduplication_report(self):
        """Generate deduplication report"""
        report_path = self.output_dir / "deduplication_report.txt"
        
        report = f"""
=================================================================
DEDUPLICATION REPORT
Generated: {datetime.now()}
=================================================================

DEDUPLICATION STRATEGY
----------------------
1. Email Match: Exact email address match → Same person
2. LinkedIn Match: Normalized LinkedIn URL match → Same person
3. Name + Company Match: Same first+last name + same company → Same person

RESULTS
-------
Total Duplicates Found and Merged: {self.stats['duplicates_merged']:,}

INDEX SIZES
-----------
Email Index: {len(self.email_index):,} entries
LinkedIn Index: {len(self.linkedin_index):,} entries
Name+Company Index: {len(self.name_company_index):,} entries

MERGE STRATEGY
--------------
When duplicates are found:
- Keep most complete data from both records
- Prefer non-null values
- Use longer/more complete values when both exist
- Update quality score based on merged data

=================================================================
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        self.log(f"\n📊 Deduplication report saved to: {report_path}")
    
    def generate_sample_queries(self):
        """Generate sample SQL queries for the user"""
        queries_path = self.output_dir / "sample_queries.sql"
        
        queries = """
-- Sample Queries for Talent Intelligence Database
-- Generated: {datetime}

-- 1. Find all candidates from a specific company
SELECT 
    p.first_name, p.last_name, p.primary_email,
    e.title, e.company_name
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE LOWER(e.company_name) LIKE '%uniswap%'
AND e.is_current = 1;

-- 2. Find candidates with both LinkedIn and GitHub
SELECT 
    p.first_name, p.last_name, p.primary_email,
    sp1.profile_url as linkedin_url,
    sp2.profile_url as github_url
FROM people p
JOIN social_profiles sp1 ON p.person_id = sp1.person_id AND sp1.platform = 'linkedin'
JOIN social_profiles sp2 ON p.person_id = sp2.person_id AND sp2.platform = 'github';

-- 3. Find high-quality candidates (quality score > 0.7)
SELECT 
    first_name, last_name, primary_email,
    data_quality_score
FROM people
WHERE data_quality_score > 0.7
ORDER BY data_quality_score DESC;

-- 4. Get complete profile for a specific person
SELECT 
    p.*,
    GROUP_CONCAT(DISTINCT sp.platform || ': ' || sp.profile_url, '\n') as social_profiles,
    GROUP_CONCAT(DISTINCT em.email, ', ') as all_emails,
    e.company_name, e.title
FROM people p
LEFT JOIN social_profiles sp ON p.person_id = sp.person_id
LEFT JOIN emails em ON p.person_id = em.person_id
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
WHERE p.primary_email = 'example@email.com'
GROUP BY p.person_id;

-- 5. Count candidates by location
SELECT 
    location,
    COUNT(*) as candidate_count
FROM people
WHERE location IS NOT NULL
GROUP BY location
ORDER BY candidate_count DESC
LIMIT 20;

-- 6. Find candidates missing LinkedIn profiles
SELECT 
    first_name, last_name, primary_email
FROM people p
WHERE NOT EXISTS (
    SELECT 1 FROM social_profiles sp 
    WHERE sp.person_id = p.person_id 
    AND sp.platform = 'linkedin'
)
AND primary_email IS NOT NULL;

-- 7. Get all emails for people at a specific company
SELECT 
    p.first_name, p.last_name,
    GROUP_CONCAT(em.email, ', ') as all_emails
FROM people p
JOIN employment e ON p.person_id = e.person_id
JOIN emails em ON p.person_id = em.person_id
WHERE LOWER(e.company_name) LIKE '%coinbase%'
AND e.is_current = 1
GROUP BY p.person_id;

-- 8. Find potential duplicate candidates (same name, different person_id)
SELECT 
    first_name, last_name,
    COUNT(*) as count,
    GROUP_CONCAT(primary_email, ', ') as emails
FROM people
WHERE first_name IS NOT NULL AND last_name IS NOT NULL
GROUP BY LOWER(first_name), LOWER(last_name)
HAVING COUNT(*) > 1;
""".format(datetime=datetime.now())
        
        with open(queries_path, 'w') as f:
            f.write(queries)
        
        self.log(f"\n📝 Sample queries saved to: {queries_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python build_candidate_database.py <source_directory>")
        print("Example: python build_candidate_database.py '/Users/charlie.kerr/Documents/CK Docs'")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_dir = Path(__file__).parent
    
    builder = DatabaseBuilder(source_dir, output_dir)
    builder.build_database()
    
    print("\n" + "="*65)
    print("✅ SUCCESS! Your database is ready.")
    print("="*65)
    print(f"\nDatabase file: {builder.db_path}")
    print(f"Quality report: {output_dir}/data_quality_report.txt")
    print(f"Sample queries: {output_dir}/sample_queries.sql")
    print("\nTo query your database:")
    print(f"  sqlite3 {builder.db_path}")
    print("  .tables")
    print("  SELECT COUNT(*) FROM people;")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# ABOUTME: Phase 3 - GitHub enrichment and matching
# ABOUTME: Matches GitHub profiles to existing candidates, creates new profiles, tracks contributions

"""
Talent Intelligence Database Builder - Phase 3: GitHub Enrichment

This script:
1. Processes enriched GitHub profile data
2. Matches GitHub profiles to existing candidates (email, name+company, Twitter)
3. Enriches existing candidates with GitHub stats
4. Creates new candidate profiles for unmatched GitHub users (if name + email)
5. Tracks GitHub contributions to companies/repos
6. Flags uncertain matches for manual review

Run this AFTER Phase 1 (candidates) and Phase 2 (companies)
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
BATCH_SIZE = 1000
MIN_MATCH_CONFIDENCE = 0.7  # Auto-match threshold

class GitHubEnrichmentBuilder:
    def __init__(self, db_path: str, github_csv_path: str):
        self.db_path = Path(db_path)
        self.github_csv = Path(github_csv_path)
        self.conn = None
        
        # Matching indexes (loaded from database)
        self.email_to_person = {}  # email -> person_id
        self.twitter_to_person = {}  # twitter -> person_id
        self.name_company_to_person = {}  # (name, company) -> person_id
        self.existing_person_ids = set()  # Track all existing person IDs
        
        # Statistics
        self.stats = {
            'github_profiles_processed': 0,
            'exact_matches': 0,
            'medium_confidence_matches': 0,
            'low_confidence_matches': 0,
            'no_match': 0,
            'new_candidates_created': 0,
            'existing_candidates_enriched': 0,
            'flagged_for_review': 0,
            'contributions_tracked': 0,
            'skipped_duplicate_person': 0
        }
        
        # Logging
        self.log_file = self.db_path.parent / "github_enrichment_log.txt"
        self.log(f"=== GitHub Enrichment Started: {datetime.now()} ===")
    
    def log(self, message: str):
        """Log to both console and file"""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def create_github_schema(self):
        """Create GitHub-related tables"""
        self.log("\n📊 Creating GitHub schema...")
        
        cursor = self.conn.cursor()
        
        # GitHub profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_profiles (
                github_profile_id TEXT PRIMARY KEY,
                person_id TEXT,
                github_username TEXT,
                github_name TEXT,
                github_email TEXT,
                github_company TEXT,
                github_location TEXT,
                personal_website TEXT,
                twitter_username TEXT,
                public_repos INTEGER,
                public_gists INTEGER,
                followers INTEGER,
                following INTEGER,
                num_contributions INTEGER,
                num_orgs INTEGER,
                num_starred INTEGER,
                match_confidence REAL,
                match_method TEXT,
                needs_review INTEGER DEFAULT 0,
                needs_enrichment INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (person_id) REFERENCES people(person_id)
            )
        """)
        
        # GitHub contributions to repos/companies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_contributions (
                contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_profile_id TEXT NOT NULL,
                person_id TEXT,
                repo_name TEXT,
                company_name TEXT,
                contribution_count INTEGER,
                created_at TEXT,
                FOREIGN KEY (github_profile_id) REFERENCES github_profiles(github_profile_id),
                FOREIGN KEY (person_id) REFERENCES people(person_id)
            )
        """)
        
        # Manual review queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_match_reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_profile_id TEXT NOT NULL,
                candidate_person_id TEXT,
                match_confidence REAL,
                match_reason TEXT,
                status TEXT DEFAULT 'pending',
                reviewed_at TEXT,
                action TEXT,
                created_at TEXT,
                FOREIGN KEY (github_profile_id) REFERENCES github_profiles(github_profile_id),
                FOREIGN KEY (candidate_person_id) REFERENCES people(person_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_person ON github_profiles(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_username ON github_profiles(github_username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_email ON github_profiles(github_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_twitter ON github_profiles(twitter_username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_needs_review ON github_profiles(needs_review)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contributions_profile ON github_contributions(github_profile_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contributions_person ON github_contributions(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_status ON github_match_reviews(status)")
        
        self.conn.commit()
        self.log("✅ GitHub schema created")
    
    def load_matching_indexes(self):
        """Load existing people data for matching"""
        self.log("\n📥 Loading matching indexes from database...")
        
        cursor = self.conn.cursor()
        
        # Load all existing person IDs
        cursor.execute("SELECT person_id FROM people")
        for (person_id,) in cursor.fetchall():
            self.existing_person_ids.add(person_id)
        
        # Load email index
        cursor.execute("SELECT person_id, email FROM emails")
        for person_id, email in cursor.fetchall():
            if email:
                self.email_to_person[email.lower().strip()] = person_id
        
        # Load primary emails
        cursor.execute("SELECT person_id, primary_email FROM people WHERE primary_email IS NOT NULL")
        for person_id, email in cursor.fetchall():
            if email:
                self.email_to_person[email.lower().strip()] = person_id
        
        # Load Twitter from social profiles
        cursor.execute("""
            SELECT person_id, username FROM social_profiles 
            WHERE platform = 'twitter' AND username IS NOT NULL
        """)
        for person_id, twitter in cursor.fetchall():
            if twitter:
                clean_twitter = twitter.lower().strip().replace('@', '')
                self.twitter_to_person[clean_twitter] = person_id
        
        # Load name + company index
        cursor.execute("""
            SELECT p.person_id, p.first_name, p.last_name, e.company_name
            FROM people p
            JOIN employment e ON p.person_id = e.person_id
            WHERE p.first_name IS NOT NULL AND p.last_name IS NOT NULL
            AND e.company_name IS NOT NULL AND e.is_current = 1
        """)
        for person_id, first, last, company in cursor.fetchall():
            key = self.normalize_name_company(first, last, company)
            if key:
                self.name_company_to_person[key] = person_id
        
        self.log(f"  Loaded {len(self.existing_person_ids):,} existing person IDs")
        self.log(f"  Loaded {len(self.email_to_person):,} email mappings")
        self.log(f"  Loaded {len(self.twitter_to_person):,} Twitter mappings")
        self.log(f"  Loaded {len(self.name_company_to_person):,} name+company mappings")
    
    def normalize_name_company(self, first: str, last: str, company: str) -> Optional[str]:
        """Create normalized key for name + company matching"""
        if not first or not last or not company:
            return None
        
        first = str(first).lower().strip()
        last = str(last).lower().strip()
        company = str(company).lower().strip()
        
        # Remove common company suffixes
        company = re.sub(r'\s+(inc|corp|llc|ltd|labs|technologies)\.?$', '', company)
        
        return f"{first}|{last}|{company}"
    
    def normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize email for matching"""
        if not email or not str(email).strip():
            return None
        return str(email).lower().strip()
    
    def normalize_twitter(self, twitter: Optional[str]) -> Optional[str]:
        """Normalize Twitter username"""
        if not twitter or not str(twitter).strip():
            return None
        return str(twitter).lower().strip().replace('@', '').replace('twitter.com/', '').replace('x.com/', '')
    
    def parse_github_name(self, name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Parse GitHub name into first/last"""
        if not name or not str(name).strip():
            return None, None
        
        name = str(name).strip()
        parts = name.split()
        
        if len(parts) == 0:
            return None, None
        elif len(parts) == 1:
            return parts[0], None
        else:
            return parts[0], ' '.join(parts[1:])
    
    def find_matching_person(self, github_record: Dict) -> Tuple[Optional[str], float, str]:
        """
        Find matching person in database
        Returns: (person_id, confidence, method)
        """
        # Match 1: Email (high confidence)
        email = self.normalize_email(github_record.get('Email'))
        if email and email in self.email_to_person:
            return self.email_to_person[email], 1.0, 'email'
        
        # Match 2: Twitter username (medium confidence)
        twitter = self.normalize_twitter(github_record.get('Twitter Username'))
        if twitter and twitter in self.twitter_to_person:
            return self.twitter_to_person[twitter], 0.85, 'twitter'
        
        # Match 3: Name + Company (medium confidence)
        github_name = github_record.get('Name - Data')
        github_company = github_record.get('Company - Data')
        
        if github_name and github_company:
            first, last = self.parse_github_name(github_name)
            if first and last:
                key = self.normalize_name_company(first, last, github_company)
                if key and key in self.name_company_to_person:
                    return self.name_company_to_person[key], 0.75, 'name_company'
        
        return None, 0.0, 'no_match'
    
    def generate_github_profile_id(self, username: str) -> str:
        """Generate stable GitHub profile ID"""
        return 'gh_' + hashlib.md5(username.lower().encode()).hexdigest()[:12]
    
    def generate_unique_person_id(self, base_string: str) -> str:
        """Generate a unique person_id that doesn't conflict"""
        # Start with hash of base string
        base_id = hashlib.md5(base_string.encode()).hexdigest()[:12]
        
        # If it doesn't exist, use it
        if base_id not in self.existing_person_ids:
            self.existing_person_ids.add(base_id)
            return base_id
        
        # If it exists, append counter until we find a unique one
        counter = 1
        while True:
            candidate_id = hashlib.md5(f"{base_string}_{counter}".encode()).hexdigest()[:12]
            if candidate_id not in self.existing_person_ids:
                self.existing_person_ids.add(candidate_id)
                return candidate_id
            counter += 1
    
    def create_new_person(self, github_record: Dict) -> Optional[str]:
        """Create a new person record from GitHub data"""
        # Only create if we have name + email
        name = github_record.get('Name - Data')
        email = self.normalize_email(github_record.get('Email'))
        
        if not name or not email:
            return None
        
        # Check if this email already exists (shouldn't happen, but double-check)
        if email in self.email_to_person:
            self.stats['skipped_duplicate_person'] += 1
            return self.email_to_person[email]
        
        first, last = self.parse_github_name(name)
        if not first:
            return None
        
        # Generate unique person_id
        person_id = self.generate_unique_person_id(email)
        
        cursor = self.conn.cursor()
        
        try:
            # Insert into people table
            cursor.execute("""
                INSERT INTO people (
                    person_id, first_name, last_name, primary_email,
                    location, status, created_at, updated_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                first,
                last,
                email,
                github_record.get('Location - Data'),
                'github_sourced',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                'Created from GitHub enrichment - needs further enrichment'
            ))
            
            # Add to email index
            self.email_to_person[email] = person_id
            
            # Add email
            cursor.execute("""
                INSERT INTO emails (person_id, email, is_primary)
                VALUES (?, ?, 1)
            """, (person_id, email))
            
            # Add Twitter if available
            twitter = github_record.get('Twitter Username')
            if twitter:
                cursor.execute("""
                    INSERT OR IGNORE INTO social_profiles (person_id, platform, username)
                    VALUES (?, 'twitter', ?)
                """, (person_id, twitter))
            
            # Add website if available
            website = github_record.get('Blog - Data')
            if website and str(website).strip():
                cursor.execute("""
                    INSERT OR IGNORE INTO social_profiles (person_id, platform, profile_url)
                    VALUES (?, 'website', ?)
                """, (person_id, str(website).strip()))
            
            # Add employment if company available
            company = github_record.get('Company - Data')
            if company and str(company).strip():
                cursor.execute("""
                    INSERT INTO employment (person_id, company_name, is_current)
                    VALUES (?, ?, 1)
                """, (person_id, str(company).strip()))
            
            self.stats['new_candidates_created'] += 1
            
            return person_id
            
        except sqlite3.IntegrityError as e:
            self.log(f"  ⚠️  Failed to create person for {email}: {str(e)}")
            self.stats['skipped_duplicate_person'] += 1
            return None
    
    def insert_github_profile(self, github_record: Dict, person_id: Optional[str], 
                            confidence: float, match_method: str):
        """Insert GitHub profile data"""
        username = github_record.get('contrib_usernames')
        if not username:
            return
        
        github_profile_id = self.generate_github_profile_id(username)
        
        # Determine if needs review
        needs_review = 1 if (person_id and confidence < 1.0) else 0
        
        # Determine if needs enrichment (new person created)
        needs_enrichment = 1 if (person_id and match_method == 'new_person') else 0
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO github_profiles (
                github_profile_id, person_id, github_username, github_name,
                github_email, github_company, github_location, personal_website,
                twitter_username, public_repos, public_gists, followers,
                following, num_contributions, num_orgs, num_starred,
                match_confidence, match_method, needs_review, needs_enrichment,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            github_profile_id,
            person_id,
            username,
            github_record.get('Name - Data'),
            github_record.get('Email'),
            github_record.get('Company - Data'),
            github_record.get('Location - Data'),
            github_record.get('Blog - Data'),
            github_record.get('Twitter Username'),
            github_record.get('Public Repos - Data'),
            github_record.get('Public Gists - Data'),
            github_record.get('Followers - Data'),
            github_record.get('Following - Data'),
            github_record.get('Num Contributions - Data'),
            github_record.get('Num Orgs - Data'),
            github_record.get('Num Starred - Data'),
            confidence,
            match_method,
            needs_review,
            needs_enrichment,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Track contributions
        contributed_to = github_record.get('Contributed To')
        if contributed_to and str(contributed_to).strip():
            cursor.execute("""
                INSERT INTO github_contributions (
                    github_profile_id, person_id, repo_name, created_at
                ) VALUES (?, ?, ?, ?)
            """, (
                github_profile_id,
                person_id,
                str(contributed_to).strip(),
                datetime.now().isoformat()
            ))
            self.stats['contributions_tracked'] += 1
        
        # Add to review queue if needed
        if needs_review and person_id:
            cursor.execute("""
                INSERT INTO github_match_reviews (
                    github_profile_id, candidate_person_id, match_confidence,
                    match_reason, status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', ?)
            """, (
                github_profile_id,
                person_id,
                confidence,
                f"Matched via {match_method}",
                datetime.now().isoformat()
            ))
            self.stats['flagged_for_review'] += 1
        
        # Update person's GitHub social profile if matched
        if person_id and confidence >= MIN_MATCH_CONFIDENCE:
            cursor.execute("""
                INSERT OR REPLACE INTO social_profiles (person_id, platform, profile_url, username)
                VALUES (?, 'github', ?, ?)
            """, (person_id, f"github.com/{username}", username))
            
            if match_method != 'new_person':
                self.stats['existing_candidates_enriched'] += 1
    
    def process_github_csv(self):
        """Process the GitHub CSV file"""
        self.log(f"\n📥 Processing GitHub CSV: {self.github_csv.name}")
        
        try:
            chunk_iter = pd.read_csv(
                self.github_csv,
                chunksize=BATCH_SIZE,
                low_memory=False,
                encoding='utf-8',
                on_bad_lines='skip'
            )
            
            for chunk_num, chunk in enumerate(chunk_iter):
                chunk = chunk.replace({np.nan: None})
                
                for _, row in chunk.iterrows():
                    record = row.to_dict()
                    
                    # Skip if no username
                    if not record.get('contrib_usernames'):
                        continue
                    
                    self.stats['github_profiles_processed'] += 1
                    
                    # Try to find matching person
                    person_id, confidence, method = self.find_matching_person(record)
                    
                    if person_id:
                        if confidence == 1.0:
                            self.stats['exact_matches'] += 1
                        elif confidence >= 0.75:
                            self.stats['medium_confidence_matches'] += 1
                        else:
                            self.stats['low_confidence_matches'] += 1
                    else:
                        # No match - try to create new person if we have name + email
                        person_id = self.create_new_person(record)
                        if person_id:
                            method = 'new_person'
                            confidence = 0.9
                        else:
                            self.stats['no_match'] += 1
                    
                    # Insert GitHub profile
                    self.insert_github_profile(record, person_id, confidence, method)
                
                # Commit every batch
                self.conn.commit()
                
                if (chunk_num + 1) % 10 == 0:
                    self.log(f"    Processed {(chunk_num + 1) * BATCH_SIZE:,} GitHub profiles...")
            
        except Exception as e:
            self.log(f"  ⚠️  Error processing GitHub CSV: {str(e)}")
            raise
    
    def build(self):
        """Main execution"""
        if not self.db_path.exists():
            self.log("❌ Database not found! Run Phase 1 and 2 first.")
            sys.exit(1)
        
        if not self.github_csv.exists():
            self.log(f"❌ GitHub CSV not found: {self.github_csv}")
            sys.exit(1)
        
        self.log("\n🚀 Starting GitHub enrichment...")
        self.log(f"Database: {self.db_path}")
        self.log(f"GitHub CSV: {self.github_csv}")
        
        # Connect to database
        self.conn = sqlite3.connect(self.db_path)
        
        # Create schema
        self.create_github_schema()
        
        # Load matching indexes
        self.load_matching_indexes()
        
        # Process GitHub CSV
        self.process_github_csv()
        
        # Generate report
        self.generate_github_report()
        
        # Close database
        self.conn.close()
        
        self.log("\n✅ GitHub enrichment complete!")
    
    def generate_github_report(self):
        """Generate GitHub enrichment report"""
        report_path = self.db_path.parent / "github_enrichment_report.txt"
        
        cursor = self.conn.cursor()
        
        # Get additional stats
        cursor.execute("SELECT COUNT(*) FROM github_profiles")
        total_profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE person_id IS NOT NULL")
        linked_profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE needs_review = 1")
        needs_review = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE needs_enrichment = 1")
        needs_enrichment = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT person_id) FROM github_profiles WHERE person_id IS NOT NULL")
        unique_people_with_github = cursor.fetchone()[0]
        
        report = f"""
=================================================================
GITHUB ENRICHMENT REPORT
Generated: {datetime.now()}
=================================================================

PROCESSING STATISTICS
---------------------
GitHub Profiles Processed: {self.stats['github_profiles_processed']:,}

MATCHING RESULTS
----------------
Exact Matches (email): {self.stats['exact_matches']:,}
Medium Confidence (Twitter, name+company): {self.stats['medium_confidence_matches']:,}
Low Confidence: {self.stats['low_confidence_matches']:,}
No Match: {self.stats['no_match']:,}
Skipped (duplicate person_id): {self.stats['skipped_duplicate_person']:,}

ACTIONS TAKEN
-------------
Existing Candidates Enriched: {self.stats['existing_candidates_enriched']:,}
New Candidates Created: {self.stats['new_candidates_created']:,}
Flagged for Manual Review: {self.stats['flagged_for_review']:,}
Contributions Tracked: {self.stats['contributions_tracked']:,}

DATABASE STATISTICS
-------------------
Total GitHub Profiles: {total_profiles:,}
Linked to People: {linked_profiles:,} ({linked_profiles/total_profiles*100:.1f}%)
Unique People with GitHub: {unique_people_with_github:,}
Needs Manual Review: {needs_review:,}
Needs Further Enrichment: {needs_enrichment:,}

NEXT STEPS
----------
1. Review matches: SELECT * FROM github_match_reviews WHERE status='pending';
2. Check new candidates: SELECT * FROM people WHERE status='github_sourced';
3. View enriched profiles: SELECT * FROM github_profiles WHERE person_id IS NOT NULL;

=================================================================
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        self.log(report)
        self.log(f"\n📊 GitHub report saved to: {report_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python build_github_enrichment.py <database_path> <github_csv_path>")
        print("Example: python build_github_enrichment.py ./talent_intelligence.db ./github_data.csv")
        sys.exit(1)
    
    db_path = sys.argv[1]
    github_csv = sys.argv[2]
    
    if not Path(db_path).exists():
        print("❌ Database not found! Run Phase 1 and 2 first.")
        sys.exit(1)
    
    if not Path(github_csv).exists():
        print(f"❌ GitHub CSV not found: {github_csv}")
        sys.exit(1)
    
    builder = GitHubEnrichmentBuilder(db_path, github_csv)
    builder.build()
    
    print("\n" + "="*65)
    print("✅ SUCCESS! GitHub enrichment complete.")
    print("="*65)
    print(f"\nDatabase file: {db_path}")
    print(f"Enrichment report: {Path(db_path).parent}/github_enrichment_report.txt")
    print("\nTo query GitHub data:")
    print(f"  sqlite3 {db_path}")
    print("  SELECT COUNT(*) FROM github_profiles;")
    print("  SELECT * FROM github_match_reviews WHERE status='pending' LIMIT 10;")
    print()


if __name__ == "__main__":
    main()

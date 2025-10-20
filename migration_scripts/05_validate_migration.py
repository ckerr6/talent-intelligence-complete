#!/usr/bin/env python3
"""
Migration Validation Script
Validates data integrity after migration and deduplication
"""

import sys
import os
import sqlite3
import psycopg2
from typing import Dict, List

class MigrationValidator:
    def __init__(self, sqlite_db_path: str, pg_conn_params: dict):
        self.sqlite_path = sqlite_db_path
        self.pg_params = pg_conn_params
        self.validation_results = {
            'passed': [],
            'warnings': [],
            'failed': []
        }
        
    def connect_databases(self):
        """Establish connections"""
        print("📡 Connecting to databases...")
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        self.pg_conn = psycopg2.connect(**self.pg_params)
        self.pg_conn.autocommit = True
        
        print("✅ Connections established")
    
    def test_schema_exists(self):
        """Test that all new tables and columns exist"""
        print("\n🔍 Testing schema...")
        
        cursor = self.pg_conn.cursor()
        
        required_tables = [
            'person',
            'person_email',
            'github_profile',
            'github_repository',
            'github_contribution',
            'migration_log'
        ]
        
        for table in required_tables:
            cursor.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            """, (table,))
            
            if cursor.fetchone():
                self.validation_results['passed'].append(f"Table {table} exists")
            else:
                self.validation_results['failed'].append(f"Table {table} missing")
        
        # Check normalized_linkedin_url column
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'person'
            AND column_name = 'normalized_linkedin_url'
        """)
        
        if cursor.fetchone():
            self.validation_results['passed'].append("Column normalized_linkedin_url exists")
        else:
            self.validation_results['failed'].append("Column normalized_linkedin_url missing")
    
    def test_email_migration(self):
        """Test email migration completeness"""
        print("\n📧 Testing email migration...")
        
        # Count emails in SQLite
        sqlite_cursor = self.sqlite_conn.cursor()
        
        sqlite_cursor.execute("""
            SELECT COUNT(DISTINCT email) FROM (
                SELECT primary_email as email FROM people WHERE primary_email IS NOT NULL
                UNION
                SELECT email FROM emails WHERE email IS NOT NULL
            )
        """)
        sqlite_email_count = sqlite_cursor.fetchone()[0]
        
        # Count emails in PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute("SELECT COUNT(*) FROM person_email")
        pg_email_count = pg_cursor.fetchone()[0]
        
        # Calculate percentage
        if sqlite_email_count > 0:
            percentage = (pg_email_count / sqlite_email_count) * 100
            message = f"Emails migrated: {pg_email_count:,}/{sqlite_email_count:,} ({percentage:.1f}%)"
            
            if percentage >= 80:
                self.validation_results['passed'].append(message)
            elif percentage >= 50:
                self.validation_results['warnings'].append(message + " - Lower than expected")
            else:
                self.validation_results['failed'].append(message + " - Migration incomplete")
        else:
            self.validation_results['warnings'].append("No emails in SQLite to compare")
    
    def test_github_migration(self):
        """Test GitHub migration completeness"""
        print("\n👤 Testing GitHub migration...")
        
        # Count GitHub profiles in SQLite
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT COUNT(*) FROM github_profiles")
        sqlite_github_count = sqlite_cursor.fetchone()[0]
        
        # Count GitHub profiles in PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute("SELECT COUNT(*) FROM github_profile")
        pg_github_count = pg_cursor.fetchone()[0]
        
        # Calculate percentage
        if sqlite_github_count > 0:
            percentage = (pg_github_count / sqlite_github_count) * 100
            message = f"GitHub profiles migrated: {pg_github_count:,}/{sqlite_github_count:,} ({percentage:.1f}%)"
            
            if percentage >= 95:
                self.validation_results['passed'].append(message)
            elif percentage >= 80:
                self.validation_results['warnings'].append(message + " - Some profiles may be missing")
            else:
                self.validation_results['failed'].append(message + " - Migration incomplete")
        else:
            self.validation_results['warnings'].append("No GitHub profiles in SQLite to compare")
    
    def test_person_matching(self):
        """Test that GitHub profiles and emails are linked to people"""
        print("\n🔗 Testing person linkage...")
        
        cursor = self.pg_conn.cursor()
        
        # Check GitHub profiles linked to people
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(person_id) as linked
            FROM github_profile
        """)
        row = cursor.fetchone()
        total, linked = row[0], row[1]
        
        if total > 0:
            percentage = (linked / total) * 100
            message = f"GitHub profiles linked to people: {linked:,}/{total:,} ({percentage:.1f}%)"
            
            if percentage >= 40:  # Expected ~60% based on audit
                self.validation_results['passed'].append(message)
            elif percentage >= 20:
                self.validation_results['warnings'].append(message + " - Lower than expected")
            else:
                self.validation_results['failed'].append(message + " - Very low match rate")
    
    def test_no_data_loss(self):
        """Test that we haven't lost critical data"""
        print("\n🔍 Testing for data loss...")
        
        cursor = self.pg_conn.cursor()
        
        # Count people
        cursor.execute("SELECT COUNT(*) FROM person")
        person_count = cursor.fetchone()[0]
        
        if person_count >= 30000:  # Expected after deduplication
            self.validation_results['passed'].append(f"Person count: {person_count:,} ✓")
        elif person_count >= 20000:
            self.validation_results['warnings'].append(f"Person count: {person_count:,} - Lower than expected")
        else:
            self.validation_results['failed'].append(f"Person count: {person_count:,} - Too low!")
        
        # Count companies
        cursor.execute("SELECT COUNT(*) FROM company")
        company_count = cursor.fetchone()[0]
        
        if company_count >= 90000:
            self.validation_results['passed'].append(f"Company count: {company_count:,} ✓")
        else:
            self.validation_results['warnings'].append(f"Company count: {company_count:,}")
        
        # Count employment records
        cursor.execute("SELECT COUNT(*) FROM employment")
        employment_count = cursor.fetchone()[0]
        
        if employment_count >= 200000:
            self.validation_results['passed'].append(f"Employment records: {employment_count:,} ✓")
        else:
            self.validation_results['warnings'].append(f"Employment records: {employment_count:,}")
    
    def test_data_quality(self):
        """Test data quality metrics"""
        print("\n📊 Testing data quality...")
        
        cursor = self.pg_conn.cursor()
        
        # LinkedIn coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(linkedin_url) as with_linkedin
            FROM person
        """)
        row = cursor.fetchone()
        total, with_linkedin = row[0], row[1]
        
        if total > 0:
            percentage = (with_linkedin / total) * 100
            message = f"LinkedIn coverage: {percentage:.1f}%"
            
            if percentage >= 95:
                self.validation_results['passed'].append(message)
            else:
                self.validation_results['warnings'].append(message)
        
        # Email coverage
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT person_id) 
            FROM person_email
        """)
        people_with_email = cursor.fetchone()[0]
        
        if total > 0:
            percentage = (people_with_email / total) * 100
            message = f"Email coverage: {percentage:.1f}%"
            
            if percentage >= 20:  # Expected ~25-30% after migration
                self.validation_results['passed'].append(message)
            else:
                self.validation_results['warnings'].append(message + " - Lower than expected")
        
        # GitHub coverage
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT person_id)
            FROM github_profile
            WHERE person_id IS NOT NULL
        """)
        people_with_github = cursor.fetchone()[0]
        
        if total > 0:
            percentage = (people_with_github / total) * 100
            message = f"GitHub coverage: {percentage:.1f}%"
            
            if percentage >= 40:  # Expected ~60% after migration
                self.validation_results['passed'].append(message)
            else:
                self.validation_results['warnings'].append(message)
    
    def test_foreign_keys(self):
        """Test foreign key integrity"""
        print("\n🔗 Testing foreign key integrity...")
        
        cursor = self.pg_conn.cursor()
        
        # Test orphaned emails
        cursor.execute("""
            SELECT COUNT(*)
            FROM person_email pe
            WHERE NOT EXISTS (
                SELECT 1 FROM person p WHERE p.person_id = pe.person_id
            )
        """)
        orphaned_emails = cursor.fetchone()[0]
        
        if orphaned_emails == 0:
            self.validation_results['passed'].append("No orphaned emails")
        else:
            self.validation_results['failed'].append(f"Found {orphaned_emails} orphaned emails")
        
        # Test orphaned GitHub profiles (linked ones only)
        cursor.execute("""
            SELECT COUNT(*)
            FROM github_profile gp
            WHERE gp.person_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM person p WHERE p.person_id = gp.person_id
            )
        """)
        orphaned_github = cursor.fetchone()[0]
        
        if orphaned_github == 0:
            self.validation_results['passed'].append("No orphaned GitHub profiles")
        else:
            self.validation_results['failed'].append(f"Found {orphaned_github} orphaned GitHub profiles")
    
    def test_migration_logs(self):
        """Test that migration was logged"""
        print("\n📝 Testing migration logs...")
        
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT migration_name, status
            FROM migration_log
            WHERE migration_phase IN ('email', 'github', 'deduplication')
            ORDER BY started_at DESC
        """)
        
        logs = cursor.fetchall()
        
        if logs:
            for name, status in logs:
                if status == 'completed':
                    self.validation_results['passed'].append(f"Migration {name}: {status}")
                else:
                    self.validation_results['warnings'].append(f"Migration {name}: {status}")
        else:
            self.validation_results['warnings'].append("No migration logs found")
    
    def spot_check_profiles(self):
        """Spot check random profiles for data completeness"""
        print("\n🔍 Spot checking profiles...")
        
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.person_id::text,
                p.full_name,
                p.linkedin_url,
                COUNT(DISTINCT pe.email) as email_count,
                COUNT(DISTINCT gp.github_profile_id) as github_count,
                COUNT(DISTINCT e.employment_id) as employment_count
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
            LEFT JOIN employment e ON p.person_id = e.person_id
            WHERE p.linkedin_url IS NOT NULL
            GROUP BY p.person_id, p.full_name, p.linkedin_url
            ORDER BY RANDOM()
            LIMIT 10
        """)
        
        profiles = cursor.fetchall()
        
        complete_count = 0
        for profile in profiles:
            name, linkedin, email_count, github_count, employment_count = profile[1:]
            if email_count > 0 and employment_count > 0:
                complete_count += 1
        
        message = f"Spot check: {complete_count}/10 profiles have emails and employment"
        
        if complete_count >= 7:
            self.validation_results['passed'].append(message)
        elif complete_count >= 5:
            self.validation_results['warnings'].append(message)
        else:
            self.validation_results['failed'].append(message)
    
    def validate(self):
        """Run all validation tests"""
        print("\n" + "=" * 80)
        print("MIGRATION VALIDATION")
        print("=" * 80)
        
        self.connect_databases()
        
        try:
            # Run all tests
            self.test_schema_exists()
            self.test_email_migration()
            self.test_github_migration()
            self.test_person_matching()
            self.test_no_data_loss()
            self.test_data_quality()
            self.test_foreign_keys()
            self.test_migration_logs()
            self.spot_check_profiles()
            
            # Print results
            self.print_results()
            
        finally:
            self.sqlite_conn.close()
            self.pg_conn.close()
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        print(f"\n✅ PASSED ({len(self.validation_results['passed'])} tests)")
        for result in self.validation_results['passed']:
            print(f"   ✓ {result}")
        
        if self.validation_results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.validation_results['warnings'])} items)")
            for result in self.validation_results['warnings']:
                print(f"   ⚠ {result}")
        
        if self.validation_results['failed']:
            print(f"\n❌ FAILED ({len(self.validation_results['failed'])} tests)")
            for result in self.validation_results['failed']:
                print(f"   ✗ {result}")
        
        print("\n" + "=" * 80)
        
        # Summary
        total_tests = len(self.validation_results['passed']) + len(self.validation_results['warnings']) + len(self.validation_results['failed'])
        passed_count = len(self.validation_results['passed'])
        
        if passed_count == total_tests:
            print("🎉 All tests passed!")
        elif not self.validation_results['failed']:
            print("✅ Validation passed with warnings")
        else:
            print("⚠️  Validation completed with failures - review required")
        
        print("=" * 80)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate migration results')
    parser.add_argument('--sqlite-db', default='../talent_intelligence.db',
                       help='Path to SQLite database')
    parser.add_argument('--pg-host', default='localhost',
                       help='PostgreSQL host')
    parser.add_argument('--pg-port', default='5432',
                       help='PostgreSQL port')
    parser.add_argument('--pg-db', default='talent',
                       help='PostgreSQL database name')
    parser.add_argument('--pg-user', default=os.environ.get('USER'),
                       help='PostgreSQL user')
    
    args = parser.parse_args()
    
    pg_params = {
        'host': args.pg_host,
        'port': args.pg_port,
        'database': args.pg_db,
        'user': args.pg_user
    }
    
    validator = MigrationValidator(args.sqlite_db, pg_params)
    validator.validate()


if __name__ == '__main__':
    main()


# ABOUTME: Comprehensive data quality checking for PostgreSQL talent database
# ABOUTME: Identifies specific issues with actionable SQL fixes

#!/usr/bin/env python3

import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from config import Config, get_db_connection


class DataQualityChecker:
    """Comprehensive data quality checker"""
    
    def __init__(self):
        import psycopg2
        # Use regular connection without dict cursor for simpler access
        self.conn = psycopg2.connect(
            host=Config.PG_HOST,
            port=Config.PG_PORT,
            database=Config.PG_DATABASE,
            user=Config.PG_USER,
            password=Config.PG_PASSWORD
        )
        self.issues = []
        self.stats = {}
    
    def check_all(self):
        """Run all quality checks"""
        print("="*80)
        print("DATA QUALITY CHECK - PostgreSQL talent database")
        print("="*80)
        
        self.check_missing_critical_fields()
        self.check_invalid_data_formats()
        self.check_duplicate_linkedin_urls()
        self.check_duplicate_emails()
        self.check_orphaned_records()
        self.check_referential_integrity()
        self.check_data_staleness()
        self.check_coverage_gaps()
        
        self.print_summary()
        self.generate_fix_sql()
    
    def check_missing_critical_fields(self):
        """Check for records missing critical fields"""
        print("\n🔍 Checking for missing critical fields...")
        
        cursor = self.conn.cursor()
        
        # Check people missing name
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE full_name IS NULL OR full_name = ''
            OR (first_name IS NULL OR first_name = '')
            OR (last_name IS NULL OR last_name = '')
        """)
        missing_name = cursor.fetchone()[0]
        
        if missing_name > 0:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'missing_data',
                'message': f'{missing_name:,} people missing name fields',
                'fix_sql': "-- Review people with missing names\nSELECT person_id, full_name, first_name, last_name FROM person WHERE full_name IS NULL OR full_name = '';"
            })
        
        # Check people missing LinkedIn
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE normalized_linkedin_url IS NULL OR normalized_linkedin_url = ''
        """)
        missing_linkedin = cursor.fetchone()[0]
        
        if missing_linkedin > 0:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'missing_data',
                'message': f'{missing_linkedin:,} people missing LinkedIn URL',
                'fix_sql': "-- Review people without LinkedIn\nSELECT person_id, full_name, linkedin_url FROM person WHERE normalized_linkedin_url IS NULL OR normalized_linkedin_url = '';"
            })
        
        print(f"   Found {len([i for i in self.issues if i['category'] == 'missing_data'])} missing data issues")
    
    def check_invalid_data_formats(self):
        """Check for invalid data formats"""
        print("\n🔍 Checking for invalid data formats...")
        
        cursor = self.conn.cursor()
        
        # Check for invalid emails
        cursor.execute("""
            SELECT COUNT(*) FROM person_email
            WHERE email NOT LIKE '%_@%_.%_'
        """)
        invalid_emails = cursor.fetchone()[0]
        
        if invalid_emails > 0:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'invalid_format',
                'message': f'{invalid_emails:,} invalid email formats',
                'fix_sql': "-- Review invalid emails\nSELECT email FROM person_email WHERE email NOT LIKE '%_@%_.%_' LIMIT 50;"
            })
        
        # Check for invalid LinkedIn URLs
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE normalized_linkedin_url IS NOT NULL
            AND normalized_linkedin_url != ''
            AND normalized_linkedin_url NOT LIKE 'linkedin.com/in/%'
        """)
        invalid_linkedin = cursor.fetchone()[0]
        
        if invalid_linkedin > 0:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'invalid_format',
                'message': f'{invalid_linkedin:,} invalid LinkedIn URL formats',
                'fix_sql': "-- Review invalid LinkedIn URLs\nSELECT person_id, normalized_linkedin_url FROM person WHERE normalized_linkedin_url NOT LIKE 'linkedin.com/in/%' LIMIT 50;"
            })
        
        print(f"   Found {len([i for i in self.issues if i['category'] == 'invalid_format'])} format issues")
    
    def check_duplicate_linkedin_urls(self):
        """Check for duplicate LinkedIn URLs"""
        print("\n🔍 Checking for duplicate LinkedIn URLs...")
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                normalized_linkedin_url,
                COUNT(*) as count
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
            AND normalized_linkedin_url != ''
            GROUP BY normalized_linkedin_url
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            total_dupes = sum(row[1] - 1 for row in duplicates)  # -1 because we keep one
            self.issues.append({
                'severity': 'HIGH',
                'category': 'duplicates',
                'message': f'{total_dupes:,} duplicate people by LinkedIn URL ({len(duplicates)} groups)',
                'fix_sql': "-- Run deduplication script\npython3 migration_scripts/04_deduplicate_people.py"
            })
        
        self.stats['linkedin_duplicates'] = len(duplicates)
        print(f"   Found {len(duplicates)} groups of LinkedIn duplicates")
    
    def check_duplicate_emails(self):
        """Check for duplicate email addresses"""
        print("\n🔍 Checking for duplicate emails...")
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                lower(email) as email,
                COUNT(DISTINCT person_id) as person_count
            FROM person_email
            GROUP BY lower(email)
            HAVING COUNT(DISTINCT person_id) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'duplicates',
                'message': f'{len(duplicates):,} emails shared by multiple people',
                'fix_sql': "-- Review shared emails\nSELECT lower(email) as email, COUNT(DISTINCT person_id) as people FROM person_email GROUP BY lower(email) HAVING COUNT(DISTINCT person_id) > 1;"
            })
        
        self.stats['email_duplicates'] = len(duplicates)
        print(f"   Found {len(duplicates)} emails shared by multiple people")
    
    def check_orphaned_records(self):
        """Check for orphaned records"""
        print("\n🔍 Checking for orphaned records...")
        
        cursor = self.conn.cursor()
        
        # Check employment without person
        cursor.execute("""
            SELECT COUNT(*) FROM employment e
            WHERE NOT EXISTS (SELECT 1 FROM person p WHERE p.person_id = e.person_id)
        """)
        orphaned_employment = cursor.fetchone()[0]
        
        if orphaned_employment > 0:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'orphaned',
                'message': f'{orphaned_employment:,} employment records without person',
                'fix_sql': "-- Delete orphaned employment\nDELETE FROM employment WHERE NOT EXISTS (SELECT 1 FROM person WHERE person.person_id = employment.person_id);"
            })
        
        # Check emails without person
        cursor.execute("""
            SELECT COUNT(*) FROM person_email pe
            WHERE NOT EXISTS (SELECT 1 FROM person p WHERE p.person_id = pe.person_id)
        """)
        orphaned_emails = cursor.fetchone()[0]
        
        if orphaned_emails > 0:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'orphaned',
                'message': f'{orphaned_emails:,} emails without person',
                'fix_sql': "-- Delete orphaned emails\nDELETE FROM person_email WHERE NOT EXISTS (SELECT 1 FROM person WHERE person.person_id = person_email.person_id);"
            })
        
        print(f"   Found {len([i for i in self.issues if i['category'] == 'orphaned'])} orphaned record issues")
    
    def check_referential_integrity(self):
        """Check referential integrity"""
        print("\n🔍 Checking referential integrity...")
        
        cursor = self.conn.cursor()
        
        # Check employment with invalid company_id
        cursor.execute("""
            SELECT COUNT(*) FROM employment e
            WHERE e.company_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM company c WHERE c.company_id = e.company_id)
        """)
        invalid_companies = cursor.fetchone()[0]
        
        if invalid_companies > 0:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'referential_integrity',
                'message': f'{invalid_companies:,} employment records with invalid company_id',
                'fix_sql': "-- Review employment with invalid companies\nSELECT * FROM employment WHERE company_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM company WHERE company.company_id = employment.company_id) LIMIT 50;"
            })
        
        print(f"   Found {len([i for i in self.issues if i['category'] == 'referential_integrity'])} referential integrity issues")
    
    def check_data_staleness(self):
        """Check for stale data"""
        print("\n🔍 Checking for data staleness...")
        
        cursor = self.conn.cursor()
        
        # Check for people not refreshed in over a year
        one_year_ago = datetime.now() - timedelta(days=365)
        
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE refreshed_at IS NOT NULL
            AND refreshed_at < %s
        """, (one_year_ago,))
        stale_count = cursor.fetchone()[0]
        
        if stale_count > 0:
            self.issues.append({
                'severity': 'LOW',
                'category': 'staleness',
                'message': f'{stale_count:,} people not refreshed in over a year',
                'fix_sql': "-- Review stale records\nSELECT person_id, full_name, refreshed_at FROM person WHERE refreshed_at < NOW() - INTERVAL '1 year' LIMIT 50;"
            })
        
        self.stats['stale_records'] = stale_count
        print(f"   Found {stale_count:,} stale records")
    
    def check_coverage_gaps(self):
        """Check for coverage gaps"""
        print("\n🔍 Checking coverage gaps...")
        
        cursor = self.conn.cursor()
        
        # Get coverage statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_people,
                COUNT(DISTINCT pe.person_id) as with_email,
                COUNT(DISTINCT gp.person_id) as with_github,
                COUNT(DISTINCT e.person_id) as with_employment
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
            LEFT JOIN employment e ON p.person_id = e.person_id
        """)
        
        result = cursor.fetchone()
        total = result[0]
        with_email = result[1]
        with_github = result[2]
        with_employment = result[3]
        
        email_coverage = (with_email / total * 100) if total > 0 else 0
        github_coverage = (with_github / total * 100) if total > 0 else 0
        employment_coverage = (with_employment / total * 100) if total > 0 else 0
        
        self.stats['email_coverage'] = email_coverage
        self.stats['github_coverage'] = github_coverage
        self.stats['employment_coverage'] = employment_coverage
        
        # Flag low coverage areas
        if email_coverage < 50:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'low_coverage',
                'message': f'Low email coverage: {email_coverage:.1f}%',
                'fix_sql': "-- Consider enriching from additional sources"
            })
        
        if employment_coverage < 80:
            self.issues.append({
                'severity': 'LOW',
                'category': 'low_coverage',
                'message': f'Low employment coverage: {employment_coverage:.1f}%',
                'fix_sql': "-- Consider importing from LinkedIn data"
            })
        
        print(f"   Email coverage: {email_coverage:.1f}%")
        print(f"   GitHub coverage: {github_coverage:.1f}%")
        print(f"   Employment coverage: {employment_coverage:.1f}%")
    
    def print_summary(self):
        """Print issues summary"""
        print("\n" + "="*80)
        print("QUALITY CHECK SUMMARY")
        print("="*80)
        
        if not self.issues:
            print("\n✅ No data quality issues found!")
            return
        
        # Group by severity
        high = [i for i in self.issues if i['severity'] == 'HIGH']
        medium = [i for i in self.issues if i['severity'] == 'MEDIUM']
        low = [i for i in self.issues if i['severity'] == 'LOW']
        
        print(f"\nTotal issues found: {len(self.issues)}")
        print(f"  🔴 High severity: {len(high)}")
        print(f"  🟡 Medium severity: {len(medium)}")
        print(f"  🟢 Low severity: {len(low)}")
        
        print("\n" + "-"*80)
        print("ISSUES BY PRIORITY:")
        print("-"*80)
        
        for severity, issues in [('HIGH', high), ('MEDIUM', medium), ('LOW', low)]:
            if issues:
                print(f"\n{severity} SEVERITY:")
                for i, issue in enumerate(issues, 1):
                    print(f"  {i}. {issue['message']}")
    
    def generate_fix_sql(self):
        """Generate SQL scripts to fix issues"""
        if not self.issues:
            return
        
        output_file = Config.REPORTS_DIR / f"quality_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with open(output_file, 'w') as f:
            f.write("-- DATA QUALITY FIX SQL\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Review and execute each statement carefully\n\n")
            
            for issue in self.issues:
                f.write(f"-- {issue['severity']}: {issue['message']}\n")
                f.write(f"{issue['fix_sql']}\n\n")
        
        print(f"\n📄 Fix SQL generated: {output_file}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    """Main execution"""
    checker = DataQualityChecker()
    
    try:
        checker.check_all()
    finally:
        checker.close()
    
    print("\n✅ Quality check complete!")


if __name__ == "__main__":
    main()


# ABOUTME: Generate quality metrics for dashboard and monitoring
# ABOUTME: Exports comprehensive metrics to JSON for tracking over time

#!/usr/bin/env python3

import json
import psycopg2
from datetime import datetime
from pathlib import Path
from config import Config, get_db_connection


class QualityMetricsGenerator:
    """Generate comprehensive quality metrics"""
    
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
        self.metrics = {
            'generated_at': datetime.now().isoformat(),
            'database': Config.PG_DATABASE,
            'totals': {},
            'coverage': {},
            'quality_distribution': {},
            'freshness': {},
            'growth': {}
        }
    
    def generate_all(self):
        """Generate all metrics"""
        print("="*80)
        print("QUALITY METRICS GENERATION")
        print("="*80)
        
        self.generate_totals()
        self.generate_coverage_metrics()
        self.generate_quality_distribution()
        self.generate_freshness_metrics()
        self.generate_growth_metrics()
        
        self.save_metrics()
        self.print_summary()
    
    def generate_totals(self):
        """Generate total record counts"""
        print("\n📊 Generating total counts...")
        
        cursor = self.conn.cursor()
        
        # People
        cursor.execute("SELECT COUNT(*) FROM person")
        self.metrics['totals']['people'] = cursor.fetchone()[0]
        
        # Companies
        cursor.execute("SELECT COUNT(*) FROM company")
        self.metrics['totals']['companies'] = cursor.fetchone()[0]
        
        # Employment records
        cursor.execute("SELECT COUNT(*) FROM employment")
        self.metrics['totals']['employment_records'] = cursor.fetchone()[0]
        
        # Emails
        cursor.execute("SELECT COUNT(*) FROM person_email")
        self.metrics['totals']['emails'] = cursor.fetchone()[0]
        
        # GitHub profiles
        cursor.execute("SELECT COUNT(*) FROM github_profile")
        self.metrics['totals']['github_profiles'] = cursor.fetchone()[0]
        
        # GitHub repositories
        cursor.execute("SELECT COUNT(*) FROM github_repository")
        self.metrics['totals']['github_repositories'] = cursor.fetchone()[0]
        
        # Education records
        cursor.execute("SELECT COUNT(*) FROM education")
        self.metrics['totals']['education_records'] = cursor.fetchone()[0]
        
        print(f"   People: {self.metrics['totals']['people']:,}")
        print(f"   Companies: {self.metrics['totals']['companies']:,}")
        print(f"   Employment records: {self.metrics['totals']['employment_records']:,}")
    
    def generate_coverage_metrics(self):
        """Generate coverage percentages"""
        print("\n📊 Generating coverage metrics...")
        
        cursor = self.conn.cursor()
        total_people = self.metrics['totals']['people']
        
        if total_people == 0:
            return
        
        # LinkedIn coverage
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE normalized_linkedin_url IS NOT NULL
            AND normalized_linkedin_url != ''
        """)
        with_linkedin = cursor.fetchone()[0]
        self.metrics['coverage']['linkedin'] = {
            'count': with_linkedin,
            'percentage': round((with_linkedin / total_people) * 100, 2)
        }
        
        # Email coverage
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) FROM person_email
        """)
        with_email = cursor.fetchone()[0]
        self.metrics['coverage']['email'] = {
            'count': with_email,
            'percentage': round((with_email / total_people) * 100, 2)
        }
        
        # GitHub coverage
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) FROM github_profile
        """)
        with_github = cursor.fetchone()[0]
        self.metrics['coverage']['github'] = {
            'count': with_github,
            'percentage': round((with_github / total_people) * 100, 2)
        }
        
        # Employment coverage
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) FROM employment
        """)
        with_employment = cursor.fetchone()[0]
        self.metrics['coverage']['employment'] = {
            'count': with_employment,
            'percentage': round((with_employment / total_people) * 100, 2)
        }
        
        # Education coverage
        cursor.execute("""
            SELECT COUNT(DISTINCT person_id) FROM education
        """)
        with_education = cursor.fetchone()[0]
        self.metrics['coverage']['education'] = {
            'count': with_education,
            'percentage': round((with_education / total_people) * 100, 2)
        }
        
        # Location coverage
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE location IS NOT NULL AND location != ''
        """)
        with_location = cursor.fetchone()[0]
        self.metrics['coverage']['location'] = {
            'count': with_location,
            'percentage': round((with_location / total_people) * 100, 2)
        }
        
        # Headline coverage
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE headline IS NOT NULL AND headline != ''
        """)
        with_headline = cursor.fetchone()[0]
        self.metrics['coverage']['headline'] = {
            'count': with_headline,
            'percentage': round((with_headline / total_people) * 100, 2)
        }
        
        print(f"   LinkedIn: {self.metrics['coverage']['linkedin']['percentage']}%")
        print(f"   Email: {self.metrics['coverage']['email']['percentage']}%")
        print(f"   GitHub: {self.metrics['coverage']['github']['percentage']}%")
        print(f"   Employment: {self.metrics['coverage']['employment']['percentage']}%")
    
    def generate_quality_distribution(self):
        """Generate quality score distribution"""
        print("\n📊 Generating quality distribution...")
        
        cursor = self.conn.cursor()
        
        # Calculate completeness scores on the fly
        # This is a simplified version - in production you'd store these
        cursor.execute("""
            SELECT 
                person_id,
                (CASE WHEN full_name IS NOT NULL AND full_name != '' THEN 1 ELSE 0 END +
                 CASE WHEN normalized_linkedin_url IS NOT NULL AND normalized_linkedin_url != '' THEN 1 ELSE 0 END +
                 CASE WHEN location IS NOT NULL AND location != '' THEN 1 ELSE 0 END +
                 CASE WHEN headline IS NOT NULL AND headline != '' THEN 1 ELSE 0 END) * 0.25 as completeness
            FROM person
        """)
        
        scores = [row[1] for row in cursor.fetchall()]
        
        # Bucket into ranges
        buckets = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }
        
        for score in scores:
            if score < 0.2:
                buckets['0.0-0.2'] += 1
            elif score < 0.4:
                buckets['0.2-0.4'] += 1
            elif score < 0.6:
                buckets['0.4-0.6'] += 1
            elif score < 0.8:
                buckets['0.6-0.8'] += 1
            else:
                buckets['0.8-1.0'] += 1
        
        self.metrics['quality_distribution'] = buckets
        self.metrics['quality_distribution']['average'] = round(sum(scores) / len(scores), 3) if scores else 0
        
        print(f"   Average completeness: {self.metrics['quality_distribution']['average']}")
    
    def generate_freshness_metrics(self):
        """Generate data freshness metrics"""
        print("\n📊 Generating freshness metrics...")
        
        cursor = self.conn.cursor()
        
        # Count records by age
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN refreshed_at > NOW() - INTERVAL '30 days' THEN 1 END) as last_30_days,
                COUNT(CASE WHEN refreshed_at > NOW() - INTERVAL '90 days' THEN 1 END) as last_90_days,
                COUNT(CASE WHEN refreshed_at > NOW() - INTERVAL '365 days' THEN 1 END) as last_year,
                COUNT(CASE WHEN refreshed_at IS NULL OR refreshed_at < NOW() - INTERVAL '365 days' THEN 1 END) as over_year
            FROM person
        """)
        
        result = cursor.fetchone()
        self.metrics['freshness'] = {
            'last_30_days': result[0],
            'last_90_days': result[1],
            'last_year': result[2],
            'over_year_old': result[3]
        }
        
        print(f"   Refreshed in last 30 days: {result[0]:,}")
        print(f"   Refreshed in last year: {result[2]:,}")
        print(f"   Over a year old: {result[3]:,}")
    
    def generate_growth_metrics(self):
        """Generate growth metrics"""
        print("\n📊 Generating growth metrics...")
        
        cursor = self.conn.cursor()
        
        # Records added in last 30/90 days (if we have created_at column)
        try:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as last_30_days,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '90 days' THEN 1 END) as last_90_days
                FROM person
                WHERE created_at IS NOT NULL
            """)
            result = cursor.fetchone()
        except Exception:
            # created_at column doesn't exist, use defaults
            self.conn.rollback()
            result = (0, 0)
        
        self.metrics['growth']['people_added'] = {
            'last_30_days': result[0] if result else 0,
            'last_90_days': result[1] if result else 0
        }
        
        # Average employment history length
        cursor.execute("""
            SELECT AVG(job_count) FROM (
                SELECT person_id, COUNT(*) as job_count
                FROM employment
                GROUP BY person_id
            ) subquery
        """)
        avg_jobs = cursor.fetchone()[0]
        self.metrics['growth']['avg_employment_records_per_person'] = round(float(avg_jobs) if avg_jobs else 0, 2)
        
        print(f"   People added (30 days): {self.metrics['growth']['people_added']['last_30_days']:,}")
        print(f"   Average jobs per person: {self.metrics['growth']['avg_employment_records_per_person']}")
    
    def save_metrics(self):
        """Save metrics to JSON file"""
        output_file = Config.REPORTS_DIR / f"quality_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert any Decimal types to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Decimal':
                return float(obj)
            return obj
        
        metrics_json = convert_decimals(self.metrics)
        
        with open(output_file, 'w') as f:
            json.dump(metrics_json, f, indent=2)
        
        print(f"\n💾 Metrics saved: {output_file}")
        
        # Also save as "latest" for easy access
        latest_file = Config.REPORTS_DIR / "quality_metrics_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(metrics_json, f, indent=2)
        
        print(f"💾 Latest metrics: {latest_file}")
    
    def print_summary(self):
        """Print metrics summary"""
        print("\n" + "="*80)
        print("METRICS SUMMARY")
        print("="*80)
        
        print(f"\n📊 Total Records:")
        print(f"   People: {self.metrics['totals']['people']:,}")
        print(f"   Companies: {self.metrics['totals']['companies']:,}")
        print(f"   Employment: {self.metrics['totals']['employment_records']:,}")
        
        print(f"\n📈 Coverage:")
        print(f"   LinkedIn: {self.metrics['coverage']['linkedin']['percentage']}%")
        print(f"   Email: {self.metrics['coverage']['email']['percentage']}%")
        print(f"   GitHub: {self.metrics['coverage']['github']['percentage']}%")
        
        print(f"\n⭐ Quality:")
        print(f"   Average completeness: {self.metrics['quality_distribution']['average']}")
        
        print(f"\n🕐 Freshness:")
        print(f"   Refreshed in last 30 days: {self.metrics['freshness']['last_30_days']:,}")
        print(f"   Over a year old: {self.metrics['freshness']['over_year_old']:,}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    """Main execution"""
    generator = QualityMetricsGenerator()
    
    try:
        generator.generate_all()
    finally:
        generator.close()
    
    print("\n✅ Metrics generation complete!")


if __name__ == "__main__":
    main()


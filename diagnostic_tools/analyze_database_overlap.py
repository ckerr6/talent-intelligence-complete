#!/usr/bin/env python3
"""
Database Overlap Analysis
Identifies duplicate and unique records across databases
"""

import json
import sqlite3
import psycopg2
from pathlib import Path
from typing import Dict, Set, List, Any
import os

class OverlapAnalyzer:
    def __init__(self):
        self.results = {
            'analysis_timestamp': '',
            'linkedin_url_analysis': {},
            'email_analysis': {},
            'people_overlap': {},
            'recommendations': []
        }
    
    def get_sqlite_linkedin_urls(self, db_path: str) -> Set[str]:
        """Get all LinkedIn URLs from SQLite database"""
        urls = set()
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if social_profiles table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='social_profiles'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT DISTINCT LOWER(TRIM(profile_url)) 
                    FROM social_profiles 
                    WHERE platform = 'linkedin' 
                    AND profile_url IS NOT NULL 
                    AND profile_url != ''
                """)
                urls = {row[0] for row in cursor.fetchall() if row[0]}
            
            conn.close()
        except Exception as e:
            print(f"Error reading SQLite {db_path}: {e}")
        
        return urls
    
    def get_sqlite_emails(self, db_path: str) -> Set[str]:
        """Get all emails from SQLite database"""
        emails = set()
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check people table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='people'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT DISTINCT LOWER(TRIM(primary_email)) 
                    FROM people 
                    WHERE primary_email IS NOT NULL 
                    AND primary_email != ''
                """)
                emails.update({row[0] for row in cursor.fetchall() if row[0]})
            
            # Check emails table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT DISTINCT LOWER(TRIM(email)) 
                    FROM emails 
                    WHERE email IS NOT NULL 
                    AND email != ''
                """)
                emails.update({row[0] for row in cursor.fetchall() if row[0]})
            
            conn.close()
        except Exception as e:
            print(f"Error reading SQLite {db_path}: {e}")
        
        return emails
    
    def get_postgres_linkedin_urls(self, db_name: str) -> Set[str]:
        """Get all LinkedIn URLs from PostgreSQL database"""
        urls = set()
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=os.environ.get('PGUSER', os.environ.get('USER')),
                host=os.environ.get('PGHOST', 'localhost'),
                port=os.environ.get('PGPORT', '5432')
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if person or people table exists
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('person', 'people')
            """)
            table_result = cursor.fetchone()
            
            if table_result:
                table_name = table_result[0]
                # Check for linkedin_url column
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                    AND column_name LIKE '%linkedin%'
                """)
                linkedin_col = cursor.fetchone()
                
                if linkedin_col:
                    cursor.execute(f"""
                        SELECT DISTINCT LOWER(TRIM({linkedin_col[0]})) 
                        FROM {table_name}
                        WHERE {linkedin_col[0]} IS NOT NULL 
                        AND {linkedin_col[0]} != ''
                    """)
                    urls = {row[0] for row in cursor.fetchall() if row[0]}
            
            conn.close()
        except Exception as e:
            print(f"Error reading PostgreSQL {db_name}: {e}")
        
        return urls
    
    def get_postgres_emails(self, db_name: str) -> Set[str]:
        """Get all emails from PostgreSQL database"""
        emails = set()
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=os.environ.get('PGUSER', os.environ.get('USER')),
                host=os.environ.get('PGHOST', 'localhost'),
                port=os.environ.get('PGPORT', '5432')
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if person or people table exists
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('person', 'people')
            """)
            table_result = cursor.fetchone()
            
            if table_result:
                table_name = table_result[0]
                # Check for email columns
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                    AND column_name LIKE '%email%'
                """)
                email_cols = cursor.fetchall()
                
                for col in email_cols:
                    cursor.execute(f"""
                        SELECT DISTINCT LOWER(TRIM({col[0]})) 
                        FROM {table_name}
                        WHERE {col[0]} IS NOT NULL 
                        AND {col[0]} != ''
                    """)
                    emails.update({row[0] for row in cursor.fetchall() if row[0]})
            
            conn.close()
        except Exception as e:
            print(f"Error reading PostgreSQL {db_name}: {e}")
        
        return emails
    
    def analyze_overlap(self):
        """Perform comprehensive overlap analysis"""
        print("=" * 80)
        print("DATABASE OVERLAP ANALYSIS")
        print("=" * 80)
        
        # Define databases to analyze
        sqlite_db = "/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/talent_intelligence.db"
        pg_databases = ['talent', 'talent_intelligence', 'talent_intel']
        
        # Collect LinkedIn URLs
        print("\n🔍 Collecting LinkedIn URLs...")
        linkedin_data = {}
        
        print(f"  - SQLite: talent_intelligence.db")
        linkedin_data['sqlite'] = self.get_sqlite_linkedin_urls(sqlite_db)
        print(f"    Found: {len(linkedin_data['sqlite']):,} LinkedIn URLs")
        
        for db_name in pg_databases:
            print(f"  - PostgreSQL: {db_name}")
            linkedin_data[db_name] = self.get_postgres_linkedin_urls(db_name)
            print(f"    Found: {len(linkedin_data[db_name]):,} LinkedIn URLs")
        
        # Collect Emails
        print("\n🔍 Collecting Emails...")
        email_data = {}
        
        print(f"  - SQLite: talent_intelligence.db")
        email_data['sqlite'] = self.get_sqlite_emails(sqlite_db)
        print(f"    Found: {len(email_data['sqlite']):,} emails")
        
        for db_name in pg_databases:
            print(f"  - PostgreSQL: {db_name}")
            email_data[db_name] = self.get_postgres_emails(db_name)
            print(f"    Found: {len(email_data[db_name]):,} emails")
        
        # Analyze LinkedIn URL overlap
        print("\n📊 Analyzing LinkedIn URL Overlap...")
        self.analyze_set_overlap('LinkedIn URLs', linkedin_data)
        
        # Analyze Email overlap
        print("\n📊 Analyzing Email Overlap...")
        self.analyze_set_overlap('Emails', email_data)
        
        # Generate recommendations
        self.generate_recommendations(linkedin_data, email_data)
        
        # Save results
        output_file = Path("audit_results/overlap_analysis.json")
        with open(output_file, 'w') as f:
            json.dump({
                'linkedin_overlap': self.format_set_analysis(linkedin_data),
                'email_overlap': self.format_set_analysis(email_data),
                'recommendations': self.results['recommendations']
            }, f, indent=2)
        
        print(f"\n✅ Analysis saved to: {output_file}")
        
    def analyze_set_overlap(self, data_type: str, data_dict: Dict[str, Set[str]]):
        """Analyze overlap between sets of data"""
        print(f"\n{data_type} Overlap Matrix:")
        print("-" * 80)
        
        databases = list(data_dict.keys())
        
        # Compare each pair
        for i, db1 in enumerate(databases):
            for db2 in databases[i+1:]:
                set1 = data_dict[db1]
                set2 = data_dict[db2]
                
                intersection = set1 & set2
                only_in_1 = set1 - set2
                only_in_2 = set2 - set1
                
                overlap_pct_1 = (len(intersection) / len(set1) * 100) if set1 else 0
                overlap_pct_2 = (len(intersection) / len(set2) * 100) if set2 else 0
                
                print(f"\n{db1} vs {db2}:")
                print(f"  In both:         {len(intersection):>8,} records")
                print(f"  Only in {db1:20}: {len(only_in_1):>8,} records ({overlap_pct_1:.1f}% overlap)")
                print(f"  Only in {db2:20}: {len(only_in_2):>8,} records ({overlap_pct_2:.1f}% overlap)")
    
    def format_set_analysis(self, data_dict: Dict[str, Set[str]]) -> Dict:
        """Format set analysis for JSON output"""
        result = {}
        databases = list(data_dict.keys())
        
        for i, db1 in enumerate(databases):
            for db2 in databases[i+1:]:
                set1 = data_dict[db1]
                set2 = data_dict[db2]
                
                intersection = set1 & set2
                only_in_1 = set1 - set2
                only_in_2 = set2 - set1
                
                key = f"{db1}_vs_{db2}"
                result[key] = {
                    'in_both': len(intersection),
                    f'only_in_{db1}': len(only_in_1),
                    f'only_in_{db2}': len(only_in_2),
                    'total_unique': len(set1 | set2)
                }
        
        return result
    
    def generate_recommendations(self, linkedin_data: Dict, email_data: Dict):
        """Generate recommendations based on overlap analysis"""
        recommendations = []
        
        # Check SQLite vs PostgreSQL talent
        sqlite_linkedin = linkedin_data.get('sqlite', set())
        talent_linkedin = linkedin_data.get('talent', set())
        
        if sqlite_linkedin and talent_linkedin:
            only_in_sqlite = sqlite_linkedin - talent_linkedin
            only_in_talent = talent_linkedin - sqlite_linkedin
            
            if only_in_sqlite:
                recommendations.append({
                    'priority': 'HIGH',
                    'action': 'MIGRATE',
                    'source': 'SQLite talent_intelligence.db',
                    'target': 'PostgreSQL talent',
                    'records': len(only_in_sqlite),
                    'reason': f'{len(only_in_sqlite):,} LinkedIn profiles exist in SQLite but not in PostgreSQL talent'
                })
            
            if only_in_talent:
                recommendations.append({
                    'priority': 'INFO',
                    'action': 'VERIFY',
                    'description': f'PostgreSQL talent has {len(only_in_talent):,} additional LinkedIn profiles not in SQLite',
                    'reason': 'These might be from GitHub enrichment or other sources'
                })
        
        # Check talent_intelligence vs talent
        ti_linkedin = linkedin_data.get('talent_intelligence', set())
        ti_emails = email_data.get('talent_intelligence', set())
        
        if ti_linkedin and talent_linkedin:
            ti_unique = ti_linkedin - talent_linkedin
            if len(ti_unique) < 100:  # If very few unique records
                recommendations.append({
                    'priority': 'LOW',
                    'action': 'ARCHIVE',
                    'database': 'PostgreSQL talent_intelligence',
                    'reason': f'Only {len(ti_unique)} unique LinkedIn profiles compared to talent database',
                    'suggestion': 'Consider archiving after verifying these records are in talent'
                })
        
        # Check talent_intel
        talent_intel_linkedin = linkedin_data.get('talent_intel', set())
        if talent_intel_linkedin and talent_linkedin:
            intel_unique = talent_intel_linkedin - talent_linkedin
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'EVALUATE',
                'database': 'PostgreSQL talent_intel',
                'unique_records': len(intel_unique),
                'reason': f'Has {len(intel_unique):,} LinkedIn profiles not in talent database',
                'suggestion': 'Review and migrate unique records to talent if valuable'
            })
        
        self.results['recommendations'] = recommendations
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority']}] {rec['action']}")
            for key, value in rec.items():
                if key not in ['priority', 'action']:
                    print(f"   {key}: {value}")


if __name__ == "__main__":
    analyzer = OverlapAnalyzer()
    analyzer.analyze_overlap()


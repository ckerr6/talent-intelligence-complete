#!/usr/bin/env python3
"""
Complete Database Audit Script
Audits all 12 databases (3 SQLite + 9 PostgreSQL) to create comprehensive inventory
"""

import json
import sqlite3
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class DatabaseAuditor:
    def __init__(self):
        self.results = {
            'audit_timestamp': datetime.now().isoformat(),
            'sqlite_databases': [],
            'postgresql_databases': [],
            'summary': {}
        }
        
    def audit_sqlite_database(self, db_path: Path) -> Dict[str, Any]:
        """Audit a single SQLite database"""
        print(f"\n📊 Auditing SQLite: {db_path.name}")
        
        if not db_path.exists():
            return {
                'name': db_path.name,
                'path': str(db_path),
                'status': 'NOT_FOUND',
                'error': 'File does not exist'
            }
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get file stats
            stat = db_path.stat()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get counts for each table
            table_counts = {}
            table_schemas = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                    
                    # Get schema
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    table_schemas[table] = [
                        {'name': col[1], 'type': col[2], 'notnull': col[3], 'pk': col[5]}
                        for col in columns
                    ]
                except Exception as e:
                    table_counts[table] = f"ERROR: {str(e)}"
                    table_schemas[table] = []
            
            # Get specific table stats if they exist
            people_stats = None
            if 'people' in tables:
                people_stats = self._get_sqlite_people_stats(cursor)
            
            companies_stats = None
            if 'companies' in tables:
                companies_stats = self._get_sqlite_companies_stats(cursor)
            
            github_stats = None
            if 'github_profiles' in tables:
                github_stats = self._get_sqlite_github_stats(cursor)
            
            conn.close()
            
            return {
                'name': db_path.name,
                'path': str(db_path),
                'status': 'ACTIVE',
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'tables': tables,
                'table_counts': table_counts,
                'table_schemas': table_schemas,
                'people_stats': people_stats,
                'companies_stats': companies_stats,
                'github_stats': github_stats
            }
            
        except Exception as e:
            return {
                'name': db_path.name,
                'path': str(db_path),
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _get_sqlite_people_stats(self, cursor) -> Dict[str, Any]:
        """Get detailed stats for people table in SQLite"""
        stats = {}
        
        try:
            # Total count
            cursor.execute("SELECT COUNT(*) FROM people")
            stats['total_count'] = cursor.fetchone()[0]
            
            # Email coverage
            cursor.execute("SELECT COUNT(*) FROM people WHERE primary_email IS NOT NULL AND primary_email != ''")
            stats['with_email'] = cursor.fetchone()[0]
            
            # LinkedIn coverage (check social_profiles table if exists)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='social_profiles'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT COUNT(DISTINCT person_id) 
                    FROM social_profiles 
                    WHERE platform = 'linkedin' AND profile_url IS NOT NULL
                """)
                stats['with_linkedin'] = cursor.fetchone()[0]
            else:
                stats['with_linkedin'] = 0
            
            # Quality score average
            cursor.execute("SELECT AVG(data_quality_score) FROM people WHERE data_quality_score IS NOT NULL")
            avg_score = cursor.fetchone()[0]
            stats['avg_quality_score'] = round(avg_score, 3) if avg_score else None
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _get_sqlite_companies_stats(self, cursor) -> Dict[str, Any]:
        """Get detailed stats for companies table in SQLite"""
        stats = {}
        
        try:
            cursor.execute("SELECT COUNT(*) FROM companies")
            stats['total_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM companies WHERE website IS NOT NULL AND website != ''")
            stats['with_website'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM companies WHERE github_org IS NOT NULL AND github_org != ''")
            stats['with_github_org'] = cursor.fetchone()[0]
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _get_sqlite_github_stats(self, cursor) -> Dict[str, Any]:
        """Get detailed stats for GitHub profiles in SQLite"""
        stats = {}
        
        try:
            cursor.execute("SELECT COUNT(*) FROM github_profiles")
            stats['total_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE person_id IS NOT NULL")
            stats['linked_to_people'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE github_email IS NOT NULL AND github_email != ''")
            stats['with_email'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE followers > 0")
            stats['with_followers'] = cursor.fetchone()[0]
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def audit_postgresql_database(self, db_name: str) -> Dict[str, Any]:
        """Audit a single PostgreSQL database"""
        print(f"\n📊 Auditing PostgreSQL: {db_name}")
        
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=os.environ.get('PGUSER', os.environ.get('USER')),
                host=os.environ.get('PGHOST', 'localhost'),
                port=os.environ.get('PGPORT', '5432')
            )
            conn.autocommit = True  # Prevent transaction errors
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute(f"""
                SELECT pg_size_pretty(pg_database_size('{db_name}'))
            """)
            db_size = cursor.fetchone()[0]
            
            # Get database owner and creation date
            cursor.execute(f"""
                SELECT datdba::regrole, 
                       (SELECT oid FROM pg_database WHERE datname = '{db_name}')
                FROM pg_database WHERE datname = '{db_name}'
            """)
            owner_info = cursor.fetchone()
            
            # Get all tables in public schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get counts and schemas for each table
            table_counts = {}
            table_schemas = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                    
                    # Get schema
                    cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = '{table}'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    table_schemas[table] = [
                        {'name': col[0], 'type': col[1], 'nullable': col[2]}
                        for col in columns
                    ]
                except Exception as e:
                    table_counts[table] = f"ERROR: {str(e)}"
                    table_schemas[table] = []
            
            # Get specific table stats
            people_stats = None
            if 'people' in tables:
                people_stats = self._get_pg_people_stats(cursor, 'people')
            elif 'person' in tables:
                people_stats = self._get_pg_people_stats(cursor, 'person')
            
            companies_stats = None
            if 'companies' in tables:
                companies_stats = self._get_pg_companies_stats(cursor)
            elif 'company' in tables:
                companies_stats = self._get_pg_companies_stats(cursor, 'company')
            
            employment_stats = None
            if 'employment' in tables:
                employment_stats = self._get_pg_employment_stats(cursor)
            
            github_stats = None
            if 'github_profiles' in tables:
                github_stats = self._get_pg_github_stats(cursor)
            
            # Check for recent activity
            cursor.execute("SELECT max(query_start) FROM pg_stat_activity WHERE datname = %s", (db_name,))
            last_activity = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'name': db_name,
                'status': 'ACTIVE',
                'size': db_size,
                'owner': str(owner_info[0]) if owner_info else 'unknown',
                'last_activity': last_activity.isoformat() if last_activity else None,
                'tables': tables,
                'table_counts': table_counts,
                'table_schemas': table_schemas,
                'people_stats': people_stats,
                'companies_stats': companies_stats,
                'employment_stats': employment_stats,
                'github_stats': github_stats
            }
            
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                return {
                    'name': db_name,
                    'status': 'NOT_FOUND',
                    'error': 'Database does not exist'
                }
            return {
                'name': db_name,
                'status': 'ERROR',
                'error': str(e)
            }
        except Exception as e:
            return {
                'name': db_name,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _get_pg_people_stats(self, cursor, table_name='people') -> Dict[str, Any]:
        """Get detailed stats for people/person table in PostgreSQL"""
        stats = {}
        
        try:
            # Check which columns exist
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # Total count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            stats['total_count'] = cursor.fetchone()[0]
            
            # Email coverage - check different possible column names
            email_col = None
            for col in ['primary_email', 'email']:
                if col in columns:
                    email_col = col
                    break
            
            if email_col:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {email_col} IS NOT NULL AND {email_col} != ''")
                stats['with_email'] = cursor.fetchone()[0]
            
            # LinkedIn coverage
            linkedin_col = None
            for col in ['linkedin_url', 'linkedin']:
                if col in columns:
                    linkedin_col = col
                    break
            
            if linkedin_col:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {linkedin_col} IS NOT NULL AND {linkedin_col} != ''")
                stats['with_linkedin'] = cursor.fetchone()[0]
            
            # Quality score if exists
            if 'data_quality_score' in columns:
                cursor.execute(f"SELECT AVG(data_quality_score) FROM {table_name} WHERE data_quality_score IS NOT NULL")
                avg_score = cursor.fetchone()[0]
                stats['avg_quality_score'] = round(float(avg_score), 3) if avg_score else None
            
            # Check for updated_at or refreshed_at timestamps
            timestamp_col = None
            for col in ['updated_at', 'refreshed_at', 'last_modified']:
                if col in columns:
                    timestamp_col = col
                    break
            
            if timestamp_col:
                cursor.execute(f"SELECT MAX({timestamp_col}) FROM {table_name}")
                last_update = cursor.fetchone()[0]
                stats['last_updated'] = last_update.isoformat() if last_update else None
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _get_pg_companies_stats(self, cursor, table_name='companies') -> Dict[str, Any]:
        """Get detailed stats for companies table in PostgreSQL"""
        stats = {}
        
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            stats['total_count'] = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE website IS NOT NULL AND website != ''")
            stats['with_website'] = cursor.fetchone()[0]
            
            # Check if github_org column exists
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = 'github_org'
            """)
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE github_org IS NOT NULL AND github_org != ''")
                stats['with_github_org'] = cursor.fetchone()[0]
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _get_pg_employment_stats(self, cursor) -> Dict[str, Any]:
        """Get employment history statistics"""
        stats = {}
        
        try:
            cursor.execute("SELECT COUNT(*) FROM employment")
            stats['total_records'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT person_id) FROM employment")
            stats['unique_people'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(record_count) FROM (SELECT person_id, COUNT(*) as record_count FROM employment GROUP BY person_id) as t")
            avg_records = cursor.fetchone()[0]
            stats['avg_records_per_person'] = round(float(avg_records), 2) if avg_records else 0
            
            # Check for is_current flag
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'employment' AND column_name = 'is_current'
            """)
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM employment WHERE is_current = true")
                stats['current_employment'] = cursor.fetchone()[0]
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _get_pg_github_stats(self, cursor) -> Dict[str, Any]:
        """Get GitHub profile statistics"""
        stats = {}
        
        try:
            cursor.execute("SELECT COUNT(*) FROM github_profiles")
            stats['total_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE person_id IS NOT NULL")
            stats['linked_to_people'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE github_email IS NOT NULL AND github_email != ''")
            stats['with_email'] = cursor.fetchone()[0]
            
            # Check if followers column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'github_profiles' AND column_name = 'followers'
            """)
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE followers > 0")
                stats['with_followers'] = cursor.fetchone()[0]
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def run_complete_audit(self):
        """Run audit on all databases"""
        print("=" * 80)
        print("COMPLETE DATABASE AUDIT")
        print("=" * 80)
        
        # Audit SQLite databases
        print("\n🔍 PHASE 1: SQLite Databases")
        print("-" * 80)
        
        sqlite_locations = [
            Path("/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/talent_intelligence.db"),
            Path("/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/talent_intelligence_backup_20251019_115502.db"),
            Path("/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db")
        ]
        
        for db_path in sqlite_locations:
            result = self.audit_sqlite_database(db_path)
            self.results['sqlite_databases'].append(result)
        
        # Audit PostgreSQL databases
        print("\n🔍 PHASE 2: PostgreSQL Databases")
        print("-" * 80)
        
        pg_databases = [
            'talent',
            'talent_intelligence',
            'talent_intel',
            'talent_graph',
            'talentgraph',
            'talentgraph2',
            'talentgraph_development',
            'tech_recruiting_db',
            'crypto_dev_network'
        ]
        
        for db_name in pg_databases:
            result = self.audit_postgresql_database(db_name)
            self.results['postgresql_databases'].append(result)
        
        # Generate summary
        self._generate_summary()
        
        # Save results
        output_file = Path("audit_results/database_inventory.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print("\n" + "=" * 80)
        print(f"✅ Audit complete! Results saved to: {output_file}")
        print("=" * 80)
        
        return self.results
    
    def _generate_summary(self):
        """Generate summary statistics"""
        summary = {
            'total_databases': 0,
            'active_databases': 0,
            'error_databases': 0,
            'not_found_databases': 0,
            'total_people_all_dbs': 0,
            'total_companies_all_dbs': 0,
            'databases_with_people': [],
            'databases_with_companies': [],
            'databases_with_github': []
        }
        
        # Summarize SQLite
        for db in self.results['sqlite_databases']:
            summary['total_databases'] += 1
            if db['status'] == 'ACTIVE':
                summary['active_databases'] += 1
                if db.get('people_stats') and db['people_stats'].get('total_count'):
                    count = db['people_stats']['total_count']
                    summary['total_people_all_dbs'] += count
                    summary['databases_with_people'].append({
                        'name': db['name'],
                        'type': 'SQLite',
                        'count': count
                    })
                if db.get('companies_stats') and db['companies_stats'].get('total_count'):
                    count = db['companies_stats']['total_count']
                    summary['total_companies_all_dbs'] += count
                    summary['databases_with_companies'].append({
                        'name': db['name'],
                        'type': 'SQLite',
                        'count': count
                    })
                if db.get('github_stats') and db['github_stats'].get('total_count'):
                    summary['databases_with_github'].append({
                        'name': db['name'],
                        'type': 'SQLite',
                        'count': db['github_stats']['total_count']
                    })
            elif db['status'] == 'ERROR':
                summary['error_databases'] += 1
            elif db['status'] == 'NOT_FOUND':
                summary['not_found_databases'] += 1
        
        # Summarize PostgreSQL
        for db in self.results['postgresql_databases']:
            summary['total_databases'] += 1
            if db['status'] == 'ACTIVE':
                summary['active_databases'] += 1
                if db.get('people_stats') and db['people_stats'].get('total_count'):
                    count = db['people_stats']['total_count']
                    summary['total_people_all_dbs'] += count
                    summary['databases_with_people'].append({
                        'name': db['name'],
                        'type': 'PostgreSQL',
                        'count': count
                    })
                if db.get('companies_stats') and db['companies_stats'].get('total_count'):
                    count = db['companies_stats']['total_count']
                    summary['total_companies_all_dbs'] += count
                    summary['databases_with_companies'].append({
                        'name': db['name'],
                        'type': 'PostgreSQL',
                        'count': count
                    })
                if db.get('github_stats') and db['github_stats'].get('total_count'):
                    summary['databases_with_github'].append({
                        'name': db['name'],
                        'type': 'PostgreSQL',
                        'count': db['github_stats']['total_count']
                    })
            elif db['status'] == 'ERROR':
                summary['error_databases'] += 1
            elif db['status'] == 'NOT_FOUND':
                summary['not_found_databases'] += 1
        
        self.results['summary'] = summary


if __name__ == "__main__":
    auditor = DatabaseAuditor()
    results = auditor.run_complete_audit()
    
    # Print summary
    print("\n📊 SUMMARY")
    print("-" * 80)
    summary = results['summary']
    print(f"Total Databases Found: {summary['active_databases']}/{summary['total_databases']}")
    print(f"Total People (sum across all DBs): {summary['total_people_all_dbs']:,}")
    print(f"Total Companies (sum across all DBs): {summary['total_companies_all_dbs']:,}")
    print(f"\nDatabases with People Data: {len(summary['databases_with_people'])}")
    for db in summary['databases_with_people']:
        print(f"  - {db['type']:12} {db['name']:30} {db['count']:>10,} people")
    print(f"\nDatabases with Company Data: {len(summary['databases_with_companies'])}")
    for db in summary['databases_with_companies']:
        print(f"  - {db['type']:12} {db['name']:30} {db['count']:>10,} companies")


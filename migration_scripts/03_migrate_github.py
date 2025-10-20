#!/usr/bin/env python3
"""
GitHub Migration Script
Migrates GitHub profiles, repositories, and contributions from SQLite to PostgreSQL
"""

import sys
import os
import sqlite3
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from migration_utils import (
    normalize_linkedin_url,
    normalize_email,
    log_migration_event,
    print_progress
)

class GitHubMigrator:
    def __init__(self, sqlite_db_path: str, pg_conn_params: dict):
        self.sqlite_path = sqlite_db_path
        self.pg_params = pg_conn_params
        self.stats = {
            'profiles_processed': 0,
            'profiles_created': 0,
            'profiles_matched': 0,
            'profiles_unmatched': 0,
            'repos_created': 0,
            'contributions_created': 0,
            'errors': 0
        }
        
    def connect_databases(self):
        """Establish connections to both databases"""
        print("📡 Connecting to databases...")
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        self.pg_conn = psycopg2.connect(**self.pg_params)
        self.pg_conn.autocommit = False
        
        print("✅ Connections established")
    
    def get_person_mapping(self) -> Dict:
        """
        Build comprehensive person mapping:
        - LinkedIn URL → PostgreSQL person_id
        - Email → PostgreSQL person_id
        """
        print("\n🔗 Building person mapping...")
        
        cursor = self.pg_conn.cursor()
        
        mapping = {
            'linkedin': {},
            'email': {}
        }
        
        # Map by LinkedIn URL
        cursor.execute("""
            SELECT 
                person_id::text,
                normalized_linkedin_url
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        
        for row in cursor.fetchall():
            mapping['linkedin'][row[1]] = row[0]
        
        # Map by email
        cursor.execute("""
            SELECT DISTINCT
                person_id::text,
                lower(email) as email
            FROM person_email
        """)
        
        for row in cursor.fetchall():
            mapping['email'][row[1]] = row[0]
        
        print(f"   LinkedIn mappings: {len(mapping['linkedin']):,}")
        print(f"   Email mappings: {len(mapping['email']):,}")
        
        return mapping
    
    def get_sqlite_person_data(self, sqlite_person_id: str) -> Dict:
        """Get person data from SQLite to help with matching"""
        cursor = self.sqlite_conn.cursor()
        
        # Get LinkedIn URL
        cursor.execute("""
            SELECT profile_url
            FROM social_profiles
            WHERE person_id = ?
            AND platform = 'linkedin'
            LIMIT 1
        """, (sqlite_person_id,))
        
        row = cursor.fetchone()
        linkedin_url = normalize_linkedin_url(row['profile_url']) if row else None
        
        # Get email
        cursor.execute("""
            SELECT primary_email
            FROM people
            WHERE person_id = ?
        """, (sqlite_person_id,))
        
        row = cursor.fetchone()
        email = normalize_email(row['primary_email']) if row and row['primary_email'] else None
        
        return {
            'linkedin_url': linkedin_url,
            'email': email
        }
    
    def match_person_to_postgres(self, sqlite_person_id: str, person_mapping: Dict) -> Optional[str]:
        """
        Try to match SQLite person to PostgreSQL person
        Returns PostgreSQL person_id or None
        """
        if not sqlite_person_id:
            return None
        
        person_data = self.get_sqlite_person_data(sqlite_person_id)
        
        # Try LinkedIn match first (highest confidence)
        if person_data['linkedin_url']:
            pg_person_id = person_mapping['linkedin'].get(person_data['linkedin_url'])
            if pg_person_id:
                return pg_person_id
        
        # Try email match
        if person_data['email']:
            pg_person_id = person_mapping['email'].get(person_data['email'])
            if pg_person_id:
                return pg_person_id
        
        return None
    
    def github_profile_exists(self, github_username: str) -> Optional[str]:
        """Check if GitHub profile already exists, return github_profile_id if exists"""
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT github_profile_id::text
            FROM github_profile
            WHERE lower(github_username) = lower(%s)
            LIMIT 1
        """, (github_username,))
        
        row = cursor.fetchone()
        return row[0] if row else None
    
    def insert_github_profile(self, profile_data: Dict) -> str:
        """Insert GitHub profile into PostgreSQL, return github_profile_id"""
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            INSERT INTO github_profile (
                person_id,
                github_username,
                github_name,
                github_email,
                github_company,
                followers,
                following,
                public_repos,
                bio,
                blog,
                twitter_username,
                location,
                avatar_url,
                source,
                last_enriched
            ) VALUES (
                %s::uuid,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING github_profile_id::text
        """, (
            profile_data.get('person_id'),  # May be NULL if unmatched
            profile_data['github_username'],
            profile_data.get('github_name'),
            profile_data.get('github_email'),
            profile_data.get('github_company'),
            profile_data.get('followers', 0),
            profile_data.get('following', 0),
            profile_data.get('public_repos', 0),
            profile_data.get('bio'),
            profile_data.get('personal_website'),
            profile_data.get('twitter_username'),
            profile_data.get('github_location'),
            profile_data.get('avatar_url'),
            'sqlite_migration',
            profile_data.get('last_enriched')
        ))
        
        return cursor.fetchone()[0]
    
    def migrate_github_profiles(self, person_mapping: Dict):
        """Migrate all GitHub profiles"""
        print("\n👤 Migrating GitHub profiles...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            SELECT 
                github_profile_id,
                person_id,
                github_username,
                github_name,
                github_email,
                github_company,
                followers,
                following,
                public_repos,
                github_bio,
                personal_website,
                twitter_username,
                github_location,
                profile_url,
                updated_at
            FROM github_profiles
            WHERE github_username IS NOT NULL
            ORDER BY github_username
        """)
        
        profiles = cursor.fetchall()
        total = len(profiles)
        print(f"   Found {total:,} profiles to migrate")
        
        for i, profile in enumerate(profiles, 1):
            self.stats['profiles_processed'] += 1
            
            try:
                # Check if profile already exists
                existing_id = self.github_profile_exists(profile['github_username'])
                if existing_id:
                    self.stats['profiles_matched'] += 1
                    continue
                
                # Try to match to PostgreSQL person
                pg_person_id = self.match_person_to_postgres(
                    profile['person_id'],
                    person_mapping
                )
                
                if pg_person_id:
                    self.stats['profiles_matched'] += 1
                else:
                    self.stats['profiles_unmatched'] += 1
                
                # Prepare profile data
                profile_data = {
                    'person_id': pg_person_id,
                    'github_username': profile['github_username'],
                    'github_name': profile['github_name'],
                    'github_email': profile['github_email'],
                    'github_company': profile['github_company'],
                    'followers': profile['followers'] or 0,
                    'following': profile['following'] or 0,
                    'public_repos': profile['public_repos'] or 0,
                    'bio': profile['github_bio'],
                    'personal_website': profile['personal_website'],
                    'twitter_username': profile['twitter_username'],
                    'github_location': profile['github_location'],
                    'avatar_url': profile['profile_url'],
                    'last_enriched': profile['updated_at']
                }
                
                # Insert profile
                self.insert_github_profile(profile_data)
                self.stats['profiles_created'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"\n   ⚠️  Error migrating profile {profile['github_username']}: {e}")
            
            # Progress and commit
            if i % 100 == 0:
                print_progress(i, total, 'Profiles')
                self.pg_conn.commit()
        
        self.pg_conn.commit()
        print_progress(total, total, 'Profiles')
    
    def get_company_id_by_name(self, company_name: str) -> Optional[str]:
        """Try to find company_id by name"""
        if not company_name:
            return None
        
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT company_id::text
            FROM company
            WHERE lower(company_name) = lower(%s)
            LIMIT 1
        """, (company_name,))
        
        row = cursor.fetchone()
        return row[0] if row else None
    
    def migrate_repositories(self):
        """Migrate GitHub repositories"""
        print("\n📦 Migrating GitHub repositories...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            SELECT 
                repo_id,
                company_id,
                repo_name,
                full_name,
                language,
                stars,
                forks,
                description,
                homepage,
                created_at,
                updated_at,
                pushed_at,
                is_archived
            FROM company_repositories
            WHERE full_name IS NOT NULL
            ORDER BY full_name
        """)
        
        repos = cursor.fetchall()
        total = len(repos)
        print(f"   Found {total:,} repositories to migrate")
        
        # Get company name mapping from SQLite
        cursor.execute("""
            SELECT company_id, name
            FROM companies
        """)
        sqlite_company_names = {row['company_id']: row['name'] for row in cursor.fetchall()}
        
        for i, repo in enumerate(repos, 1):
            try:
                # Try to match company
                sqlite_company_id = repo['company_id']
                pg_company_id = None
                
                if sqlite_company_id and sqlite_company_id in sqlite_company_names:
                    company_name = sqlite_company_names[sqlite_company_id]
                    pg_company_id = self.get_company_id_by_name(company_name)
                
                # Extract owner from full_name
                full_name = repo['full_name']
                owner = full_name.split('/')[0] if '/' in full_name else None
                
                # Insert repository
                pg_cursor = self.pg_conn.cursor()
                pg_cursor.execute("""
                    INSERT INTO github_repository (
                        company_id,
                        repo_name,
                        full_name,
                        owner_username,
                        language,
                        stars,
                        forks,
                        description,
                        homepage_url,
                        is_fork,
                        created_at_github,
                        updated_at_github,
                        last_pushed_at
                    ) VALUES (
                        %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (full_name) DO NOTHING
                """, (
                    pg_company_id,
                    repo['repo_name'],
                    full_name,
                    owner,
                    repo['language'],
                    repo['stars'] or 0,
                    repo['forks'] or 0,
                    repo['description'],
                    repo['homepage'],
                    bool(repo['is_archived']),  # Map is_archived to is_fork (closest match)
                    repo['created_at'],
                    repo['updated_at'],
                    repo['pushed_at']
                ))
                
                if pg_cursor.rowcount > 0:
                    self.stats['repos_created'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"\n   ⚠️  Error migrating repo {repo['full_name']}: {e}")
            
            # Progress and commit
            if i % 100 == 0:
                print_progress(i, total, 'Repositories')
                self.pg_conn.commit()
        
        self.pg_conn.commit()
        print_progress(total, total, 'Repositories')
    
    def migrate_contributions(self):
        """Migrate GitHub contributions (links profiles to repos)"""
        print("\n🔗 Migrating GitHub contributions...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            SELECT 
                github_profile_id,
                repo_id,
                contribution_count
            FROM github_repo_contributions
        """)
        
        contributions = cursor.fetchall()
        total = len(contributions)
        print(f"   Found {total:,} contributions to migrate")
        
        # Build mapping of SQLite IDs to PostgreSQL IDs
        # Get GitHub profile mapping
        cursor.execute("SELECT github_profile_id, github_username FROM github_profiles")
        sqlite_profiles = {row['github_profile_id']: row['github_username'] for row in cursor.fetchall()}
        
        # Get repo mapping
        cursor.execute("SELECT repo_id, full_name FROM company_repositories")
        sqlite_repos = {row['repo_id']: row['full_name'] for row in cursor.fetchall()}
        
        # Get PostgreSQL mappings
        pg_cursor = self.pg_conn.cursor()
        
        pg_cursor.execute("SELECT github_profile_id::text, github_username FROM github_profile")
        pg_profiles = {row[1].lower(): row[0] for row in pg_cursor.fetchall()}
        
        pg_cursor.execute("SELECT repo_id::text, full_name FROM github_repository")
        pg_repos = {row[1].lower(): row[0] for row in pg_cursor.fetchall()}
        
        for i, contrib in enumerate(contributions, 1):
            try:
                # Map SQLite IDs to PostgreSQL IDs
                sqlite_profile_id = contrib['github_profile_id']
                sqlite_repo_id = contrib['repo_id']
                
                github_username = sqlite_profiles.get(sqlite_profile_id)
                repo_full_name = sqlite_repos.get(sqlite_repo_id)
                
                if not github_username or not repo_full_name:
                    continue
                
                pg_profile_id = pg_profiles.get(github_username.lower())
                pg_repo_id = pg_repos.get(repo_full_name.lower())
                
                if not pg_profile_id or not pg_repo_id:
                    continue
                
                # Insert contribution
                pg_cursor.execute("""
                    INSERT INTO github_contribution (
                        github_profile_id,
                        repo_id,
                        contribution_count
                    ) VALUES (
                        %s::uuid, %s::uuid, %s
                    )
                    ON CONFLICT (github_profile_id, repo_id) DO NOTHING
                """, (pg_profile_id, pg_repo_id, contrib['contribution_count'] or 0))
                
                if pg_cursor.rowcount > 0:
                    self.stats['contributions_created'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
            
            # Progress and commit
            if i % 500 == 0:
                print_progress(i, total, 'Contributions')
                self.pg_conn.commit()
        
        self.pg_conn.commit()
        print_progress(total, total, 'Contributions')
    
    def migrate_github_data(self):
        """Main migration process"""
        print("\n" + "=" * 80)
        print("GITHUB MIGRATION: SQLite → PostgreSQL talent")
        print("=" * 80)
        
        self.connect_databases()
        
        log_migration_event(
            self.pg_conn,
            'github_migration',
            'github',
            'started',
            metadata={'source': self.sqlite_path}
        )
        
        try:
            # Build person mapping
            person_mapping = self.get_person_mapping()
            
            # Migrate profiles
            self.migrate_github_profiles(person_mapping)
            
            # Migrate repositories
            self.migrate_repositories()
            
            # Migrate contributions
            self.migrate_contributions()
            
            # Log success
            log_migration_event(
                self.pg_conn,
                'github_migration',
                'github',
                'completed',
                records_processed=self.stats['profiles_processed'],
                records_created=self.stats['profiles_created'] + self.stats['repos_created'],
                metadata=self.stats
            )
            
            self.print_summary()
            
        except Exception as e:
            self.pg_conn.rollback()
            print(f"\n❌ Error during migration: {e}")
            
            log_migration_event(
                self.pg_conn,
                'github_migration',
                'github',
                'failed',
                error_message=str(e),
                metadata=self.stats
            )
            
            raise
        
        finally:
            self.sqlite_conn.close()
            self.pg_conn.close()
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"GitHub Profiles:")
        print(f"  Processed:               {self.stats['profiles_processed']:,}")
        print(f"  Created:                 {self.stats['profiles_created']:,}")
        print(f"  Matched to people:       {self.stats['profiles_matched']:,}")
        print(f"  Unmatched:               {self.stats['profiles_unmatched']:,}")
        print(f"\nRepositories:")
        print(f"  Created:                 {self.stats['repos_created']:,}")
        print(f"\nContributions:")
        print(f"  Created:                 {self.stats['contributions_created']:,}")
        print(f"\nErrors:                    {self.stats['errors']:,}")
        print("=" * 80)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate GitHub data from SQLite to PostgreSQL')
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
    
    migrator = GitHubMigrator(args.sqlite_db, pg_params)
    migrator.migrate_github_data()
    
    print("\n✅ GitHub migration complete!")


if __name__ == '__main__':
    main()


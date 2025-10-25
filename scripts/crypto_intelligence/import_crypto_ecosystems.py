#!/usr/bin/env python3
"""
ABOUTME: Import crypto ecosystems from Electric Capital's taxonomy
ABOUTME: Priority enrichment for Ethereum and other blockchain developers
"""

import sys
import os
sys.path.insert(0, '/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete')

from config import get_db_context
import json
import requests
from typing import List, Dict
import time

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

def create_crypto_tables():
    """Create tables for crypto ecosystem tracking"""
    print("🔧 Creating crypto ecosystem tables...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Crypto ecosystems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_ecosystems (
                ecosystem_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                ecosystem_name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Crypto repos table (links repos to ecosystems)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_ecosystem_repos (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                ecosystem_id UUID REFERENCES crypto_ecosystems(ecosystem_id),
                repo_owner TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                repo_url TEXT NOT NULL,
                branch JSONB,  -- Sub-ecosystem branches
                tags JSONB,    -- Electric Capital tags
                stars INTEGER,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(repo_owner, repo_name, ecosystem_id)
            )
        """)
        
        # Crypto developer profiles (links developers to ecosystems)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_developers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                github_profile_id UUID REFERENCES github_profile(github_profile_id),
                ecosystem_id UUID REFERENCES crypto_ecosystems(ecosystem_id),
                contribution_count INTEGER DEFAULT 0,
                first_contribution TIMESTAMP,
                last_contribution TIMESTAMP,
                is_core_contributor BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(github_profile_id, ecosystem_id)
            )
        """)
        
        conn.commit()
        print("✅ Crypto ecosystem tables created")

def import_ecosystem_data(ecosystem_name: str, jsonl_file: str):
    """Import ecosystem data from Electric Capital export"""
    print(f"\n📥 Importing {ecosystem_name} ecosystem...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Create or get ecosystem
        cursor.execute("""
            INSERT INTO crypto_ecosystems (ecosystem_name)
            VALUES (%s)
            ON CONFLICT (ecosystem_name) DO UPDATE SET ecosystem_name = EXCLUDED.ecosystem_name
            RETURNING ecosystem_id
        """, (ecosystem_name,))
        result = cursor.fetchone()
        ecosystem_id = result[0] if isinstance(result, tuple) else result['ecosystem_id']
        
        # Read and import repos
        imported = 0
        skipped = 0
        
        with open(jsonl_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                repo_url = data['repo_url']
                
                # Parse GitHub URL
                if 'github.com/' not in repo_url:
                    skipped += 1
                    continue
                
                parts = repo_url.replace('https://github.com/', '').split('/')
                if len(parts) < 2:
                    skipped += 1
                    continue
                
                repo_owner = parts[0]
                repo_name = parts[1]
                
                # Insert repo
                try:
                    cursor.execute("""
                        INSERT INTO crypto_ecosystem_repos 
                        (ecosystem_id, repo_owner, repo_name, repo_url, branch, tags)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (repo_owner, repo_name, ecosystem_id) DO NOTHING
                    """, (
                        ecosystem_id,
                        repo_owner,
                        repo_name,
                        repo_url,
                        json.dumps(data.get('branch', [])),
                        json.dumps(data.get('tags', []))
                    ))
                    imported += 1
                    
                    if imported % 1000 == 0:
                        print(f"   📦 Imported {imported} repos...")
                        conn.commit()
                        
                except Exception as e:
                    skipped += 1
                    if skipped % 1000 == 0:
                        print(f"   ⚠️  Skipped {skipped} repos")
        
        conn.commit()
        print(f"✅ Imported {imported} repos, skipped {skipped}")
        return ecosystem_id

def discover_contributors(ecosystem_id: str, limit: int = 100):
    """
    Discover top contributors from ecosystem repos.
    Prioritizes core/popular repos.
    """
    print(f"\n🔍 Discovering contributors...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get top repos by tags (core protocol repos)
        cursor.execute("""
            SELECT repo_owner, repo_name, repo_url, tags
            FROM crypto_ecosystem_repos
            WHERE ecosystem_id = %s
            AND (
                tags::text LIKE '%%protocol%%' 
                OR tags::text LIKE '%%core%%'
                OR tags::text LIKE '%%client%%'
            )
            LIMIT %s
        """, (str(ecosystem_id), limit))
        
        repos = cursor.fetchall()
        
        print(f"   Found {len(repos)} priority repos to scan")
        
        all_contributors = {}
        
        for repo in repos[:20]:  # Start with top 20 repos
            if isinstance(repo, tuple):
                owner, name, url, tags = repo
            else:
                owner = repo['repo_owner']
                name = repo['repo_name']
                url = repo['repo_url']
                tags = repo['tags']
            
            print(f"   📊 Scanning {owner}/{name}...")
            
            # Fetch contributors from GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{name}/contributors"
            
            try:
                response = requests.get(api_url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    contributors = response.json()
                    
                    for contributor in contributors[:50]:  # Top 50 per repo
                        username = contributor.get('login')
                        contributions = contributor.get('contributions', 0)
                        
                        if username not in all_contributors:
                            all_contributors[username] = {
                                'repos': [],
                                'total_contributions': 0
                            }
                        
                        all_contributors[username]['repos'].append({
                            'repo': f"{owner}/{name}",
                            'contributions': contributions
                        })
                        all_contributors[username]['total_contributions'] += contributions
                    
                    print(f"      ✅ Found {len(contributors)} contributors")
                else:
                    print(f"      ⚠️  Failed: {response.status_code}")
                
                # Rate limiting
                time.sleep(0.75)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        # Sort by total contributions
        sorted_contributors = sorted(
            all_contributors.items(),
            key=lambda x: x[1]['total_contributions'],
            reverse=True
        )
        
        print(f"\n✅ Discovered {len(sorted_contributors)} unique contributors")
        print(f"\n🏆 Top 10 Contributors:")
        for i, (username, data) in enumerate(sorted_contributors[:10], 1):
            repos_count = len(data['repos'])
            total_contribs = data['total_contributions']
            print(f"   {i}. @{username} - {total_contribs} contributions across {repos_count} repos")
        
        return sorted_contributors

def queue_for_enrichment(contributors: List, ecosystem_id: str):
    """Add discovered contributors to enrichment queue"""
    print(f"\n📋 Queuing contributors for enrichment...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        queued = 0
        existing = 0
        
        for username, data in contributors:
            # Check if profile exists
            cursor.execute("""
                SELECT github_profile_id 
                FROM github_profile 
                WHERE github_username = %s
            """, (username,))
            
            profile = cursor.fetchone()
            
            if profile:
                profile_id = profile[0] if isinstance(profile, tuple) else profile['github_profile_id']
                
                # Link to crypto ecosystem
                cursor.execute("""
                    INSERT INTO crypto_developers 
                    (github_profile_id, ecosystem_id, contribution_count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (github_profile_id, ecosystem_id) 
                    DO UPDATE SET contribution_count = EXCLUDED.contribution_count
                """, (profile_id, ecosystem_id, data['total_contributions']))
                
                existing += 1
            else:
                # Create new profile for enrichment
                cursor.execute("""
                    INSERT INTO github_profile (github_username)
                    VALUES (%s)
                    ON CONFLICT (github_username) DO NOTHING
                    RETURNING github_profile_id
                """, (username,))
                
                result = cursor.fetchone()
                if result:
                    profile_id = result[0] if isinstance(result, tuple) else result['github_profile_id']
                    
                    # Link to crypto ecosystem
                    cursor.execute("""
                        INSERT INTO crypto_developers 
                        (github_profile_id, ecosystem_id, contribution_count, is_core_contributor)
                        VALUES (%s, %s, %s, TRUE)
                    """, (profile_id, ecosystem_id, data['total_contributions']))
                    
                    queued += 1
        
        conn.commit()
        print(f"✅ Queued {queued} new profiles, linked {existing} existing profiles")

def main(ecosystem_name: str = "Ethereum", limit: int = 100):
    """Main import pipeline"""
    print("="*80)
    print(f"🚀 CRYPTO ECOSYSTEM IMPORTER - {ecosystem_name}")
    print("="*80)
    
    # Check if export exists
    export_file = f"/tmp/{ecosystem_name.lower()}_ecosystem.jsonl"
    
    if not os.path.exists(export_file):
        print(f"\n❌ Export file not found: {export_file}")
        print(f"   Run: cd /tmp/crypto-ecosystems && ./run.sh export -e {ecosystem_name} {export_file}")
        return
    
    # Step 1: Create tables
    create_crypto_tables()
    
    # Step 2: Import ecosystem data
    ecosystem_id = import_ecosystem_data(ecosystem_name, export_file)
    
    # Step 3: Discover contributors
    contributors = discover_contributors(ecosystem_id, limit)
    
    # Step 4: Queue for enrichment
    queue_for_enrichment(contributors[:100], ecosystem_id)  # Queue top 100
    
    print("\n" + "="*80)
    print("🎉 Import complete!")
    print(f"   Next: Run enrichment on crypto developers")
    print("="*80)

if __name__ == "__main__":
    ecosystem = sys.argv[1] if len(sys.argv) > 1 else "Ethereum"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    main(ecosystem, limit)


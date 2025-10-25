#!/usr/bin/env python3
"""
ABOUTME: Comprehensive Ethereum ecosystem contributor discovery
ABOUTME: Scans ALL repos from Electric Capital taxonomy and discovers ALL contributors
"""

import sys
import os
sys.path.insert(0, '/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete')

from config import get_db_context
import requests
import time
from typing import Dict, Set
import json
from scripts.crypto_intelligence.detailed_logger import DetailedLogger
from scripts.crypto_intelligence.bot_detection import is_bot, filter_bots, get_bot_stats

# Initialize detailed logger
logger = DetailedLogger('ethereum_discovery')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

def get_all_ecosystem_repos(ecosystem_name: str = "Ethereum"):
    """Get all repos for an ecosystem from database"""
    logger.info(f"📦 Loading all {ecosystem_name} repositories...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get ecosystem ID
        cursor.execute("""
            SELECT ecosystem_id 
            FROM crypto_ecosystems 
            WHERE ecosystem_name = %s
        """, (ecosystem_name,))
        
        result = cursor.fetchone()
        if not result:
            print(f"❌ Ecosystem '{ecosystem_name}' not found")
            return None, []
        
        ecosystem_id = result[0] if isinstance(result, tuple) else result['ecosystem_id']
        
        # Get all repos
        cursor.execute("""
            SELECT repo_owner, repo_name, repo_url, tags
            FROM crypto_ecosystem_repos
            WHERE ecosystem_id = %s
            ORDER BY repo_owner, repo_name
        """, (str(ecosystem_id),))
        
        repos = cursor.fetchall()
        print(f"✅ Found {len(repos)} repositories")
        
        return ecosystem_id, repos

def discover_all_contributors(ecosystem_id: str, repos: list, batch_size: int = 1000):
    """
    Discover ALL contributors from ALL repos.
    Processes in batches to handle the scale.
    """
    print(f"\n🔍 Starting comprehensive contributor discovery...")
    print(f"   Processing {len(repos)} repositories")
    print(f"   Batch size: {batch_size} repos at a time")
    
    all_contributors: Dict[str, Dict] = {}
    processed = 0
    skipped = 0
    api_calls = 0
    batch_num = 0
    
    for i in range(0, len(repos), batch_size):
        batch = repos[i:i+batch_size]
        batch_num += 1
        
        print(f"\n📊 Batch {batch_num}: Processing repos {i+1} to {min(i+batch_size, len(repos))}")
        
        for repo in batch:
            if isinstance(repo, tuple):
                owner, name, url, tags = repo
            else:
                owner = repo['repo_owner']
                name = repo['repo_name']
                url = repo['repo_url']
                tags = repo['tags']
            
            # Fetch contributors from GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{name}/contributors"
            
            try:
                response = requests.get(api_url, headers=HEADERS, timeout=10, params={'per_page': 100})
                api_calls += 1
                
                if response.status_code == 200:
                    contributors = response.json()
                    
                    # Filter out bots
                    bot_stats = get_bot_stats(contributors)
                    human_contributors = filter_bots(contributors)
                    
                    if bot_stats['bot_count'] > 0:
                        logger.debug(f"      Filtered {bot_stats['bot_count']} bots: {', '.join(bot_stats['bot_usernames'][:3])}")
                    
                    for contributor in human_contributors:
                        username = contributor.get('login')
                        contributions = contributor.get('contributions', 0)
                        
                        if username:
                            if username not in all_contributors:
                                all_contributors[username] = {
                                    'repos': [],
                                    'total_contributions': 0
                                }
                            
                            all_contributors[username]['repos'].append({
                                'repo': f"{owner}/{name}",
                                'contributions': contributions,
                                'tags': tags
                            })
                            all_contributors[username]['total_contributions'] += contributions
                    
                    processed += 1
                    
                elif response.status_code == 404:
                    skipped += 1  # Repo doesn't exist or is private
                elif response.status_code == 403:
                    # Rate limit hit
                    print(f"\n⚠️  Rate limit hit after {api_calls} API calls")
                    print(f"   Processed: {processed}, Skipped: {skipped}")
                    print(f"   Discovered: {len(all_contributors)} unique contributors so far")
                    
                    # Check rate limit status
                    rate_response = requests.get('https://api.github.com/rate_limit', headers=HEADERS)
                    if rate_response.status_code == 200:
                        rate_data = rate_response.json()
                        core_limit = rate_data['resources']['core']
                        reset_time = core_limit['reset']
                        remaining = core_limit['remaining']
                        
                        import datetime
                        reset_datetime = datetime.datetime.fromtimestamp(reset_time)
                        wait_seconds = (reset_datetime - datetime.datetime.now()).total_seconds()
                        
                        print(f"   Remaining API calls: {remaining}")
                        print(f"   Rate limit resets at: {reset_datetime}")
                        print(f"   Waiting {int(wait_seconds/60)} minutes...")
                        
                        # Save progress before waiting
                        save_progress(ecosystem_id, all_contributors, processed, skipped)
                        
                        time.sleep(wait_seconds + 10)  # Wait until reset + 10 seconds
                        continue
                    else:
                        print("   Waiting 60 minutes for rate limit reset...")
                        save_progress(ecosystem_id, all_contributors, processed, skipped)
                        time.sleep(3600)
                        continue
                else:
                    skipped += 1
                
                # Rate limiting: ~0.75s between requests = ~4800 requests/hour (under 5000 limit)
                time.sleep(0.75)
                
                # Progress update
                if processed % 100 == 0:
                    print(f"   ✅ Processed {processed} repos, {len(all_contributors)} contributors, {api_calls} API calls")
                
            except Exception as e:
                skipped += 1
                if skipped % 100 == 0:
                    print(f"   ⚠️  Skipped {skipped} repos due to errors")
        
        # Save progress after each batch
        print(f"\n💾 Saving batch {batch_num} progress...")
        save_progress(ecosystem_id, all_contributors, processed, skipped)
    
    print(f"\n✅ Discovery complete!")
    print(f"   Processed: {processed} repos")
    print(f"   Skipped: {skipped} repos")
    print(f"   API calls: {api_calls}")
    print(f"   Unique contributors: {len(all_contributors)}")
    
    return all_contributors

def save_progress(ecosystem_id: str, contributors: Dict, processed: int, skipped: int):
    """Save discovered contributors to database"""
    print(f"\n💾 Saving {len(contributors)} contributors...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        saved = 0
        existing = 0
        
        for username, data in contributors.items():
            # Check if profile exists
            cursor.execute("""
                SELECT github_profile_id 
                FROM github_profile 
                WHERE github_username = %s
            """, (username,))
            
            profile = cursor.fetchone()
            
            if profile:
                profile_id = profile[0] if isinstance(profile, tuple) else profile['github_profile_id']
                existing += 1
            else:
                # Create new profile
                cursor.execute("""
                    INSERT INTO github_profile (github_username)
                    VALUES (%s)
                    ON CONFLICT (github_username) DO NOTHING
                    RETURNING github_profile_id
                """, (username,))
                
                result = cursor.fetchone()
                if result:
                    profile_id = result[0] if isinstance(result, tuple) else result['github_profile_id']
                    saved += 1
                else:
                    continue
            
            # Link to crypto ecosystem
            cursor.execute("""
                INSERT INTO crypto_developers 
                (github_profile_id, ecosystem_id, contribution_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (github_profile_id, ecosystem_id) 
                DO UPDATE SET contribution_count = GREATEST(crypto_developers.contribution_count, EXCLUDED.contribution_count)
            """, (profile_id, str(ecosystem_id), data['total_contributions']))
        
        conn.commit()
        
    print(f"✅ Saved: {saved} new, {existing} existing")
    print(f"   Progress: {processed} processed, {skipped} skipped")
    
    # Also save to JSON file as backup
    backup_file = f'/tmp/ethereum_contributors_backup_{int(time.time())}.json'
    with open(backup_file, 'w') as f:
        json.dump({
            'contributors': contributors,
            'processed': processed,
            'skipped': skipped
        }, f)
    print(f"   Backup: {backup_file}")

def get_enrichment_queue_stats():
    """Show how many profiles are queued for enrichment"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Total crypto developers
        cursor.execute("""
            SELECT COUNT(DISTINCT github_profile_id) 
            FROM crypto_developers
        """)
        total = cursor.fetchone()[0]
        
        # Already enriched
        cursor.execute("""
            SELECT COUNT(DISTINCT cd.github_profile_id)
            FROM crypto_developers cd
            JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id
        """)
        enriched = cursor.fetchone()[0]
        
        # Pending enrichment
        pending = total - enriched
        
        print(f"\n📊 Enrichment Queue Status:")
        print(f"   Total crypto developers: {total:,}")
        print(f"   Already enriched: {enriched:,}")
        print(f"   Pending enrichment: {pending:,}")
        
        return pending

def main(ecosystem: str = "Ethereum", batch_size: int = 1000):
    """Main pipeline"""
    print("="*80)
    print(f"🌍 COMPREHENSIVE {ecosystem.upper()} CONTRIBUTOR DISCOVERY")
    print("="*80)
    print("\nThis will discover ALL contributors from ALL repos.")
    print("Expected runtime: Several hours (166K+ repos to scan)")
    print("="*80)
    
    # Step 1: Get all repos
    ecosystem_id, repos = get_all_ecosystem_repos(ecosystem)
    if not repos:
        return
    
    # Step 2: Discover all contributors
    contributors = discover_all_contributors(ecosystem_id, repos, batch_size)
    
    # Step 3: Final save
    save_progress(ecosystem_id, contributors, len(repos), 0)
    
    # Step 4: Show enrichment queue stats
    pending = get_enrichment_queue_stats()
    
    print("\n" + "="*80)
    print("🎉 DISCOVERY COMPLETE!")
    print(f"   {len(contributors):,} unique contributors discovered")
    print(f"   {pending:,} profiles queued for enrichment")
    print("\n   Next: Run continuous enrichment")
    print("   python3 scripts/crypto_intelligence/enrich_crypto_developers.py")
    print("="*80)

if __name__ == "__main__":
    ecosystem = sys.argv[1] if len(sys.argv) > 1 else "Ethereum"
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    main(ecosystem, batch_size)


#!/usr/bin/env python3
"""
ABOUTME: Continuous enrichment for crypto ecosystem developers
ABOUTME: Prioritizes developers by contribution count and enriches in parallel with discovery
"""

import sys
import os
sys.path.insert(0, '/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete')

from config import get_db_context
from scripts.github_intelligence.github_client import GitHubClient
from scripts.github_intelligence.profile_builder import ProfileBuilder
from scripts.github_intelligence.skill_extractor import SkillExtractor
from scripts.github_intelligence.seniority_scorer import SeniorityScorer
from scripts.github_intelligence.reachability_assessor import ReachabilityAssessor
from scripts.github_intelligence.activity_tracker import ActivityTracker
from scripts.github_intelligence.network_analyzer import NetworkAnalyzer
from api.services.github_intelligence.ai_profile_analyzer import AIProfileAnalyzer
import time
import json

def get_crypto_enrichment_queue(ecosystem: str = "Ethereum", limit: int = 100):
    """
    Get crypto developers to enrich, prioritized by contribution count.
    Only returns developers not yet enriched.
    """
    print(f"🔍 Finding {ecosystem} developers to enrich...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get ecosystem ID
        cursor.execute("""
            SELECT ecosystem_id 
            FROM crypto_ecosystems 
            WHERE ecosystem_name = %s
        """, (ecosystem,))
        
        result = cursor.fetchone()
        if not result:
            print(f"❌ Ecosystem '{ecosystem}' not found")
            return []
        
        ecosystem_id = result[0] if isinstance(result, tuple) else result['ecosystem_id']
        
        # Get unenriched crypto developers, ordered by contribution count
        cursor.execute("""
            SELECT 
                gp.github_username,
                cd.contribution_count,
                cd.is_core_contributor
            FROM crypto_developers cd
            JOIN github_profile gp ON cd.github_profile_id = gp.github_profile_id
            LEFT JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
            WHERE cd.ecosystem_id = %s
            AND gi.github_profile_id IS NULL
            AND gp.github_username IS NOT NULL
            ORDER BY cd.contribution_count DESC, cd.is_core_contributor DESC
            LIMIT %s
        """, (str(ecosystem_id), limit))
        
        results = cursor.fetchall()
        
        usernames = []
        for row in results:
            if isinstance(row, tuple):
                username, contrib_count, is_core = row
            else:
                username = row['github_username']
                contrib_count = row['contribution_count']
                is_core = row['is_core_contributor']
            
            usernames.append({
                'username': username,
                'contributions': contrib_count,
                'is_core': is_core
            })
        
        print(f"✅ Found {len(usernames)} {ecosystem} developers to enrich")
        if usernames:
            print(f"   Top contributor: @{usernames[0]['username']} ({usernames[0]['contributions']} contributions)")
        
        return usernames

def enrich_crypto_developer(username: str, github_client, profile_builder, skill_extractor, 
                           seniority_scorer, reachability_assessor, activity_tracker, 
                           network_analyzer, ai_analyzer, logger):
    """Enrich a single crypto developer"""
    
    logger.log_enrichment_start(username)
    
    try:
        # Fetch profile data
        profile_data = profile_builder.build_profile(username)
        if not profile_data:
            print(f"   ❌ Failed to fetch profile")
            return False
        
        # Extract intelligence
        skills = skill_extractor.extract_skills(profile_data)
        seniority = seniority_scorer.score_seniority(profile_data, skills)
        reachability = reachability_assessor.assess_reachability(profile_data)
        activity = activity_tracker.track_activity(profile_data)
        network = network_analyzer.analyze_network(profile_data)
        
        # AI analysis (optional, can be slow)
        try:
            ai_summary = ai_analyzer.generate_summary(profile_data, skills, seniority)
        except:
            ai_summary = None
        
        # Store in database
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get profile ID
            cursor.execute("""
                SELECT github_profile_id 
                FROM github_profile 
                WHERE github_username = %s
            """, (username,))
            
            result = cursor.fetchone()
            if not result:
                print(f"   ❌ Profile not found in database")
                return False
            
            profile_id = result[0] if isinstance(result, tuple) else result['github_profile_id']
            
            # Store intelligence
            cursor.execute("""
                INSERT INTO github_intelligence (
                    github_profile_id, 
                    inferred_seniority, 
                    seniority_confidence,
                    primary_languages,
                    frameworks,
                    domains,
                    influence_score, 
                    reachability_score,
                    activity_trend,
                    organizations,
                    ai_generated_summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (github_profile_id) DO NOTHING
            """, (
                profile_id,
                seniority['level'],
                seniority['confidence'],
                json.dumps(skills.get('languages', {})),
                json.dumps(skills.get('frameworks', [])),
                json.dumps(skills.get('domains', [])),
                network['influence_score'],
                reachability['score'],
                activity.get('trend', 'stable'),
                json.dumps(network.get('organizations', [])),
                ai_summary
            ))
            
            conn.commit()
        
        print(f"   ✅ Enriched: {seniority['level']} ({seniority['confidence']*100:.0f}% confidence)")
        print(f"      Influence: {network['influence_score']}, Reachability: {reachability['score']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def run_continuous_enrichment(ecosystem: str = "Ethereum", batch_size: int = 50):
    """
    Run continuous enrichment on crypto developers.
    Processes in batches, respects rate limits.
    """
    print("="*80)
    print(f"🚀 CRYPTO DEVELOPER ENRICHMENT - {ecosystem}")
    print("="*80)
    
    # Initialize components
    github_client = GitHubClient()
    profile_builder = ProfileBuilder(github_client)
    skill_extractor = SkillExtractor()
    seniority_scorer = SeniorityScorer()
    reachability_assessor = ReachabilityAssessor()
    activity_tracker = ActivityTracker()
    network_analyzer = NetworkAnalyzer()
    ai_analyzer = AIProfileAnalyzer()
    
    enriched_total = 0
    failed_total = 0
    
    while True:
        # Get next batch
        queue = get_crypto_enrichment_queue(ecosystem, batch_size)
        
        if not queue:
            print("\n✅ All discovered developers enriched!")
            print("   Waiting for more discoveries...")
            time.sleep(60)  # Wait 1 minute and check again
            continue
        
        print(f"\n📊 Processing batch of {len(queue)} developers")
        
        enriched_batch = 0
        failed_batch = 0
        
        for dev in queue:
            username = dev['username']
            contributions = dev['contributions']
            
            success = enrich_crypto_developer(
                username,
                github_client,
                profile_builder,
                skill_extractor,
                seniority_scorer,
                reachability_assessor,
                activity_tracker,
                network_analyzer,
                ai_analyzer
            )
            
            if success:
                enriched_batch += 1
                enriched_total += 1
            else:
                failed_batch += 1
                failed_total += 1
            
            # Rate limiting: ~0.75s between profiles
            time.sleep(0.75)
        
        print(f"\n✅ Batch complete: {enriched_batch} enriched, {failed_batch} failed")
        print(f"   Total: {enriched_total} enriched, {failed_total} failed")
        
        # Show progress
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Total crypto devs
            cursor.execute("SELECT COUNT(*) FROM crypto_developers")
            total = cursor.fetchone()[0]
            
            # Enriched
            cursor.execute("""
                SELECT COUNT(DISTINCT cd.github_profile_id)
                FROM crypto_developers cd
                JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id
            """)
            enriched = cursor.fetchone()[0]
            
            percentage = (enriched / total * 100) if total > 0 else 0
            
            print(f"\n📈 Progress: {enriched:,} / {total:,} ({percentage:.1f}%)")

def main(ecosystem: str = "Ethereum", batch_size: int = 50):
    """Main entry point"""
    try:
        run_continuous_enrichment(ecosystem, batch_size)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ecosystem = sys.argv[1] if len(sys.argv) > 1 else "Ethereum"
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    main(ecosystem, batch_size)


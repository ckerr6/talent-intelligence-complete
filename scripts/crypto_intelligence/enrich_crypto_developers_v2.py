#!/usr/bin/env python3
"""
ABOUTME: Continuous enrichment for crypto ecosystem developers with DETAILED LOGGING
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
from scripts.crypto_intelligence.detailed_logger import DetailedLogger
import time
import json

# Initialize detailed logger
logger = DetailedLogger('ethereum_enrichment')

def get_crypto_enrichment_queue(ecosystem: str = "Ethereum", limit: int = 100):
    """
    Get crypto developers to enrich, prioritized by contribution count.
    Only returns developers not yet enriched.
    """
    logger.info(f"🔍 Finding {ecosystem} developers to enrich...")
    
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
            logger.error(f"❌ Ecosystem '{ecosystem}' not found")
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
        
        logger.info(f"✅ Found {len(usernames)} {ecosystem} developers to enrich")
        if usernames:
            logger.info(f"   Top contributor: @{usernames[0]['username']} ({usernames[0]['contributions']:,} contributions)")
        
        return usernames

def enrich_crypto_developer(username: str, contribution_count: int, components: dict):
    """Enrich a single crypto developer with DETAILED LOGGING"""
    
    logger.log_enrichment_start(username, contribution_count)
    
    try:
        # Fetch profile data
        profile_data = components['profile_builder'].build_profile(username)
        if not profile_data:
            logger.error(f"   ❌ Failed to fetch profile for @{username}")
            return False
        
        # Log profile data received
        logger.log_profile_data_fetched(username, {
            'name': profile_data.get('user', {}).get('name'),
            'bio': profile_data.get('user', {}).get('bio'),
            'followers': profile_data.get('user', {}).get('followers', 0),
            'public_repos': profile_data.get('user', {}).get('public_repos', 0),
            'created_at': profile_data.get('user', {}).get('created_at'),
            'email': profile_data.get('user', {}).get('email'),
            'company': profile_data.get('user', {}).get('company'),
            'location': profile_data.get('user', {}).get('location')
        })
        
        # Extract skills
        skills = components['skill_extractor'].extract_skills(profile_data)
        logger.log_skills_extracted(username, skills)
        
        # Log repositories analyzed
        repos = profile_data.get('repos', [])
        if repos:
            logger.log_repositories_analyzed(username, len(repos), skills.get('languages', {}))
        
        # Assess seniority
        seniority = components['seniority_scorer'].score_seniority(profile_data, skills)
        logger.log_seniority_assessed(
            username, 
            seniority['level'], 
            seniority['confidence'],
            {
                'years_active': seniority.get('years_active'),
                'commit_volume': seniority.get('commit_volume'),
                'project_complexity': seniority.get('project_complexity')
            }
        )
        
        # Assess reachability
        reachability = components['reachability_assessor'].assess_reachability(profile_data)
        
        # Track activity
        activity = components['activity_tracker'].track_activity(profile_data)
        
        # Analyze network
        network = components['network_analyzer'].analyze_network(profile_data)
        logger.log_network_analyzed(
            username,
            len(network.get('collaborators', [])),
            network.get('organizations', []),
            network['influence_score']
        )
        
        # AI analysis (optional)
        ai_summary = None
        try:
            ai_summary = components['ai_analyzer'].generate_summary(profile_data, skills, seniority)
            logger.debug(f"   🤖 AI Summary generated")
        except Exception as e:
            logger.warning(f"   ⚠️  AI summary failed: {e}")
        
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
                logger.error(f"   ❌ Profile not found in database for @{username}")
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
        
        # Log completion
        logger.log_enrichment_complete(username, str(profile_id), {
            'seniority': seniority['level'],
            'influence': network['influence_score'],
            'reachability': reachability['score']
        })
        
        return True
        
    except Exception as e:
        logger.log_error("enrichment", e, username=username)
        return False

def run_continuous_enrichment(ecosystem: str = "Ethereum", batch_size: int = 50):
    """
    Run continuous enrichment on crypto developers with DETAILED LOGGING.
    Processes in batches, respects rate limits.
    """
    logger.info("="*80)
    logger.info(f"🚀 CRYPTO DEVELOPER ENRICHMENT - {ecosystem}")
    logger.info("="*80)
    
    # Initialize components
    github_client = GitHubClient()
    components = {
        'profile_builder': ProfileBuilder(github_client),
        'skill_extractor': SkillExtractor(),
        'seniority_scorer': SeniorityScorer(),
        'reachability_assessor': ReachabilityAssessor(),
        'activity_tracker': ActivityTracker(),
        'network_analyzer': NetworkAnalyzer(),
        'ai_analyzer': AIProfileAnalyzer()
    }
    
    enriched_total = 0
    failed_total = 0
    batch_num = 0
    
    while True:
        batch_num += 1
        
        # Get next batch
        queue = get_crypto_enrichment_queue(ecosystem, batch_size)
        
        if not queue:
            logger.info("\n✅ All discovered developers enriched!")
            logger.info("   Waiting for more discoveries...")
            time.sleep(60)  # Wait 1 minute and check again
            continue
        
        logger.info(f"\n📊 Processing batch #{batch_num} of {len(queue)} developers")
        
        enriched_batch = 0
        failed_batch = 0
        
        for dev in queue:
            username = dev['username']
            contributions = dev['contributions']
            
            success = enrich_crypto_developer(username, contributions, components)
            
            if success:
                enriched_batch += 1
                enriched_total += 1
            else:
                failed_batch += 1
                failed_total += 1
            
            # Rate limiting: ~1s between profiles (to allow for API calls)
            time.sleep(1.0)
        
        # Log batch progress
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Total crypto devs
            cursor.execute("SELECT COUNT(*) FROM crypto_developers")
            result = cursor.fetchone()
            total = result[0] if isinstance(result, tuple) else result.get('count', 0)
            
            # Enriched
            cursor.execute("""
                SELECT COUNT(DISTINCT cd.github_profile_id)
                FROM crypto_developers cd
                JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id
            """)
            result = cursor.fetchone()
            enriched = result[0] if isinstance(result, tuple) else result.get('count', 0)
            
            logger.log_batch_progress(
                batch_num,
                enriched,
                total,
                enriched_batch,
                enriched_batch
            )

def main(ecosystem: str = "Ethereum", batch_size: int = 50):
    """Main entry point"""
    try:
        run_continuous_enrichment(ecosystem, batch_size)
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Stopped by user")
    except Exception as e:
        logger.log_error("main", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ecosystem = sys.argv[1] if len(sys.argv) > 1 else "Ethereum"
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    
    main(ecosystem, batch_size)


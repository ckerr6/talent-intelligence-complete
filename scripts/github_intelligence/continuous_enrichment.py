#!/usr/bin/env python3
# ABOUTME: Simplified continuous enrichment script
# ABOUTME: Enriches GitHub profiles one at a time with visible progress

import sys
import os
sys.path.insert(0, '/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete')

from config import get_db_context
from scripts.github_intelligence.profile_builder import ProfileBuilder
from scripts.github_intelligence.skill_extractor import SkillExtractor
from scripts.github_intelligence.seniority_scorer import SeniorityScorer
from scripts.github_intelligence.reachability_assessor import ReachabilityAssessor
from scripts.github_intelligence.activity_tracker import ActivityTracker
from scripts.github_intelligence.network_analyzer import NetworkAnalyzer
from api.services.github_intelligence.ai_profile_analyzer import AIProfileAnalyzer
import time

print("🚀 Starting GitHub Intelligence Enrichment")
print("="*60)

# Initialize components
github_client = ProfileBuilder()
skill_extractor = SkillExtractor()
seniority_scorer = SeniorityScorer()
reachability_assessor = ReachabilityAssessor()
activity_tracker = ActivityTracker()
network_analyzer = NetworkAnalyzer()
ai_analyzer = AIProfileAnalyzer()

enriched_count = 0
failed_count = 0

while True:
    try:
        # Get next unenriched profile
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT gp.github_username, gp.github_profile_id
                FROM github_profile gp
                LEFT JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
                WHERE gi.github_profile_id IS NULL
                AND gp.github_username IS NOT NULL
                ORDER BY gp.followers DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if not result:
                print("\n✅ All profiles enriched!")
                break
            
            if isinstance(result, dict):
                username = result['github_username']
                profile_id = result['github_profile_id']
            else:
                username = result[0]
                profile_id = result[1]
        
        print(f"\n📊 Enriching: @{username}")
        
        # Fetch profile data
        profile_data = github_client.fetch_profile(username)
        if not profile_data:
            print(f"   ❌ Failed to fetch profile")
            failed_count += 1
            continue
        
        # Extract intelligence
        print("   🔍 Extracting skills...")
        skills = skill_extractor.extract_skills(profile_data)
        
        print("   📈 Scoring seniority...")
        seniority = seniority_scorer.score_seniority(profile_data, skills)
        
        print("   📞 Assessing reachability...")
        reachability = reachability_assessor.assess_reachability(profile_data)
        
        print("   📅 Tracking activity...")
        activity = activity_tracker.track_activity(profile_data)
        
        print("   🌐 Analyzing network...")
        network = network_analyzer.analyze_network(profile_data)
        
        print("   🤖 Generating AI summary...")
        ai_summary = ai_analyzer.generate_summary(profile_data, skills, seniority)
        
        # Store in database
        print("   💾 Storing...")
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO github_intelligence (
                    github_profile_id, inferred_seniority, seniority_confidence,
                    influence_score, reachability_score, ai_generated_summary
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                profile_id,
                seniority['level'],
                seniority['confidence'],
                network['influence_score'],
                reachability['score'],
                ai_summary
            ))
            conn.commit()
        
        enriched_count += 1
        print(f"   ✅ Done! ({enriched_count} total, {failed_count} failed)")
        
        # Rate limit: ~0.72s between requests (5000/hour)
        time.sleep(0.75)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Stopped. Enriched: {enriched_count}, Failed: {failed_count}")
        break
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed_count += 1
        time.sleep(1)

print("\n" + "="*60)
print(f"📊 Final Stats: {enriched_count} enriched, {failed_count} failed")


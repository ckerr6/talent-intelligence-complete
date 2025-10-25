#!/usr/bin/env python3
"""
ABOUTME: Main orchestrator for GitHub intelligence extraction pipeline.
ABOUTME: Coordinates all extraction modules to build comprehensive developer profiles.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import get_db_context
from scripts.github_intelligence.github_client import GitHubClient
from scripts.github_intelligence.profile_builder import ProfileBuilder
from scripts.github_intelligence.skill_extractor import SkillExtractor
from scripts.github_intelligence.seniority_scorer import SeniorityScorer
from scripts.github_intelligence.network_analyzer import NetworkAnalyzer
from scripts.github_intelligence.activity_tracker import ActivityTracker
from scripts.github_intelligence.reachability_assessor import ReachabilityAssessor
from scripts.github_intelligence.discovery import DeveloperDiscovery


class IntelligenceOrchestrator:
    """
    Orchestrates the complete intelligence extraction pipeline.
    
    Pipeline:
    1. Fetch profile data from GitHub API
    2. Extract skills from repos
    3. Calculate seniority
    4. Analyze network
    5. Track activity patterns
    6. Assess reachability
    7. Store in database
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize orchestrator with all extraction modules.
        
        Args:
            github_token: GitHub personal access token
        """
        self.client = GitHubClient(token=github_token)
        self.profile_builder = ProfileBuilder(self.client)
        self.skill_extractor = SkillExtractor()
        self.seniority_scorer = SeniorityScorer()
        self.network_analyzer = NetworkAnalyzer(self.client)
        self.activity_tracker = ActivityTracker()
        self.reachability_assessor = ReachabilityAssessor()
        self.discovery = DeveloperDiscovery(self.client)
        
        self.profiles_processed = 0
        self.profiles_failed = 0
    
    def enrich_developer(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Run complete enrichment pipeline for a developer.
        
        Args:
            username: GitHub username
        
        Returns:
            Complete intelligence data or None if failed
        """
        print(f"\n{'='*60}")
        print(f"🚀 Enriching: @{username}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Build profile
            profile_data = self.profile_builder.build_profile(username)
            if not profile_data:
                print(f"   ❌ Failed to build profile for @{username}")
                self.profiles_failed += 1
                return None
            
            # Step 2: Extract skills
            skills = self.skill_extractor.extract_skills(profile_data)
            skill_summary = self.skill_extractor.get_skill_summary(skills)
            
            # Step 3: Calculate seniority
            seniority = self.seniority_scorer.calculate_seniority(profile_data)
            
            # Step 4: Analyze network (shallow for speed)
            network = self.network_analyzer.analyze_network(profile_data, deep=False)
            
            # Step 5: Track activity
            activity = self.activity_tracker.analyze_activity(profile_data)
            
            # Step 6: Assess reachability
            reachability = self.reachability_assessor.assess_reachability(profile_data)
            
            # Compile intelligence
            intelligence = {
                'username': username,
                'profile_data': profile_data,
                'skills': skills,
                'skill_summary': skill_summary,
                'seniority': seniority,
                'network': network,
                'activity': activity,
                'reachability': reachability,
                'enriched_at': datetime.now().isoformat()
            }
            
            print(f"\n   ✅ Intelligence extraction complete for @{username}")
            print(f"      Specialization: {skill_summary['specialization']}")
            print(f"      Seniority: {seniority['seniority_level']} (confidence: {seniority['confidence']:.0%})")
            print(f"      Network: {network['total_collaborators']} collaborators")
            print(f"      Activity: {activity['activity_level']}")
            print(f"      Reachability: {reachability['reachability_score']}/100")
            
            self.profiles_processed += 1
            
            return intelligence
            
        except Exception as e:
            print(f"   ❌ Error enriching @{username}: {e}")
            import traceback
            traceback.print_exc()
            self.profiles_failed += 1
            return None
    
    def store_intelligence(self, intelligence: Dict[str, Any]) -> bool:
        """
        Store intelligence data in database.
        
        Args:
            intelligence: Complete intelligence data
        
        Returns:
            True if successful, False otherwise
        """
        username = intelligence['username']
        
        try:
            with get_db_context() as conn:
                cursor = conn.cursor()
                
                # Find github_profile_id
                cursor.execute("""
                    SELECT github_profile_id FROM github_profile
                    WHERE github_username = %s
                """, (username,))
                
                result = cursor.fetchone()
                if not result:
                    print(f"   ⚠️  No github_profile found for @{username}, skipping storage")
                    return False
                
                github_profile_id = result[0]
                
                # Extract data for storage
                skills = intelligence['skills']
                seniority = intelligence['seniority']
                network = intelligence['network']
                activity = intelligence['activity']
                reachability = intelligence['reachability']
                profile_data = intelligence['profile_data']
                user = profile_data.get('user', {})
                
                # Prepare JSONB fields
                primary_languages = json.dumps(skills.get('languages', {}))
                frameworks = json.dumps([f['name'] for f in skills.get('frameworks', [])])
                tools = json.dumps(skills.get('tools', []))
                domains = json.dumps({k: v for k, v in skills.get('domains', {}).items()})
                top_collaborators = json.dumps(network.get('top_collaborators', []))
                organization_memberships = json.dumps([org['name'] for org in network.get('organizations', [])])
                technical_specialization = json.dumps(intelligence['skill_summary'].get('top_frameworks', []))
                domain_specialization = json.dumps(list(skills.get('domains', {}).keys()))
                reachability_signals = json.dumps(reachability.get('signals', []))
                
                # Extract emails
                extracted_emails = []
                if user.get('email'):
                    extracted_emails.append(user['email'])
                
                # Insert or update github_intelligence
                cursor.execute("""
                    INSERT INTO github_intelligence (
                        github_profile_id,
                        extracted_emails,
                        inferred_location_city,
                        current_employer,
                        primary_languages,
                        frameworks,
                        tools,
                        domains,
                        years_active,
                        inferred_seniority,
                        seniority_confidence,
                        top_collaborators,
                        organization_memberships,
                        influence_score,
                        technical_specialization,
                        domain_specialization,
                        commits_per_week,
                        prs_per_month,
                        activity_trend,
                        last_active_date,
                        consistency_score,
                        reachability_score,
                        reachability_signals,
                        best_contact_method,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (github_profile_id) DO UPDATE SET
                        extracted_emails = EXCLUDED.extracted_emails,
                        inferred_location_city = EXCLUDED.inferred_location_city,
                        current_employer = EXCLUDED.current_employer,
                        primary_languages = EXCLUDED.primary_languages,
                        frameworks = EXCLUDED.frameworks,
                        tools = EXCLUDED.tools,
                        domains = EXCLUDED.domains,
                        years_active = EXCLUDED.years_active,
                        inferred_seniority = EXCLUDED.inferred_seniority,
                        seniority_confidence = EXCLUDED.seniority_confidence,
                        top_collaborators = EXCLUDED.top_collaborators,
                        organization_memberships = EXCLUDED.organization_memberships,
                        influence_score = EXCLUDED.influence_score,
                        technical_specialization = EXCLUDED.technical_specialization,
                        domain_specialization = EXCLUDED.domain_specialization,
                        commits_per_week = EXCLUDED.commits_per_week,
                        prs_per_month = EXCLUDED.prs_per_month,
                        activity_trend = EXCLUDED.activity_trend,
                        last_active_date = EXCLUDED.last_active_date,
                        consistency_score = EXCLUDED.consistency_score,
                        reachability_score = EXCLUDED.reachability_score,
                        reachability_signals = EXCLUDED.reachability_signals,
                        best_contact_method = EXCLUDED.best_contact_method,
                        updated_at = NOW()
                """, (
                    github_profile_id,
                    extracted_emails,
                    user.get('location'),
                    user.get('company'),
                    primary_languages,
                    frameworks,
                    tools,
                    domains,
                    seniority.get('breakdown', {}).get('experience', 0) / 10,  # Rough years estimate
                    seniority.get('seniority_level'),
                    seniority.get('confidence'),
                    top_collaborators,
                    organization_memberships,
                    network.get('influence_score'),
                    technical_specialization,
                    domain_specialization,
                    activity.get('commits_per_week'),
                    activity.get('prs_per_month'),
                    activity.get('activity_trend'),
                    activity.get('last_active_date'),
                    activity.get('consistency_score'),
                    reachability.get('reachability_score'),
                    reachability_signals,
                    reachability.get('best_contact_method')
                ))
                
                conn.commit()
                print(f"   ✅ Stored intelligence for @{username}")
                return True
                
        except Exception as e:
            print(f"   ❌ Error storing intelligence for @{username}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def enrich_and_store(self, username: str) -> bool:
        """
        Enrich a developer and store results in database.
        
        Args:
            username: GitHub username
        
        Returns:
            True if successful, False otherwise
        """
        intelligence = self.enrich_developer(username)
        
        if intelligence:
            return self.store_intelligence(intelligence)
        
        return False
    
    def enrich_batch(self, usernames: List[str], checkpoint_interval: int = 10) -> Dict[str, int]:
        """
        Enrich a batch of developers with progress tracking.
        
        Args:
            usernames: List of GitHub usernames
            checkpoint_interval: Save progress every N profiles
        
        Returns:
            Statistics dictionary
        """
        total = len(usernames)
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting batch enrichment: {total} developers")
        print(f"{'='*60}\n")
        
        for i, username in enumerate(usernames, 1):
            print(f"\n[{i}/{total}] Processing @{username}...")
            
            self.enrich_and_store(username)
            
            # Checkpoint
            if i % checkpoint_interval == 0:
                print(f"\n📊 Checkpoint at {i}/{total}")
                print(f"   Processed: {self.profiles_processed}")
                print(f"   Failed: {self.profiles_failed}")
                print(f"   Success rate: {self.profiles_processed / i * 100:.1f}%")
                self.client.print_rate_limit_status()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"✨ Batch enrichment complete!")
        print(f"{'='*60}")
        print(f"   Total: {total}")
        print(f"   Successful: {self.profiles_processed}")
        print(f"   Failed: {self.profiles_failed}")
        print(f"   Success rate: {self.profiles_processed / total * 100:.1f}%")
        
        self.client.print_rate_limit_status()
        
        return {
            'total': total,
            'successful': self.profiles_processed,
            'failed': self.profiles_failed
        }
    
    def enrich_existing_profiles(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Enrich existing GitHub profiles from database.
        
        Args:
            limit: Maximum number of profiles to enrich
        
        Returns:
            Statistics dictionary
        """
        print("🔍 Finding existing GitHub profiles to enrich...")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Find profiles not yet enriched
            query = """
                SELECT gp.github_username
                FROM github_profile gp
                LEFT JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
                WHERE gi.github_profile_id IS NULL
                AND gp.github_username IS NOT NULL
                ORDER BY gp.followers DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            usernames = [row[0] for row in cursor.fetchall()]
        
        print(f"   ✅ Found {len(usernames)} profiles to enrich")
        
        if not usernames:
            print("   No profiles need enrichment!")
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        return self.enrich_batch(usernames)


def main():
    """
    Main entry point with CLI interface.
    """
    parser = argparse.ArgumentParser(
        description='GitHub Intelligence Orchestrator - Extract deep intelligence from GitHub profiles'
    )
    
    parser.add_argument(
        '--mode',
        choices=['single', 'batch', 'existing', 'discover'],
        default='single',
        help='Operation mode'
    )
    
    parser.add_argument(
        '--username',
        help='GitHub username (for single mode)'
    )
    
    parser.add_argument(
        '--usernames',
        nargs='+',
        help='List of GitHub usernames (for batch mode)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of profiles to process'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (process 5 profiles)'
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = IntelligenceOrchestrator()
    
    # Test mode
    if args.test:
        print("🧪 Running in TEST mode (5 profiles)")
        test_usernames = ['vitalik', 'haydenadams', 'gakonst', 't11s', 'transmissions11']
        orchestrator.enrich_batch(test_usernames[:5])
        return
    
    # Single mode
    if args.mode == 'single':
        if not args.username:
            print("❌ --username required for single mode")
            return
        
        orchestrator.enrich_and_store(args.username)
    
    # Batch mode
    elif args.mode == 'batch':
        if not args.usernames:
            print("❌ --usernames required for batch mode")
            return
        
        orchestrator.enrich_batch(args.usernames)
    
    # Existing profiles mode
    elif args.mode == 'existing':
        limit = args.limit or 100
        orchestrator.enrich_existing_profiles(limit=limit)
    
    # Discovery mode
    elif args.mode == 'discover':
        print("🔍 Running discovery mode...")
        discovered = orchestrator.discovery.discover_high_value_targets(limit_per_org=30)
        not_enriched = orchestrator.discovery.filter_already_enriched(discovered)
        
        if not_enriched:
            limit = args.limit or 50
            to_enrich = not_enriched[:limit]
            orchestrator.enrich_batch(to_enrich)


if __name__ == '__main__':
    main()


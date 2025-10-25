#!/usr/bin/env python3
"""
ABOUTME: Database migration script for GitHub-native intelligence tables.
ABOUTME: Creates new tables to store deep GitHub intelligence without modifying existing schema.

Migrate Existing GitHub Data to Enhanced Schema

We already have:
- 100K+ GitHub profiles
- 24K+ merged PRs
- Contribution data

This script:
1. Creates new intelligence tables (additive only, no modifications to existing)
2. Analyzes existing data for baseline metrics
3. Prepares for deep intelligence extraction
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import get_db_context
from datetime import datetime


def create_intelligence_tables():
    """
    Create new tables for GitHub intelligence.
    These are additive - existing tables are not modified.
    """
    
    print("🏗️  Creating GitHub intelligence tables...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Table 1: github_intelligence - Main intelligence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_intelligence (
                github_profile_id UUID PRIMARY KEY REFERENCES github_profile(github_profile_id),
                
                -- Identity & Contact (extracted from GitHub)
                extracted_emails TEXT[],
                inferred_timezone VARCHAR(50),
                inferred_location_city VARCHAR(100),
                inferred_location_country VARCHAR(100),
                current_employer VARCHAR(255),
                
                -- Technical Skills (analyzed from repos/commits)
                primary_languages JSONB,  -- {language: lines_of_code}
                frameworks JSONB,          -- [framework1, framework2, ...]
                tools JSONB,
                domains JSONB,             -- [DeFi, NFT, L2, ...]
                
                -- Experience & Seniority
                years_active FLOAT,
                total_commits INT,
                repos_maintained INT,
                major_project_contributions INT,
                inferred_seniority VARCHAR(50),  -- Junior, Mid, Senior, Staff, Principal
                seniority_confidence FLOAT,      -- 0.0 to 1.0
                
                -- Collaboration & Network
                top_collaborators JSONB,  -- [{username, collaboration_strength, shared_repos}, ...]
                organization_memberships JSONB,  -- [org1, org2, ...]
                influence_score INT,      -- 0-100
                
                -- Specialization
                technical_specialization JSONB,  -- [Smart Contracts, Frontend, ...]
                domain_specialization JSONB,     -- [DeFi, Gaming, ...]
                focus_areas JSONB,               -- [Security, Performance, ...]
                
                -- Activity & Trajectory
                commits_per_week FLOAT,
                prs_per_month FLOAT,
                activity_trend VARCHAR(50),  -- Growing, Stable, Declining
                last_active_date TIMESTAMP,
                consistency_score FLOAT,     -- 0.0 to 1.0
                
                -- Reachability
                reachability_score INT,  -- 0-100
                reachability_signals JSONB,  -- [{signal, weight}, ...]
                best_contact_method VARCHAR(50),
                
                -- AI Analysis
                ai_generated_summary TEXT,
                ideal_role_fit TEXT,
                ai_analyzed_at TIMESTAMP,
                
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Indexes for github_intelligence
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_github_intelligence_seniority 
                ON github_intelligence(inferred_seniority)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_github_intelligence_reachability 
                ON github_intelligence(reachability_score)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_github_intelligence_active 
                ON github_intelligence(last_active_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_github_intelligence_influence 
                ON github_intelligence(influence_score)
        """)
        
        print("   ✅ github_intelligence table created")
        
        # Table 2: github_collaboration - Network relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_collaboration (
                collaboration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                github_profile_id UUID REFERENCES github_profile(github_profile_id),
                collaborator_profile_id UUID REFERENCES github_profile(github_profile_id),
                
                shared_repos TEXT[],
                collaboration_strength INT,  -- Number of interactions
                relationship_type VARCHAR(50),  -- coworker, reviewer, contributor
                
                reviews_given INT DEFAULT 0,
                reviews_received INT DEFAULT 0,
                shared_organizations TEXT[],
                
                first_interaction TIMESTAMP,
                last_interaction TIMESTAMP,
                
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                
                UNIQUE(github_profile_id, collaborator_profile_id)
            )
        """)
        
        # Indexes for github_collaboration
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_collaboration_profile 
                ON github_collaboration(github_profile_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_collaboration_strength 
                ON github_collaboration(collaboration_strength)
        """)
        
        print("   ✅ github_collaboration table created")
        
        # Table 3: github_market_intelligence - Talent flows and hiring signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_market_intelligence (
                market_intel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                
                organization_name VARCHAR(255),
                snapshot_date DATE,
                
                -- Team metrics
                total_contributors INT,
                active_contributors_90d INT,
                core_team_size INT,
                
                -- Language distribution
                language_distribution JSONB,  -- {language: contributor_count}
                
                -- Skill distribution
                skill_distribution JSONB,  -- {skill: count}
                
                -- Talent flow
                new_contributors_30d INT,
                departed_contributors_30d INT,
                departed_to JSONB,  -- [{company, count}, ...]
                
                -- Hiring signals
                hiring_trend VARCHAR(50),  -- Growing, Stable, Declining
                growth_rate FLOAT,
                
                created_at TIMESTAMP DEFAULT NOW(),
                
                UNIQUE(organization_name, snapshot_date)
            )
        """)
        
        # Indexes for github_market_intelligence
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_intel_org 
                ON github_market_intelligence(organization_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_intel_date 
                ON github_market_intelligence(snapshot_date)
        """)
        
        print("   ✅ github_market_intelligence table created")
        
        # Table 4: github_activity_timeline - Time-series activity data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_activity_timeline (
                timeline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                github_profile_id UUID REFERENCES github_profile(github_profile_id),
                
                week_start DATE,
                
                commits_count INT,
                prs_opened INT,
                prs_merged INT,
                issues_opened INT,
                reviews_given INT,
                
                active_days INT,  -- Days active this week
                active_hours JSONB,  -- [hour1, hour2, ...] when they were active
                
                created_at TIMESTAMP DEFAULT NOW(),
                
                UNIQUE(github_profile_id, week_start)
            )
        """)
        
        # Indexes for github_activity_timeline
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_timeline_profile 
                ON github_activity_timeline(github_profile_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_timeline_date 
                ON github_activity_timeline(week_start)
        """)
        
        print("   ✅ github_activity_timeline table created")
        
        conn.commit()
        print("\n✅ All tables created successfully!")


def analyze_existing_data():
    """
    Analyze what data we already have in the database.
    """
    
    print("\n📊 Analyzing existing GitHub data...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Count existing GitHub profiles
        cursor.execute("SELECT COUNT(*) FROM github_profile")
        result = cursor.fetchone()
        profile_count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {profile_count:,} GitHub profiles")
        
        # Count people with linked GitHub
        cursor.execute("SELECT COUNT(*) FROM github_profile WHERE person_id IS NOT NULL")
        result = cursor.fetchone()
        linked_count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {linked_count:,} GitHub profiles linked to people")
        
        # Count contributions
        cursor.execute("SELECT COUNT(*) FROM github_contribution")
        result = cursor.fetchone()
        contrib_count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {contrib_count:,} contribution records")
        
        # Count repos
        cursor.execute("SELECT COUNT(*) FROM github_repository")
        result = cursor.fetchone()
        repo_count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {repo_count:,} repositories tracked")
        
        # Sample profiles with email
        cursor.execute("""
            SELECT COUNT(*) FROM github_profile 
            WHERE github_email IS NOT NULL AND github_email != ''
        """)
        result = cursor.fetchone()
        email_count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {email_count:,} profiles have public email")
        
        # Profiles with bio
        cursor.execute("""
            SELECT COUNT(*) FROM github_profile 
            WHERE bio IS NOT NULL AND bio != ''
        """)
        result = cursor.fetchone()
        bio_count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {bio_count:,} profiles have bio")
        
        # Profiles enriched recently (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) FROM github_profile 
            WHERE last_enriched > NOW() - INTERVAL '30 days'
        """)
        result = cursor.fetchone()
        recent_enriched = result['count'] if isinstance(result, dict) else result[0]
        print(f"   {recent_enriched:,} profiles enriched in last 30 days")


def create_test_sample():
    """
    Create a small test sample of profiles to enrich.
    """
    
    print("\n🔬 Preparing test sample...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Find 100 profiles that:
        # 1. Have a username
        # 2. Have some contribution data
        # 3. Are diverse in follower count
        cursor.execute("""
            SELECT 
                gp.github_profile_id,
                gp.github_username,
                gp.github_name,
                gp.github_email,
                gp.github_company,
                gp.location,
                gp.followers,
                COUNT(gc.contribution_id) as contrib_count
            FROM github_profile gp
            LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            WHERE gp.github_username IS NOT NULL
            GROUP BY gp.github_profile_id
            HAVING COUNT(gc.contribution_id) > 0
            ORDER BY RANDOM()
            LIMIT 100
        """)
        
        profiles = cursor.fetchall()
        print(f"   ✅ Selected {len(profiles)} profiles for test sample")
        
        if profiles:
            print(f"\n   Sample profile examples:")
            for i, profile in enumerate(profiles[:5]):
                # Handle both dict and tuple results
                if isinstance(profile, dict):
                    username = profile['github_username']
                    followers = profile['followers']
                    contribs = profile['contrib_count']
                else:
                    username = profile[1]
                    followers = profile[6]
                    contribs = profile[7]
                print(f"      {i+1}. @{username} - {followers} followers, {contribs} contributions")
        
        return profiles


def main():
    """
    Main migration process.
    """
    
    print("=" * 60)
    print("GitHub-Native Intelligence - Database Migration")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Create new tables
        create_intelligence_tables()
        
        # Step 2: Analyze existing data
        analyze_existing_data()
        
        # Step 3: Create test sample
        test_profiles = create_test_sample()
        
        print("\n" + "=" * 60)
        print("✨ Migration complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run intelligence extraction on test sample (100 profiles)")
        print("   python scripts/github_intelligence/intelligence_orchestrator.py --test")
        print()
        print("2. Build out the core extraction modules:")
        print("   - profile_builder.py")
        print("   - skill_extractor.py")
        print("   - seniority_scorer.py")
        print("   - network_analyzer.py")
        print("   - activity_tracker.py")
        print("   - reachability_assessor.py")
        print()
        print("3. Run full extraction on all 100K+ profiles")
        print("   python scripts/github_intelligence/intelligence_orchestrator.py --full")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


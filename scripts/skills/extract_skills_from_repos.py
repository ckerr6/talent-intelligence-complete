#!/usr/bin/env python3
"""
ABOUTME: Extract skills from repository languages and link repos to skills
ABOUTME: Derives person skills from their repository contributions

Extract Skills from Repositories
=================================
Extracts skills by:
1. Linking repositories to skills via their primary language
2. Deriving person skills from their contributions to repos

Process:
- github_repository.language → repository_skills
- github_contribution + repository_skills → person_skills

Usage:
    python3 extract_skills_from_repos.py --all
    python3 extract_skills_from_repos.py --limit 1000
    python3 extract_skills_from_repos.py --repos-only  # Only tag repos, don't compute person skills

Author: AI Assistant (Tier 1 Data Completion)
Date: October 24, 2025
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Dict, List, Set, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import load_env_file, get_db_connection
load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RepoSkillExtractor:
    """Extract skills from repositories and derive person skills"""
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        # Load language → skill mappings
        self.language_skill_map = self._load_language_skill_map()
        
        self.stats = {
            'repos_processed': 0,
            'repo_skills_created': 0,
            'people_processed': 0,
            'person_skills_created': 0,
            'person_skills_updated': 0,
            'errors': []
        }
    
    def _load_language_skill_map(self) -> Dict[str, Dict]:
        """Load programming language → skill mappings"""
        cursor = self.conn.cursor()
        
        # Get all language-category skills
        cursor.execute("""
            SELECT 
                skill_id,
                skill_name,
                aliases
            FROM skills
            WHERE category = 'language'
        """)
        
        language_map = {}
        
        for row in cursor.fetchall():
            skill_dict = dict(row)
            skill_name = skill_dict['skill_name']
            aliases = skill_dict.get('aliases', []) or []
            
            # Map main name
            language_map[skill_name.lower()] = skill_dict
            
            # Map aliases
            for alias in aliases:
                language_map[alias.lower()] = skill_dict
        
        logger.info(f"Loaded {len(set(s['skill_id'] for s in language_map.values()))} language skills")
        return language_map
    
    def tag_repositories_with_skills(self, limit: Optional[int] = None) -> int:
        """
        Tag repositories with skills based on their primary language
        
        Returns: Number of repos tagged
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                repo_id,
                full_name,
                language
            FROM github_repository
            WHERE language IS NOT NULL
            AND language != ''
            AND NOT EXISTS (
                SELECT 1 FROM repository_skills rs 
                WHERE rs.repo_id = github_repository.repo_id
            )
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        repos = cursor.fetchall()
        
        total = len(repos)
        logger.info(f"Tagging {total:,} repositories with skills...")
        
        tagged_count = 0
        
        for i, repo_row in enumerate(repos, 1):
            if i % 5000 == 0:
                logger.info(f"  Progress: {i:,}/{total:,} ({i/total*100:.1f}%) - "
                           f"Repos tagged: {tagged_count:,}")
            
            repo = dict(repo_row)
            language = repo.get('language', '').lower().strip()
            
            if not language:
                continue
            
            # Find matching skill
            skill_dict = self.language_skill_map.get(language)
            
            if not skill_dict:
                # Skip unknown languages (could log for later addition)
                continue
            
            # Insert repository_skill
            try:
                cursor.execute("""
                    INSERT INTO repository_skills (
                        repo_id,
                        skill_id,
                        is_primary,
                        confidence_score,
                        source
                    )
                    VALUES (
                        %s::uuid,
                        %s::uuid,
                        TRUE,
                        0.95,
                        'github_language'
                    )
                    ON CONFLICT (repo_id, skill_id) DO NOTHING
                """, (repo['repo_id'], skill_dict['skill_id']))
                
                if cursor.rowcount > 0:
                    tagged_count += 1
                    self.stats['repo_skills_created'] += 1
                
                # Commit every 1000 repos
                if i % 1000 == 0:
                    self.conn.commit()
                    
            except Exception as e:
                logger.error(f"Error tagging repo {repo['full_name']}: {e}")
                self.conn.rollback()
                self.stats['errors'].append(f"Repo {repo['full_name']}: {e}")
        
        # Final commit
        self.conn.commit()
        
        self.stats['repos_processed'] = total
        return tagged_count
    
    def compute_person_skills_from_repos(self, limit: Optional[int] = None) -> int:
        """
        Compute person skills from their repository contributions
        
        Returns: Number of people processed
        """
        cursor = self.conn.cursor()
        
        # Get people with GitHub contributions
        query = """
            SELECT DISTINCT gp.person_id
            FROM github_profile gp
            JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            WHERE gp.person_id IS NOT NULL
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        person_ids = [row['person_id'] for row in cursor.fetchall()]
        
        total = len(person_ids)
        logger.info(f"Computing skills for {total:,} people from their repos...")
        
        for i, person_id in enumerate(person_ids, 1):
            if i % 500 == 0:
                logger.info(f"  Progress: {i:,}/{total:,} ({i/total*100:.1f}%) - "
                           f"Person skills created: {self.stats['person_skills_created']:,}")
            
            try:
                self._compute_person_skills_from_contributions(person_id)
                self.stats['people_processed'] += 1
            except Exception as e:
                logger.error(f"Error processing person {person_id}: {e}")
                self.stats['errors'].append(f"Person {person_id}: {e}")
        
        return total
    
    def _compute_person_skills_from_contributions(self, person_id: str):
        """Compute skills for one person from their contributions"""
        cursor = self.conn.cursor()
        
        # Get skills from repos the person contributed to, aggregated
        cursor.execute("""
            SELECT 
                rs.skill_id,
                s.skill_name,
                COUNT(DISTINCT gc.repo_id) as repos_using_skill,
                SUM(gc.contribution_count) as total_contributions,
                SUM(gc.merged_pr_count) as merged_prs,
                MIN(gc.first_contribution_date) as first_seen,
                MAX(gc.last_contribution_date) as last_used
            FROM github_contribution gc
            JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
            JOIN repository_skills rs ON gc.repo_id = rs.repo_id
            JOIN skills s ON rs.skill_id = s.skill_id
            WHERE gp.person_id = %s::uuid
            AND rs.is_primary = TRUE
            GROUP BY rs.skill_id, s.skill_name
        """, (person_id,))
        
        skill_rows = cursor.fetchall()
        
        for skill_row in skill_rows:
            skill = dict(skill_row)
            
            # Calculate proficiency based on:
            # - Number of repos (weight: 10 per repo, max 30)
            # - Contribution count (weight: 0.01 per contribution, max 20)
            # - Merged PRs (weight: 2 per PR, max 20)
            
            repo_score = min(skill['repos_using_skill'] * 10, 30)
            contrib_score = min(skill['total_contributions'] * 0.01, 20)
            pr_score = min((skill.get('merged_prs') or 0) * 2, 20)
            
            # Base proficiency from repos
            proficiency = 30 + repo_score + contrib_score + pr_score
            proficiency = min(proficiency, 100)  # Cap at 100
            
            # Insert or update person_skill
            try:
                cursor.execute("""
                    INSERT INTO person_skills (
                        person_id,
                        skill_id,
                        proficiency_score,
                        evidence_sources,
                        confidence_score,
                        merged_prs_count,
                        repos_using_skill,
                        first_seen,
                        last_used
                    )
                    VALUES (
                        %s::uuid,
                        %s::uuid,
                        %s,
                        ARRAY['repos'],
                        0.85,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    ON CONFLICT (person_id, skill_id) DO UPDATE SET
                        -- Add 'repos' to evidence sources if not present
                        evidence_sources = CASE 
                            WHEN 'repos' = ANY(person_skills.evidence_sources) THEN person_skills.evidence_sources
                            ELSE array_append(person_skills.evidence_sources, 'repos')
                        END,
                        -- Update proficiency (combine existing + new evidence)
                        proficiency_score = GREATEST(
                            person_skills.proficiency_score,
                            (person_skills.proficiency_score + EXCLUDED.proficiency_score) / 2.0
                        ),
                        -- Increase confidence
                        confidence_score = LEAST(
                            (person_skills.confidence_score + EXCLUDED.confidence_score) / 2.0,
                            1.0
                        ),
                        -- Update metrics
                        merged_prs_count = COALESCE(person_skills.merged_prs_count, 0) + EXCLUDED.merged_prs_count,
                        repos_using_skill = EXCLUDED.repos_using_skill,
                        first_seen = LEAST(person_skills.first_seen, EXCLUDED.first_seen),
                        last_used = GREATEST(person_skills.last_used, EXCLUDED.last_used),
                        updated_at = NOW()
                    RETURNING (xmax = 0) as is_insert
                """, (
                    person_id,
                    skill['skill_id'],
                    proficiency,
                    skill.get('merged_prs', 0),
                    skill['repos_using_skill'],
                    skill.get('first_seen'),
                    skill.get('last_used')
                ))
                
                result = cursor.fetchone()
                if result and result['is_insert']:
                    self.stats['person_skills_created'] += 1
                else:
                    self.stats['person_skills_updated'] += 1
                
                self.conn.commit()
                
            except Exception as e:
                logger.error(f"Error upserting person skill: {e}")
                self.conn.rollback()
                self.stats['errors'].append(str(e))
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Extract skills from repositories')
    parser.add_argument('--all', action='store_true', help='Process all repos and people')
    parser.add_argument('--limit', type=int, help='Limit number to process')
    parser.add_argument('--repos-only', action='store_true', help='Only tag repos, skip person skills')
    args = parser.parse_args()
    
    print("\n" + "🔍 " + "=" * 66)
    print("🔍  Skills Extraction from Repositories")
    print("🔍 " + "=" * 66)
    
    extractor = RepoSkillExtractor()
    
    limit = None if args.all else (args.limit or 100000)
    
    # Phase 1: Tag repositories
    print(f"\n📋 Phase 1: Tagging repositories with skills...")
    tagged = extractor.tag_repositories_with_skills(limit=limit)
    print(f"✅ Tagged {tagged:,} repositories")
    
    if not args.repos_only:
        # Phase 2: Compute person skills
        print(f"\n📋 Phase 2: Computing person skills from contributions...")
        people_processed = extractor.compute_person_skills_from_repos(limit=limit)
        print(f"✅ Processed {people_processed:,} people")
    
    stats = extractor.stats
    
    print("\n" + "📊 " + "=" * 66)
    print("📊  Extraction Results")
    print("📊 " + "=" * 66)
    print(f"✅ Repos processed: {stats['repos_processed']:,}")
    print(f"✅ Repo-skill links created: {stats['repo_skills_created']:,}")
    
    if not args.repos_only:
        print(f"✅ People processed: {stats['people_processed']:,}")
        print(f"✅ Person-skill records created: {stats['person_skills_created']:,}")
        print(f"✅ Person-skill records updated: {stats['person_skills_updated']:,}")
    
    if stats['errors']:
        print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
        print("   (See log for details)")
    
    print("=" * 70)
    
    extractor.close()


if __name__ == '__main__':
    main()


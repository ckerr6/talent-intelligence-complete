#!/usr/bin/env python3
"""
ABOUTME: Extract skills from job titles and person headlines
ABOUTME: Rule-based skill extraction from employment and profile data

Extract Skills from Titles
===========================
Extracts skills from:
- employment.title (e.g., "Senior Solidity Engineer")
- person.headline (e.g., "Full Stack Developer | React & Node.js")

Uses pattern matching to identify skills from titles.

Usage:
    python3 extract_skills_from_titles.py --all
    python3 extract_skills_from_titles.py --limit 1000
    python3 extract_skills_from_titles.py --person-id <uuid>

Author: AI Assistant (Tier 1 Data Completion)
Date: October 24, 2025
"""

import argparse
import sys
from pathlib import Path
import logging
import re
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import load_env_file, get_db_connection
load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Seniority keywords (used for proficiency scoring later)
SENIORITY_LEVELS = {
    'junior': 1,
    'jr': 1,
    'associate': 1,
    'mid-level': 2,
    'intermediate': 2,
    'senior': 3,
    'sr': 3,
    'lead': 4,
    'principal': 5,
    'staff': 5,
    'distinguished': 6,
    'fellow': 7,
    'architect': 4,
    'head': 5,
    'director': 5,
    'vp': 6,
    'chief': 7,
    'cto': 7,
    'ceo': 7,
}


class TitleSkillExtractor:
    """Extract skills from job titles and headlines"""
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
        
        # Load skills from database
        self.skills_map = self._load_skills_map()
        
        self.stats = {
            'people_processed': 0,
            'titles_processed': 0,
            'skills_extracted': 0,
            'person_skills_created': 0,
            'person_skills_updated': 0,
            'errors': []
        }
    
    def _load_skills_map(self) -> Dict[str, Dict]:
        """Load skills and their aliases from database"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                skill_id,
                skill_name,
                aliases,
                category
            FROM skills
        """)
        
        skills_map = {}
        
        for row in cursor.fetchall():
            skill_dict = dict(row)
            skill_id = skill_dict['skill_id']
            skill_name = skill_dict['skill_name']
            aliases = skill_dict.get('aliases', []) or []
            
            # Add main name
            key = skill_name.lower()
            if key not in skills_map:
                skills_map[key] = skill_dict
            
            # Add aliases
            for alias in aliases:
                alias_key = alias.lower()
                if alias_key not in skills_map:
                    skills_map[alias_key] = skill_dict
        
        logger.info(f"Loaded {len(skills_map)} skill mappings ({len(set(s['skill_id'] for s in skills_map.values()))} unique skills)")
        return skills_map
    
    def extract_skills_from_text(self, text: str) -> Set[Dict]:
        """
        Extract skills from text using pattern matching
        
        Returns: Set of dicts with skill_id, skill_name, match_text
        """
        if not text or not text.strip():
            return set()
        
        text_lower = text.lower()
        found_skills = set()
        
        # Try exact matches first (for multi-word skills)
        for skill_key, skill_dict in sorted(
            self.skills_map.items(),
            key=lambda x: len(x[0]),  # Longer matches first
            reverse=True
        ):
            # Use word boundaries to avoid partial matches
            # e.g., "Go" should match "Go Developer" but not "Google"
            pattern = r'\b' + re.escape(skill_key) + r'\b'
            
            if re.search(pattern, text_lower):
                found_skills.add((
                    skill_dict['skill_id'],
                    skill_dict['skill_name'],
                    skill_key
                ))
        
        return found_skills
    
    def detect_seniority_level(self, text: str) -> int:
        """
        Detect seniority level from text (0-7)
        
        Returns: Seniority level (0 = unknown, 1-7 = junior to C-level)
        """
        if not text:
            return 0
        
        text_lower = text.lower()
        
        for keyword, level in sorted(
            SENIORITY_LEVELS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                return level
        
        return 2  # Default to mid-level if no seniority detected
    
    def extract_skills_for_person(self, person_id: str) -> int:
        """
        Extract skills from a person's titles and headline
        
        Returns: Number of skills extracted
        """
        cursor = self.conn.cursor()
        
        # Get person data
        cursor.execute("""
            SELECT 
                person_id,
                full_name,
                headline
            FROM person
            WHERE person_id = %s::uuid
        """, (person_id,))
        
        person_row = cursor.fetchone()
        if not person_row:
            logger.warning(f"Person {person_id} not found")
            return 0
        
        person = dict(person_row)
        skills_found = set()
        
        # Extract from headline
        headline = person.get('headline', '')
        if headline:
            headline_skills = self.extract_skills_from_text(headline)
            for skill_id, skill_name, match_text in headline_skills:
                seniority = self.detect_seniority_level(headline)
                skills_found.add((skill_id, skill_name, seniority, 'headline'))
        
        # Extract from employment titles
        cursor.execute("""
            SELECT 
                title,
                start_date,
                end_date,
                (end_date IS NULL) as is_current
            FROM employment
            WHERE person_id = %s::uuid
            ORDER BY (end_date IS NULL) DESC, start_date DESC NULLS LAST
        """, (person_id,))
        
        employment_rows = cursor.fetchall()
        
        for emp_row in employment_rows:
            emp = dict(emp_row)
            title = emp.get('title', '')
            
            if not title:
                continue
            
            self.stats['titles_processed'] += 1
            
            title_skills = self.extract_skills_from_text(title)
            for skill_id, skill_name, match_text in title_skills:
                seniority = self.detect_seniority_level(title)
                
                # Boost seniority if it's a current position
                if emp.get('is_current'):
                    seniority = min(seniority + 1, 7)
                
                skills_found.add((skill_id, skill_name, seniority, 'title'))
        
        # Insert/update person_skills
        for skill_id, skill_name, seniority, source in skills_found:
            self._upsert_person_skill(
                person_id,
                skill_id,
                skill_name,
                seniority,
                source
            )
        
        self.stats['skills_extracted'] += len(skills_found)
        return len(skills_found)
    
    def _upsert_person_skill(
        self,
        person_id: str,
        skill_id: str,
        skill_name: str,
        seniority: int,
        source: str
    ):
        """Insert or update a person_skill record"""
        cursor = self.conn.cursor()
        
        # Calculate initial proficiency based on seniority
        # Junior: 20-30, Mid: 40-50, Senior: 60-70, Lead+: 75-85
        base_proficiency = {
            0: 30,  # Unknown
            1: 25,  # Junior
            2: 45,  # Mid
            3: 65,  # Senior
            4: 75,  # Lead
            5: 80,  # Principal/Staff
            6: 85,  # Distinguished
            7: 90,  # Fellow/C-level
        }.get(seniority, 45)
        
        try:
            # First check if exists
            cursor.execute("""
                SELECT person_skills_id 
                FROM person_skills 
                WHERE person_id = %s::uuid AND skill_id = %s::uuid
            """, (person_id, skill_id))
            
            exists = cursor.fetchone() is not None
            
            cursor.execute("""
                INSERT INTO person_skills (
                    person_id,
                    skill_id,
                    proficiency_score,
                    evidence_sources,
                    confidence_score,
                    first_seen,
                    last_used
                )
                VALUES (
                    %s::uuid,
                    %s::uuid,
                    %s,
                    ARRAY[%s],
                    0.7,
                    CURRENT_DATE,
                    CURRENT_DATE
                )
                ON CONFLICT (person_id, skill_id) DO UPDATE SET
                    evidence_sources = CASE 
                        WHEN %s = ANY(person_skills.evidence_sources) THEN person_skills.evidence_sources
                        ELSE array_append(person_skills.evidence_sources, %s)
                    END,
                    proficiency_score = GREATEST(person_skills.proficiency_score, EXCLUDED.proficiency_score),
                    confidence_score = (person_skills.confidence_score + EXCLUDED.confidence_score) / 2.0,
                    last_used = CURRENT_DATE,
                    updated_at = NOW()
            """, (person_id, skill_id, base_proficiency, source, source, source))
            
            if exists:
                self.stats['person_skills_updated'] += 1
            else:
                self.stats['person_skills_created'] += 1
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error upserting person skill: {e}")
            self.conn.rollback()
            self.stats['errors'].append(str(e))
    
    def extract_skills_for_all(self, limit: Optional[int] = None) -> Dict:
        """Extract skills for all people"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT person_id
            FROM person
            WHERE (
                headline IS NOT NULL
                OR EXISTS (
                    SELECT 1 FROM employment e 
                    WHERE e.person_id = person.person_id 
                    AND e.title IS NOT NULL
                )
            )
            ORDER BY person_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        person_ids = [row['person_id'] for row in cursor.fetchall()]
        
        total = len(person_ids)
        logger.info(f"Extracting skills from titles for {total:,} people...")
        
        for i, person_id in enumerate(person_ids, 1):
            if i % 500 == 0:
                logger.info(f"  Progress: {i:,}/{total:,} ({i/total*100:.1f}%) - "
                           f"Skills extracted: {self.stats['skills_extracted']:,}")
            
            try:
                self.extract_skills_for_person(person_id)
                self.stats['people_processed'] += 1
            except Exception as e:
                logger.error(f"Error processing person {person_id}: {e}")
                self.stats['errors'].append(f"Person {person_id}: {e}")
        
        return self.stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Extract skills from job titles and headlines')
    parser.add_argument('--all', action='store_true', help='Extract for all people')
    parser.add_argument('--limit', type=int, help='Limit number of people to process')
    parser.add_argument('--person-id', help='Extract for specific person')
    args = parser.parse_args()
    
    print("\n" + "🔍 " + "=" * 66)
    print("🔍  Skills Extraction from Titles & Headlines")
    print("🔍 " + "=" * 66)
    
    extractor = TitleSkillExtractor()
    
    if args.person_id:
        print(f"\n📋 Extracting skills for person: {args.person_id}")
        count = extractor.extract_skills_for_person(args.person_id)
        print(f"\n✅ Extracted {count} skills")
    else:
        limit = None if args.all else (args.limit or 10000)
        
        if args.all:
            print("\n⚠️  Extracting for ALL people (no limit)")
        else:
            print(f"\n📋 Extracting for up to {limit:,} people")
        
        stats = extractor.extract_skills_for_all(limit=limit)
        
        print("\n" + "📊 " + "=" * 66)
        print("📊  Extraction Results")
        print("📊 " + "=" * 66)
        print(f"✅ People processed: {stats['people_processed']:,}")
        print(f"✅ Titles analyzed: {stats['titles_processed']:,}")
        print(f"✅ Skills extracted: {stats['skills_extracted']:,}")
        print(f"✅ Person-skill records created: {stats['person_skills_created']:,}")
        print(f"✅ Person-skill records updated: {stats['person_skills_updated']:,}")
        
        if stats['errors']:
            print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
            print("   (See log for details)")
        
        print("=" * 70)
    
    extractor.close()


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
ABOUTME: Improved GitHub profile matching with lower thresholds and fuzzy matching
ABOUTME: Matches orphaned GitHub profiles to people using multiple strategies

Improved Matching Script
========================
Enhanced version of match_github_profiles.py with:
- Lower confidence threshold (85% → 70%) for auto-matching
- Fuzzy name matching using Levenshtein distance
- Better GitHub email → person_email matching
- Better company name matching with normalization
- Aggressive mode for maximum matches

Usage:
    python3 match_github_profiles_improved.py --limit 1000
    python3 match_github_profiles_improved.py --all  # Match all unmatched profiles
    python3 match_github_profiles_improved.py --aggressive  # Use lowest thresholds

Author: AI Assistant (Tier 1 Data Completion)
Date: October 24, 2025
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Dict, Optional, List, Tuple
from fuzzywuzzy import fuzz
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import load_env_file, get_db_connection
load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImprovedProfileMatcher:
    """
    Enhanced GitHub profile matcher with lower thresholds and fuzzy matching
    """
    
    def __init__(self, aggressive=False):
        self.conn = get_db_connection(use_pool=False)
        self.aggressive = aggressive
        
        # Confidence thresholds (lowered from defaults)
        if aggressive:
            self.EMAIL_MATCH_CONFIDENCE = 0.95
            self.LINKEDIN_MATCH_CONFIDENCE = 0.99
            self.NAME_COMPANY_MATCH_CONFIDENCE = 0.70  # Lowered from 0.85
            self.NAME_LOCATION_MATCH_CONFIDENCE = 0.65  # Lowered from 0.70
            self.FUZZY_NAME_MATCH_CONFIDENCE = 0.60    # New: fuzzy matching
            self.AUTO_MATCH_THRESHOLD = 0.60           # Lowered from 0.85 (very aggressive)
        else:
            self.EMAIL_MATCH_CONFIDENCE = 0.95
            self.LINKEDIN_MATCH_CONFIDENCE = 0.99
            self.NAME_COMPANY_MATCH_CONFIDENCE = 0.75  # Lowered from 0.85
            self.NAME_LOCATION_MATCH_CONFIDENCE = 0.70
            self.FUZZY_NAME_MATCH_CONFIDENCE = 0.65    # New: fuzzy matching
            self.AUTO_MATCH_THRESHOLD = 0.70           # Lowered from 0.85
        
        self.stats = {
            'total_processed': 0,
            'matched': 0,
            'high_confidence': 0,  # >= 0.85
            'medium_confidence': 0,  # 0.70-0.85
            'low_confidence': 0,  # 0.60-0.70
            'very_low_confidence': 0,  # < 0.60
            'skipped': 0,
            'by_strategy': {}
        }
    
    def normalize_company_name(self, company: str) -> str:
        """Normalize company name for better matching"""
        if not company:
            return ""
        
        # Remove common suffixes
        company = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corporation|Corp\.?|Limited)$', '', company, flags=re.IGNORECASE)
        
        # Remove special characters
        company = re.sub(r'[^\w\s]', '', company)
        
        # Lowercase and strip
        company = company.lower().strip()
        
        # Remove extra whitespace
        company = re.sub(r'\s+', ' ', company)
        
        return company
    
    def fuzzy_name_match(self, name1: str, name2: str) -> float:
        """
        Calculate fuzzy match score between two names
        
        Returns score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0
        
        # Token sort ratio handles word order differences
        # (e.g., "John Smith" vs "Smith John")
        token_sort_score = fuzz.token_sort_ratio(name1.lower(), name2.lower())
        
        # Partial ratio handles substring matches
        partial_score = fuzz.partial_ratio(name1.lower(), name2.lower())
        
        # Use the better of the two scores
        best_score = max(token_sort_score, partial_score)
        
        return best_score / 100.0
    
    def match_profile(self, profile: Dict) -> Tuple[Optional[str], float, str]:
        """
        Match a single GitHub profile to a person using multiple strategies
        
        Returns: (person_id, confidence, strategy) or (None, 0, 'no_match')
        """
        self.stats['total_processed'] += 1
        
        # Try each matching strategy in order of confidence
        strategies = [
            (self._match_by_email, 'email'),
            (self._match_by_linkedin, 'linkedin'),
            (self._match_by_name_company_exact, 'name_company_exact'),
            (self._match_by_name_company_fuzzy, 'name_company_fuzzy'),
            (self._match_by_name_location, 'name_location'),
            (self._match_by_fuzzy_name_company, 'fuzzy_name_company'),
        ]
        
        for strategy_func, strategy_name in strategies:
            person_id, confidence = strategy_func(profile)
            
            if person_id and confidence >= self.AUTO_MATCH_THRESHOLD:
                logger.debug(f"  ✅ Matched via {strategy_name} (confidence: {confidence:.2f})")
                
                # Track confidence levels
                if confidence >= 0.85:
                    self.stats['high_confidence'] += 1
                elif confidence >= 0.70:
                    self.stats['medium_confidence'] += 1
                elif confidence >= 0.60:
                    self.stats['low_confidence'] += 1
                else:
                    self.stats['very_low_confidence'] += 1
                
                # Track by strategy
                self.stats['by_strategy'][strategy_name] = self.stats['by_strategy'].get(strategy_name, 0) + 1
                
                self.stats['matched'] += 1
                return person_id, confidence, strategy_name
        
        # No match found
        self.stats['skipped'] += 1
        return None, 0.0, 'no_match'
    
    def _match_by_email(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by email address (highest confidence)"""
        email = profile.get('github_email')
        if not email or not email.strip():
            return None, 0.0
        
        cursor = self.conn.cursor()
        
        # Check person_email table
        cursor.execute("""
            SELECT person_id
            FROM person_email
            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            return result['person_id'], self.EMAIL_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def _match_by_linkedin(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by LinkedIn URL extracted from bio"""
        bio = profile.get('bio', '')
        if not bio:
            return None, 0.0
        
        # Extract LinkedIn URL from bio
        linkedin_patterns = [
            r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in linkedin_patterns:
            match = re.search(pattern, bio, re.IGNORECASE)
            if match:
                linkedin_username = match.group(1)
                
                cursor = self.conn.cursor()
                
                # Match against normalized_linkedin_url
                cursor.execute("""
                    SELECT person_id
                    FROM person
                    WHERE normalized_linkedin_url LIKE %s
                    LIMIT 1
                """, (f'%{linkedin_username}%',))
                
                result = cursor.fetchone()
                if result:
                    return result['person_id'], self.LINKEDIN_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def _match_by_name_company_exact(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by exact name + company"""
        name = profile.get('github_name')
        company = profile.get('github_company')
        
        if not name or not company:
            return None, 0.0
        
        # Clean company name (remove @ prefix if present)
        company = company.strip().lstrip('@')
        normalized_company = self.normalize_company_name(company)
        
        if not normalized_company:
            return None, 0.0
        
        # Parse name into parts
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return None, 0.0
        
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        cursor = self.conn.cursor()
        
        # Match on name + company in current employment
        cursor.execute("""
            SELECT p.person_id
            FROM person p
            JOIN employment e ON p.person_id = e.person_id
            JOIN company c ON e.company_id = c.company_id
            WHERE 
                LOWER(TRIM(p.first_name)) = LOWER(TRIM(%s))
                AND LOWER(TRIM(p.last_name)) = LOWER(TRIM(%s))
                AND (
                    LOWER(TRIM(c.company_name)) LIKE LOWER(TRIM(%s))
                    OR LOWER(TRIM(c.company_name)) LIKE LOWER(TRIM(%s))
                )
                AND e.end_date IS NULL
            LIMIT 1
        """, (first_name, last_name, f'%{normalized_company}%', f'{normalized_company}%'))
        
        result = cursor.fetchone()
        if result:
            return result['person_id'], self.NAME_COMPANY_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def _match_by_name_company_fuzzy(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by name + company with fuzzy company matching"""
        name = profile.get('github_name')
        company = profile.get('github_company')
        
        if not name or not company:
            return None, 0.0
        
        # Clean company name
        company = company.strip().lstrip('@')
        normalized_company = self.normalize_company_name(company)
        
        if not normalized_company or len(normalized_company) < 3:
            return None, 0.0
        
        # Parse name into parts
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return None, 0.0
        
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        cursor = self.conn.cursor()
        
        # Get candidates with matching name
        cursor.execute("""
            SELECT DISTINCT
                p.person_id,
                c.company_name
            FROM person p
            JOIN employment e ON p.person_id = e.person_id
            JOIN company c ON e.company_id = c.company_id
            WHERE 
                LOWER(TRIM(p.first_name)) = LOWER(TRIM(%s))
                AND LOWER(TRIM(p.last_name)) = LOWER(TRIM(%s))
                AND e.end_date IS NULL
            LIMIT 20
        """, (first_name, last_name))
        
        candidates = cursor.fetchall()
        
        # Fuzzy match company names
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            candidate_company = self.normalize_company_name(candidate['company_name'])
            score = self.fuzzy_name_match(normalized_company, candidate_company)
            
            if score > best_score and score >= 0.75:  # Require 75% fuzzy match
                best_score = score
                best_match = candidate['person_id']
        
        if best_match:
            # Adjust confidence based on fuzzy match score
            confidence = self.NAME_COMPANY_MATCH_CONFIDENCE * best_score
            return best_match, confidence
        
        return None, 0.0
    
    def _match_by_name_location(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by name + location"""
        name = profile.get('github_name')
        location = profile.get('location')
        
        if not name or not location:
            return None, 0.0
        
        # Parse name
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return None, 0.0
        
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        cursor = self.conn.cursor()
        
        # Match on name + location
        cursor.execute("""
            SELECT person_id
            FROM person
            WHERE 
                LOWER(TRIM(first_name)) = LOWER(TRIM(%s))
                AND LOWER(TRIM(last_name)) = LOWER(TRIM(%s))
                AND LOWER(TRIM(location)) LIKE LOWER(TRIM(%s))
            LIMIT 1
        """, (first_name, last_name, f'%{location}%'))
        
        result = cursor.fetchone()
        if result:
            return result['person_id'], self.NAME_LOCATION_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def _match_by_fuzzy_name_company(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match using fuzzy name matching + company"""
        name = profile.get('github_name')
        company = profile.get('github_company')
        
        if not name or not company:
            return None, 0.0
        
        # Clean company
        company = company.strip().lstrip('@')
        normalized_company = self.normalize_company_name(company)
        
        if not normalized_company or len(normalized_company) < 3:
            return None, 0.0
        
        cursor = self.conn.cursor()
        
        # Get candidates from same company
        cursor.execute("""
            SELECT DISTINCT
                p.person_id,
                p.full_name,
                p.first_name,
                p.last_name
            FROM person p
            JOIN employment e ON p.person_id = e.person_id
            JOIN company c ON e.company_id = c.company_id
            WHERE 
                (
                    LOWER(TRIM(c.company_name)) LIKE LOWER(TRIM(%s))
                    OR LOWER(TRIM(c.company_name)) LIKE LOWER(TRIM(%s))
                )
                AND e.end_date IS NULL
                AND p.full_name IS NOT NULL
            LIMIT 50
        """, (f'%{normalized_company}%', f'{normalized_company}%'))
        
        candidates = cursor.fetchall()
        
        # Fuzzy match names
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            full_name = candidate.get('full_name', '')
            if not full_name:
                # Construct from first + last
                first = candidate.get('first_name', '')
                last = candidate.get('last_name', '')
                full_name = f"{first} {last}".strip()
            
            if not full_name:
                continue
            
            score = self.fuzzy_name_match(name, full_name)
            
            if score > best_score and score >= 0.80:  # Require 80% fuzzy match for name
                best_score = score
                best_match = candidate['person_id']
        
        if best_match:
            # Lower confidence for fuzzy match
            confidence = self.FUZZY_NAME_MATCH_CONFIDENCE * best_score
            return best_match, confidence
        
        return None, 0.0
    
    def update_profile_match(self, profile_id: str, person_id: str, confidence: float, strategy: str) -> bool:
        """Update database with match"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE github_profile
                SET 
                    person_id = %s::uuid,
                    updated_at = NOW()
                WHERE github_profile_id = %s::uuid
            """, (person_id, profile_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating match: {e}")
            self.conn.rollback()
            return False
    
    def match_unmatched_profiles(self, limit: Optional[int] = None) -> Dict:
        """Match all unmatched GitHub profiles"""
        cursor = self.conn.cursor()
        
        # Get unmatched profiles with enriched data
        query = """
            SELECT 
                github_profile_id,
                github_username,
                github_name,
                github_email,
                github_company,
                location,
                bio,
                followers
            FROM github_profile
            WHERE 
                person_id IS NULL
                AND (
                    github_name IS NOT NULL
                    OR github_email IS NOT NULL
                    OR github_company IS NOT NULL
                )
            ORDER BY followers DESC NULLS LAST
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        profiles = cursor.fetchall()
        
        logger.info(f"\n🔗 Matching {len(profiles):,} unmatched profiles...")
        logger.info(f"   Mode: {'AGGRESSIVE' if self.aggressive else 'NORMAL'}")
        logger.info(f"   Auto-match threshold: {self.AUTO_MATCH_THRESHOLD:.2f}")
        
        matched_count = 0
        
        for i, profile in enumerate(profiles, 1):
            profile_dict = dict(profile)
            username = profile_dict.get('github_username', 'unknown')
            
            if i % 500 == 0:
                logger.info(f"  Progress: {i:,}/{len(profiles):,} ({i/len(profiles)*100:.1f}%) - Matched so far: {matched_count:,}")
            
            # Try to match
            person_id, confidence, strategy = self.match_profile(profile_dict)
            
            if person_id:
                # Update database with match
                success = self.update_profile_match(
                    profile_dict['github_profile_id'],
                    person_id,
                    confidence,
                    strategy
                )
                
                if success:
                    matched_count += 1
        
        logger.info(f"\n✅ Matched {matched_count:,} profiles")
        
        return self.stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Improved GitHub profile matching')
    parser.add_argument('--limit', type=int, default=None, help='Number of profiles to match')
    parser.add_argument('--all', action='store_true', help='Match all unmatched profiles')
    parser.add_argument('--aggressive', action='store_true', help='Use aggressive mode (lowest thresholds)')
    args = parser.parse_args()
    
    print("\n" + "🔗 " + "=" * 66)
    print("🔗  IMPROVED GitHub Profile Matching")
    print("🔗 " + "=" * 66)
    print("   Features:")
    print("   ✅ Lower confidence threshold (85% → 70%)")
    print("   ✅ Fuzzy name matching with Levenshtein distance")
    print("   ✅ Better company name normalization")
    print("   ✅ Enhanced email matching via person_email table")
    
    matcher = ImprovedProfileMatcher(aggressive=args.aggressive)
    
    # Match unmatched profiles
    limit = None if args.all else args.limit
    
    if args.all:
        print("\n⚠️  Matching ALL unmatched profiles (no limit)")
    elif limit:
        print(f"\n📋 Matching up to {limit:,} profiles")
    else:
        print("\n📋 Matching up to 10,000 profiles (default)")
        limit = 10000
    
    stats = matcher.match_unmatched_profiles(limit=limit)
    
    print("\n" + "📊 " + "=" * 66)
    print("📊  Matching Results")
    print("📊 " + "=" * 66)
    print(f"✅ Total matched: {stats['matched']:,}")
    print(f"   High confidence (>=85%): {stats['high_confidence']:,}")
    print(f"   Medium confidence (70-85%): {stats['medium_confidence']:,}")
    print(f"   Low confidence (60-70%): {stats['low_confidence']:,}")
    if stats['very_low_confidence'] > 0:
        print(f"   Very low confidence (<60%): {stats['very_low_confidence']:,}")
    print(f"⏭️  Skipped (no match): {stats.get('skipped', 0):,}")
    
    if stats['by_strategy']:
        print(f"\n📋 Matches by strategy:")
        for strategy, count in sorted(stats['by_strategy'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {strategy}: {count:,}")
    
    print("=" * 70)
    
    matcher.close()


if __name__ == '__main__':
    main()


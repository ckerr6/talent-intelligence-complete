"""
Profile Matcher - Match GitHub profiles to people

Uses multiple strategies to match profiles with confidence scoring
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from typing import Dict, Optional, List, Tuple
from config import Config, get_db_connection
from .config import GitHubAutomationConfig as AutoConfig
import logging
import re

logger = logging.getLogger(__name__)


class ProfileMatcher:
    """
    Matches GitHub profiles to people using multiple strategies
    
    Matching strategies (in order of confidence):
    1. Email match (highest confidence)
    2. LinkedIn URL match (very high confidence)
    3. Name + Company match (high confidence)
    4. Name + Location match (medium confidence)
    5. Fuzzy name + company match (lower confidence)
    
    Also creates new person records for high-quality unmatched profiles
    """
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        
        self.stats = {
            'total_processed': 0,
            'matched': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'no_match': 0,
            'new_people_created': 0
        }
    
    def match_profile(self, profile: Dict) -> Tuple[Optional[str], float, str]:
        """
        Match a single GitHub profile to a person
        
        Args:
            profile: GitHub profile dict
            
        Returns:
            Tuple of (person_id, confidence, strategy)
            or (None, 0, 'no_match') if no match
        """
        self.stats['total_processed'] += 1
        
        # Try each matching strategy in order of confidence
        strategies = [
            (self._match_by_email, 'email'),
            (self._match_by_linkedin, 'linkedin'),
            (self._match_by_name_company, 'name_company'),
            (self._match_by_name_location, 'name_location'),
        ]
        
        for strategy_func, strategy_name in strategies:
            person_id, confidence = strategy_func(profile)
            
            if person_id:
                logger.info(f"  ✅ Matched via {strategy_name} (confidence: {confidence:.2f})")
                
                # Track confidence levels
                if confidence >= 0.90:
                    self.stats['high_confidence'] += 1
                elif confidence >= 0.70:
                    self.stats['medium_confidence'] += 1
                else:
                    self.stats['low_confidence'] += 1
                
                self.stats['matched'] += 1
                return person_id, confidence, strategy_name
        
        # No match found
        self.stats['no_match'] += 1
        return None, 0.0, 'no_match'
    
    def _match_by_email(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by email address"""
        email = profile.get('github_email')
        if not email:
            return None, 0.0
        
        cursor = self.conn.cursor()
        
        # Check person_email table
        cursor.execute("""
            SELECT person_id
            FROM person_email
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            return result['person_id'], AutoConfig.EMAIL_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def _match_by_linkedin(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by LinkedIn URL extracted from bio"""
        bio = profile.get('bio', '')
        if not bio:
            return None, 0.0
        
        # Extract LinkedIn URL from bio
        linkedin_patterns = [
            r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
            r'linkedin\.com/company/([a-zA-Z0-9_-]+)'
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
                    return result['person_id'], AutoConfig.LINKEDIN_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def _match_by_name_company(self, profile: Dict) -> Tuple[Optional[str], float]:
        """Match by name + current company"""
        name = profile.get('github_name')
        company = profile.get('github_company')
        
        if not name or not company:
            return None, 0.0
        
        # Clean company name (remove @ prefix if present)
        company = company.strip().lstrip('@')
        
        # Parse name into parts
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return None, 0.0
        
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        cursor = self.conn.cursor()
        
        # Match on name + company in employment
        cursor.execute("""
            SELECT p.person_id
            FROM person p
            JOIN employment e ON p.person_id = e.person_id
            JOIN company c ON e.company_id = c.company_id
            WHERE 
                LOWER(p.first_name) = LOWER(%s)
                AND LOWER(p.last_name) = LOWER(%s)
                AND (
                    LOWER(c.company_name) LIKE LOWER(%s)
                    OR LOWER(c.company_name) LIKE LOWER(%s)
                )
                AND e.end_date IS NULL
            LIMIT 1
        """, (first_name, last_name, f'%{company}%', f'{company}%'))
        
        result = cursor.fetchone()
        if result:
            return result['person_id'], AutoConfig.NAME_COMPANY_MATCH_CONFIDENCE
        
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
                LOWER(first_name) = LOWER(%s)
                AND LOWER(last_name) = LOWER(%s)
                AND LOWER(location) LIKE LOWER(%s)
            LIMIT 1
        """, (first_name, last_name, f'%{location}%'))
        
        result = cursor.fetchone()
        if result:
            return result['person_id'], AutoConfig.NAME_LOCATION_MATCH_CONFIDENCE
        
        return None, 0.0
    
    def update_profile_match(
        self,
        profile_id: str,
        person_id: str,
        confidence: float,
        strategy: str
    ) -> bool:
        """
        Update database with match
        
        Args:
            profile_id: GitHub profile ID
            person_id: Person ID
            confidence: Match confidence score
            strategy: Matching strategy used
            
        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE github_profile
                SET 
                    person_id = %s,
                    updated_at = NOW()
                WHERE github_profile_id = %s
            """, (person_id, profile_id))
            
            self.conn.commit()
            
            # Log the match
            logger.info(f"  💾 Linked profile {profile_id[:8]}... to person {person_id[:8]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating match: {e}")
            self.conn.rollback()
            return False
    
    def match_unmatched_profiles(self, limit: Optional[int] = None) -> Dict:
        """
        Match all unmatched GitHub profiles
        
        Args:
            limit: Max profiles to process (None = all)
            
        Returns:
            Dict of statistics
        """
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
        
        logger.info(f"🔗 Matching {len(profiles):,} unmatched profiles...")
        
        matched_count = 0
        
        for i, profile in enumerate(profiles, 1):
            profile_dict = dict(profile)
            username = profile_dict.get('github_username', 'unknown')
            
            if i % 100 == 0:
                logger.info(f"  Progress: {i}/{len(profiles)} ({i/len(profiles)*100:.1f}%)")
            
            # Try to match
            person_id, confidence, strategy = self.match_profile(profile_dict)
            
            if person_id and confidence >= AutoConfig.AUTO_MATCH_THRESHOLD:
                # Update database with match
                success = self.update_profile_match(
                    profile_dict['github_profile_id'],
                    person_id,
                    confidence,
                    strategy
                )
                
                if success:
                    matched_count += 1
            elif person_id:
                # Low confidence - log for review
                logger.warning(f"  ⚠️  Low confidence match for {username}: {confidence:.2f} via {strategy}")
        
        logger.info(f"✅ Matched {matched_count:,} profiles")
        
        return self.stats
    
    def create_person_from_profile(self, profile: Dict) -> Optional[str]:
        """
        Create a new person record from a high-quality GitHub profile
        
        Only create if profile has:
        - Name
        - Email OR location
        - Bio (shows it's a real, active profile)
        
        Args:
            profile: GitHub profile dict
            
        Returns:
            New person_id or None
        """
        # Validation - need minimum data quality
        if not profile.get('github_name'):
            return None
        
        if not (profile.get('github_email') or profile.get('location')):
            return None
        
        if not profile.get('bio'):
            return None
        
        cursor = self.conn.cursor()
        
        try:
            # Parse name
            name = profile['github_name']
            name_parts = name.strip().split()
            first_name = name_parts[0] if name_parts else name
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            
            # Insert person
            cursor.execute("""
                INSERT INTO person (
                    full_name,
                    first_name,
                    last_name,
                    location,
                    headline,
                    description
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING person_id
            """, (
                name,
                first_name,
                last_name,
                profile.get('location'),
                f"GitHub: {profile.get('followers', 0)} followers",
                profile.get('bio')
            ))
            
            person_id = cursor.fetchone()['person_id']
            
            # Add email if we have it
            if profile.get('github_email'):
                cursor.execute("""
                    INSERT INTO person_email (person_id, email, email_type, is_primary, source)
                    VALUES (%s, %s, 'work', TRUE, 'github_enrichment')
                """, (person_id, profile['github_email']))
            
            # Link GitHub profile
            cursor.execute("""
                UPDATE github_profile
                SET person_id = %s
                WHERE github_profile_id = %s
            """, (person_id, profile['github_profile_id']))
            
            self.conn.commit()
            
            self.stats['new_people_created'] += 1
            logger.info(f"  ➕ Created new person: {name}")
            
            return person_id
            
        except Exception as e:
            logger.error(f"Error creating person: {e}")
            self.conn.rollback()
            return None
    
    def get_stats(self) -> Dict:
        """Get matching statistics"""
        return self.stats
    
    def log_stats(self):
        """Log matching statistics"""
        stats = self.get_stats()
        
        logger.info("=" * 60)
        logger.info("📊 Matching Statistics")
        logger.info("=" * 60)
        logger.info(f"Profiles processed: {stats['total_processed']:,}")
        logger.info(f"Matched: {stats['matched']:,}")
        logger.info(f"  High confidence: {stats['high_confidence']:,}")
        logger.info(f"  Medium confidence: {stats['medium_confidence']:,}")
        logger.info(f"  Low confidence: {stats['low_confidence']:,}")
        logger.info(f"No match: {stats['no_match']:,}")
        logger.info(f"New people created: {stats['new_people_created']:,}")
        logger.info("=" * 60)
    
    def close(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()


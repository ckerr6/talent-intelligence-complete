"""
Queue Manager for GitHub profile enrichment

Manages priority queue of profiles to enrich, with status tracking
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from config import Config, get_db_connection
from .config import GitHubAutomationConfig as AutoConfig
import logging

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages the queue of GitHub profiles for enrichment
    
    Features:
    - Priority-based queueing
    - Status tracking
    - Checkpoint/resume support
    - Statistics and monitoring
    """
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.stats = {
            'queued': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        }
    
    def calculate_priority(self, profile: Dict) -> int:
        """
        Calculate priority score for a profile
        
        Higher score = higher priority
        
        Factors:
        - Has email (easier to match)
        - Has location
        - High followers (more visible/important)
        - Already has some data (partial enrichment)
        """
        priority = 0
        
        # Has email
        if profile.get('github_email'):
            priority += AutoConfig.PRIORITY_HAS_EMAIL
        
        # Has location
        if profile.get('location'):
            priority += AutoConfig.PRIORITY_HAS_LOCATION
        
        # High followers
        followers = profile.get('followers', 0)
        if followers > 1000:
            priority += AutoConfig.PRIORITY_HIGH_FOLLOWERS
        elif followers > 100:
            priority += AutoConfig.PRIORITY_HIGH_FOLLOWERS // 2
        
        # Has some data (partial enrichment)
        if profile.get('bio') or profile.get('github_name') or profile.get('github_company'):
            priority += AutoConfig.PRIORITY_RECENT_ACTIVITY
        
        return priority
    
    def get_unenriched_profiles(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get profiles that need enrichment, ordered by priority
        
        A profile needs enrichment if:
        - Never enriched (last_enriched IS NULL)
        - Stale (last_enriched > STALE_DAYS ago)
        - Has minimal data (bio IS NULL, etc.)
        
        Returns:
            List of profile dicts with priority scores
        """
        cursor = self.conn.cursor()
        
        stale_date = datetime.now() - timedelta(days=AutoConfig.STALE_DAYS)
        
        query = """
            SELECT 
                github_profile_id,
                github_username,
                github_email,
                github_name,
                github_company,
                location,
                bio,
                followers,
                last_enriched,
                CASE
                    WHEN last_enriched IS NULL THEN 100
                    WHEN bio IS NULL THEN 90
                    WHEN github_email IS NULL THEN 80
                    ELSE 50
                END as base_priority
            FROM github_profile
            WHERE 
                (last_enriched IS NULL OR last_enriched < %s)
                AND github_username IS NOT NULL
            ORDER BY base_priority DESC, followers DESC NULLS LAST
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (stale_date,))
        
        profiles = []
        for row in cursor.fetchall():
            profile = dict(row)
            # Calculate dynamic priority
            profile['priority'] = self.calculate_priority(profile)
            profiles.append(profile)
        
        # Sort by calculated priority
        profiles.sort(key=lambda x: x['priority'], reverse=True)
        
        logger.info(f"📋 Found {len(profiles):,} profiles needing enrichment")
        
        return profiles
    
    def get_batch(self, batch_size: int = None) -> List[Dict]:
        """
        Get next batch of profiles to process
        
        Args:
            batch_size: Number of profiles to return
            
        Returns:
            List of profiles to enrich
        """
        if batch_size is None:
            batch_size = AutoConfig.BATCH_SIZE
        
        return self.get_unenriched_profiles(limit=batch_size)
    
    def mark_enriched(
        self,
        profile_id: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Mark a profile as enriched
        
        Args:
            profile_id: GitHub profile ID
            success: Whether enrichment succeeded
            error: Error message if failed
        """
        cursor = self.conn.cursor()
        
        if success:
            cursor.execute("""
                UPDATE github_profile
                SET 
                    last_enriched = NOW(),
                    updated_at = NOW()
                WHERE github_profile_id = %s
            """, (profile_id,))
            self.stats['completed'] += 1
        else:
            # Log failure but don't update last_enriched
            # This allows retry on next run
            logger.error(f"❌ Failed to enrich {profile_id}: {error}")
            self.stats['failed'] += 1
        
        self.conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get queue statistics"""
        cursor = self.conn.cursor()
        
        # Total profiles
        cursor.execute("SELECT COUNT(*) as count FROM github_profile")
        total = cursor.fetchone()['count']
        
        # Enriched profiles (have bio or recent enrichment)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM github_profile
            WHERE last_enriched IS NOT NULL
            OR bio IS NOT NULL
        """)
        enriched = cursor.fetchone()['count']
        
        # Stale profiles
        stale_date = datetime.now() - timedelta(days=AutoConfig.STALE_DAYS)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM github_profile
            WHERE last_enriched < %s
            OR last_enriched IS NULL
        """, (stale_date,))
        stale = cursor.fetchone()['count']
        
        # Matched profiles
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM github_profile
            WHERE person_id IS NOT NULL
        """)
        matched = cursor.fetchone()['count']
        
        return {
            'total': total,
            'enriched': enriched,
            'stale': stale,
            'matched': matched,
            'enrichment_coverage': (enriched / total * 100) if total > 0 else 0,
            'match_rate': (matched / total * 100) if total > 0 else 0,
            **self.stats
        }
    
    def log_statistics(self):
        """Log queue statistics"""
        stats = self.get_statistics()
        
        logger.info("=" * 60)
        logger.info("📊 Queue Statistics")
        logger.info("=" * 60)
        logger.info(f"Total profiles: {stats['total']:,}")
        logger.info(f"Enriched: {stats['enriched']:,} ({stats['enrichment_coverage']:.1f}%)")
        logger.info(f"Stale/Pending: {stats['stale']:,}")
        logger.info(f"Matched to people: {stats['matched']:,} ({stats['match_rate']:.1f}%)")
        logger.info("")
        logger.info(f"This session:")
        logger.info(f"  Completed: {stats['completed']:,}")
        logger.info(f"  Failed: {stats['failed']:,}")
        logger.info("=" * 60)
    
    def reset_failed(self, days_old: int = 7):
        """
        Reset failed enrichments older than N days for retry
        
        This allows us to retry profiles that failed due to temporary issues
        """
        cursor = self.conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        cursor.execute("""
            UPDATE github_profile
            SET last_enriched = NULL
            WHERE 
                last_enriched < %s
                AND (bio IS NULL OR github_email IS NULL)
        """, (cutoff_date,))
        
        reset_count = cursor.rowcount
        self.conn.commit()
        
        logger.info(f"🔄 Reset {reset_count:,} stale/failed profiles for retry")
        
        return reset_count
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


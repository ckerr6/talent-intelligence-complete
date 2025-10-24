"""
Monitoring Service for AI-First Recruiting

Runs background monitoring jobs to discover:
- New matches for saved searches
- Job changes for watched candidates
- GitHub activity on watched repos
- Rising talent signals

Creates notifications for all discoveries.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from .ai_research_assistant import AIResearchAssistant
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service for running AI monitoring jobs and creating notifications.
    
    Integrates AIResearchAssistant discoveries with NotificationService.
    """
    
    def __init__(self, db_connection):
        """
        Initialize monitoring service.
        
        Args:
            db_connection: PostgreSQL connection
        """
        self.db = db_connection
        self.research_assistant = AIResearchAssistant(db_connection)
        self.notification_service = NotificationService(db_connection)
    
    def run_daily_monitoring(self, user_id: str = 'default_user') -> Dict[str, Any]:
        """
        Run all monitoring tasks for a user.
        
        This is the main entry point called by the background scheduler.
        
        Args:
            user_id: User to monitor for (default: 'default_user' for MVP)
        
        Returns:
            Summary of monitoring results with counts
        """
        logger.info(f"Starting daily monitoring for user {user_id}")
        start_time = datetime.utcnow()
        
        try:
            # Get user's saved searches with auto_monitor enabled
            saved_searches = self._get_monitored_searches(user_id)
            
            # Get watched people and repos (for Phase 2 - from user preferences)
            watched_people = self._get_watched_people(user_id)
            watched_repos = self._get_watched_repos(user_id)
            
            # Run AI discovery
            results = {
                'user_id': user_id,
                'run_at': start_time.isoformat(),
                'new_matches': [],
                'job_changes': [],
                'github_activity': [],
                'rising_talent': [],
                'notifications_created': 0,
                'errors': []
            }
            
            # 1. Discover new matches for saved searches
            if saved_searches:
                try:
                    new_matches = self.research_assistant.discover_new_matches(
                        user_id=user_id,
                        search_patterns=saved_searches,
                        since_hours=24
                    )
                    results['new_matches'] = new_matches
                    
                    # Create notifications for each match
                    for match in new_matches:
                        notification_id = self.process_new_match(user_id, match)
                        if notification_id:
                            results['notifications_created'] += 1
                    
                    logger.info(f"Found {len(new_matches)} new matches")
                except Exception as e:
                    logger.error(f"Error in new match discovery: {e}")
                    results['errors'].append(f"New match discovery: {str(e)}")
            
            # 2. Monitor job changes
            if watched_people:
                try:
                    job_changes = self.research_assistant.monitor_job_changes(
                        watched_people=watched_people,
                        since_hours=168  # 1 week
                    )
                    results['job_changes'] = job_changes
                    
                    # Create notifications for job changes
                    for change in job_changes:
                        notification_id = self.process_job_change(user_id, change)
                        if notification_id:
                            results['notifications_created'] += 1
                    
                    logger.info(f"Found {len(job_changes)} job changes")
                except Exception as e:
                    logger.error(f"Error in job change monitoring: {e}")
                    results['errors'].append(f"Job change monitoring: {str(e)}")
            
            # 3. Monitor GitHub activity
            if watched_repos:
                try:
                    github_activity = self.research_assistant.monitor_github_activity(
                        watched_repos=watched_repos,
                        since_hours=168  # 1 week
                    )
                    results['github_activity'] = github_activity
                    
                    # Create notifications for GitHub activity
                    for activity in github_activity:
                        notification_id = self.process_github_activity(user_id, activity)
                        if notification_id:
                            results['notifications_created'] += 1
                    
                    logger.info(f"Found {len(github_activity)} GitHub activities")
                except Exception as e:
                    logger.error(f"Error in GitHub activity monitoring: {e}")
                    results['errors'].append(f"GitHub monitoring: {str(e)}")
            
            # 4. Identify rising talent
            try:
                rising_talent = self.research_assistant.identify_rising_talent(
                    min_github_growth=10,
                    since_days=90
                )
                results['rising_talent'] = rising_talent
                
                # Create notifications for rising talent
                for talent in rising_talent[:5]:  # Top 5 only to avoid spam
                    notification_id = self.process_rising_talent(user_id, talent)
                    if notification_id:
                        results['notifications_created'] += 1
                
                logger.info(f"Identified {len(rising_talent)} rising talents")
            except Exception as e:
                logger.error(f"Error in rising talent identification: {e}")
                results['errors'].append(f"Rising talent: {str(e)}")
            
            # Update last_monitored_at for saved searches
            self._update_search_monitoring_time(user_id, saved_searches)
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Monitoring complete for user {user_id}: "
                f"{results['notifications_created']} notifications created "
                f"in {elapsed:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Fatal error in daily monitoring: {e}")
            raise
    
    def process_new_match(
        self,
        user_id: str,
        match_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create notification for a new match.
        
        Args:
            user_id: User ID
            match_data: Match data from AIResearchAssistant
        
        Returns:
            Notification ID if created, None otherwise
        """
        try:
            # Extract data
            person_id = match_data.get('person_id')
            person_name = match_data.get('person_name', 'Unknown')
            match_score = match_data.get('match_score', 0)
            pattern_name = match_data.get('pattern_name', 'Your search')
            reason = match_data.get('reason', '')
            headline = match_data.get('headline', '')
            
            # Determine priority based on match score
            if match_score >= 90:
                priority = 'high'
            elif match_score >= 80:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Create notification
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type='new_match',
                priority=priority,
                title=f"🎯 New Match: {person_name} ({match_score}% match)",
                message=f"Found a {match_score}% match for '{pattern_name}': {person_name} {headline}",
                person_id=person_id,
                person_name=person_name,
                action_url=f"/profile/{person_id}",
                action_label='View Profile',
                metadata={
                    'match_score': match_score,
                    'search_name': pattern_name,
                    'reason': reason,
                    'discovered_at': match_data.get('discovered_at')
                }
            )
            
            return notification['notification_id']
            
        except Exception as e:
            logger.error(f"Error processing new match: {e}")
            return None
    
    def process_job_change(
        self,
        user_id: str,
        change_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create notification for a job change.
        
        Args:
            user_id: User ID
            change_data: Job change data from AIResearchAssistant
        
        Returns:
            Notification ID if created, None otherwise
        """
        try:
            person_id = change_data.get('person_id')
            person_name = change_data.get('person_name', 'Unknown')
            new_company = change_data.get('new_company', 'a new company')
            new_title = change_data.get('new_title', '')
            
            # Job changes are always high priority (good time to reach out)
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type='job_change',
                priority='urgent',
                title=f"🔔 {person_name} joined {new_company}",
                message=f"{person_name} just started as {new_title} at {new_company}. Perfect time to reach out!",
                person_id=person_id,
                person_name=person_name,
                action_url=f"/profile/{person_id}",
                action_label='Reach Out',
                metadata={
                    'new_company': new_company,
                    'new_title': new_title,
                    'detected_at': change_data.get('detected_at'),
                    'suggestion': change_data.get('action_suggestion')
                }
            )
            
            return notification['notification_id']
            
        except Exception as e:
            logger.error(f"Error processing job change: {e}")
            return None
    
    def process_github_activity(
        self,
        user_id: str,
        activity_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create notification for GitHub activity.
        
        Args:
            user_id: User ID
            activity_data: GitHub activity data from AIResearchAssistant
        
        Returns:
            Notification ID if created, None otherwise
        """
        try:
            person_id = activity_data.get('person_id')
            person_name = activity_data.get('person_name', 'Unknown')
            repo_name = activity_data.get('repo_name', '')
            merged_prs = activity_data.get('merged_prs', 0)
            relevance = activity_data.get('relevance', 'medium')
            
            priority = 'high' if relevance == 'high' else 'medium'
            
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type='github_activity',
                priority=priority,
                title=f"🚀 New contributor to {repo_name}",
                message=f"{person_name} just merged {merged_prs} PRs to {repo_name}. They might be a good fit!",
                person_id=person_id,
                person_name=person_name,
                action_url=f"/profile/{person_id}",
                action_label='View Profile',
                metadata={
                    'repo_name': repo_name,
                    'merged_prs': merged_prs,
                    'stars': activity_data.get('stars'),
                    'relevance': relevance,
                    'detected_at': activity_data.get('detected_at')
                }
            )
            
            return notification['notification_id']
            
        except Exception as e:
            logger.error(f"Error processing GitHub activity: {e}")
            return None
    
    def process_rising_talent(
        self,
        user_id: str,
        talent_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create notification for rising talent.
        
        Args:
            user_id: User ID
            talent_data: Rising talent data from AIResearchAssistant
        
        Returns:
            Notification ID if created, None otherwise
        """
        try:
            person_id = talent_data.get('person_id')
            person_name = talent_data.get('person_name', 'Unknown')
            total_prs = talent_data.get('total_prs', 0)
            recent_contributions = talent_data.get('recent_contributions', 0)
            reason = talent_data.get('reason', '')
            
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type='rising_talent',
                priority='medium',
                title=f"⭐ Rising Talent: {person_name}",
                message=f"{person_name} has {total_prs} merged PRs with rapid growth. {reason}",
                person_id=person_id,
                person_name=person_name,
                action_url=f"/profile/{person_id}",
                action_label='Add to List',
                metadata={
                    'total_prs': total_prs,
                    'recent_contributions': recent_contributions,
                    'growth_indicator': talent_data.get('growth_indicator'),
                    'reason': reason,
                    'detected_at': talent_data.get('detected_at')
                }
            )
            
            return notification['notification_id']
            
        except Exception as e:
            logger.error(f"Error processing rising talent: {e}")
            return None
    
    # Helper methods
    
    def _get_monitored_searches(self, user_id: str) -> List[Dict[str, Any]]:
        """Get saved searches with auto_monitor enabled."""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    search_id, name, filters, 
                    min_match_score, monitor_frequency
                FROM saved_searches
                WHERE user_id = %s
                AND auto_monitor = TRUE
            """, (user_id,))
            
            searches = []
            for row in cursor.fetchall():
                search = dict(row)
                # Parse filters JSON and add search name
                filters = search['filters']
                filters['name'] = search['name']
                filters['min_match_score'] = search['min_match_score']
                searches.append(filters)
            
            return searches
            
        except Exception as e:
            logger.error(f"Error getting monitored searches: {e}")
            return []
        finally:
            cursor.close()
    
    def _get_watched_people(self, user_id: str) -> List[str]:
        """Get list of person IDs user is watching (from candidate lists)."""
        cursor = self.db.cursor()
        
        try:
            # Get people from all candidate lists for this user
            cursor.execute("""
                SELECT DISTINCT clm.person_id
                FROM candidate_list_members clm
                JOIN candidate_lists cl ON clm.list_id = cl.list_id
                WHERE cl.user_id = %s
            """, (user_id,))
            
            person_ids = [str(row['person_id']) for row in cursor.fetchall()]
            return person_ids
            
        except Exception as e:
            logger.error(f"Error getting watched people: {e}")
            return []
        finally:
            cursor.close()
    
    def _get_watched_repos(self, user_id: str) -> List[str]:
        """Get list of repos user is watching (from preferences - Phase 2)."""
        # For MVP, return empty list
        # In Phase 2, we'll let users add repos to watch
        return []
    
    def _update_search_monitoring_time(
        self,
        user_id: str,
        searches: List[Dict[str, Any]]
    ):
        """Update last_monitored_at timestamp for searches."""
        if not searches:
            return
        
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                UPDATE saved_searches
                SET last_monitored_at = NOW()
                WHERE user_id = %s
                AND auto_monitor = TRUE
            """, (user_id,))
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating search monitoring time: {e}")
            self.db.rollback()
        finally:
            cursor.close()


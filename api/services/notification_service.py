"""
Notification Service for AI-First Recruiting

Manages creation, retrieval, and updates of AI-generated notifications
for talent discoveries, job changes, and rising talent signals.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import json

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing AI-generated notifications.
    
    Handles:
    - Creating notifications from AI discoveries
    - Retrieving notifications for users
    - Marking notifications as read/actioned
    - Batch operations
    """
    
    def __init__(self, db_connection):
        """
        Initialize notification service.
        
        Args:
            db_connection: PostgreSQL connection from dependency injection
        """
        self.db = db_connection
    
    def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        person_id: Optional[str] = None,
        person_name: Optional[str] = None,
        priority: str = 'medium',
        action_url: Optional[str] = None,
        action_label: str = 'View Profile',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new notification.
        
        Args:
            user_id: User to notify
            notification_type: Type of notification (new_match, job_change, etc.)
            title: Notification title
            message: Notification message
            person_id: Related person (optional)
            person_name: Person's name for quick display
            priority: low, medium, high, or urgent
            action_url: URL to navigate to on click
            action_label: Button label (default: "View Profile")
            metadata: Additional data (match_score, reason, etc.)
        
        Returns:
            Created notification dict with notification_id
        """
        cursor = self.db.cursor()
        
        try:
            # Prepare metadata
            meta = metadata or {}
            meta_json = json.dumps(meta)
            
            # Insert notification
            cursor.execute("""
                INSERT INTO notifications (
                    user_id, notification_type, priority,
                    title, message,
                    person_id, person_name,
                    action_url, action_label,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING 
                    notification_id, user_id, notification_type, priority,
                    title, message, person_id, person_name,
                    action_url, action_label, metadata,
                    is_read, is_dismissed, is_actioned,
                    created_at, read_at, actioned_at
            """, (
                user_id, notification_type, priority,
                title, message,
                person_id, person_name,
                action_url, action_label,
                meta_json
            ))
            
            result = cursor.fetchone()
            self.db.commit()
            
            notification = dict(result)
            
            logger.info(f"Created notification: {notification_type} for user {user_id}")
            
            return notification
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise
        finally:
            cursor.close()
    
    def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: If True, only return unread notifications
            notification_type: Filter by type (optional)
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of notification dicts
        """
        cursor = self.db.cursor()
        
        try:
            # Build query
            query = """
                SELECT 
                    notification_id, user_id, notification_type, priority,
                    title, message, person_id, person_name,
                    action_url, action_label, metadata,
                    is_read, is_dismissed, is_actioned,
                    created_at, read_at, actioned_at
                FROM notifications
                WHERE user_id = %s
                AND is_dismissed = FALSE
            """
            params = [user_id]
            
            if unread_only:
                query += " AND is_read = FALSE"
            
            if notification_type:
                query += " AND notification_type = %s"
                params.append(notification_type)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            notifications = [dict(row) for row in results]
            
            logger.debug(f"Retrieved {len(notifications)} notifications for user {user_id}")
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error retrieving notifications: {e}")
            raise
        finally:
            cursor.close()
    
    def mark_as_read(
        self,
        notification_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: Optional user ID for verification
        
        Returns:
            True if successful, False if notification not found
        """
        cursor = self.db.cursor()
        
        try:
            query = """
                UPDATE notifications
                SET is_read = TRUE, read_at = NOW()
                WHERE notification_id = %s
            """
            params = [notification_id]
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            cursor.execute(query, params)
            self.db.commit()
            
            success = cursor.rowcount > 0
            
            if success:
                logger.debug(f"Marked notification {notification_id} as read")
            else:
                logger.warning(f"Notification {notification_id} not found")
            
            return success
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification as read: {e}")
            raise
        finally:
            cursor.close()
    
    def mark_all_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of notifications marked as read
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                UPDATE notifications
                SET is_read = TRUE, read_at = NOW()
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            
            self.db.commit()
            count = cursor.rowcount
            
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking all notifications as read: {e}")
            raise
        finally:
            cursor.close()
    
    def dismiss_notification(
        self,
        notification_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Dismiss a notification (soft delete).
        
        Args:
            notification_id: Notification ID
            user_id: Optional user ID for verification
        
        Returns:
            True if successful, False if notification not found
        """
        cursor = self.db.cursor()
        
        try:
            query = """
                UPDATE notifications
                SET is_dismissed = TRUE
                WHERE notification_id = %s
            """
            params = [notification_id]
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            cursor.execute(query, params)
            self.db.commit()
            
            success = cursor.rowcount > 0
            
            if success:
                logger.debug(f"Dismissed notification {notification_id}")
            else:
                logger.warning(f"Notification {notification_id} not found")
            
            return success
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error dismissing notification: {e}")
            raise
        finally:
            cursor.close()
    
    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Count of unread notifications
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM notifications
                WHERE user_id = %s
                AND is_read = FALSE
                AND is_dismissed = FALSE
            """, (user_id,))
            
            count = cursor.fetchone()[0]
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            raise
        finally:
            cursor.close()
    
    def mark_as_actioned(
        self,
        notification_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Mark a notification as actioned (user took action on it).
        
        Args:
            notification_id: Notification ID
            user_id: Optional user ID for verification
        
        Returns:
            True if successful, False if notification not found
        """
        cursor = self.db.cursor()
        
        try:
            query = """
                UPDATE notifications
                SET is_actioned = TRUE, actioned_at = NOW()
                WHERE notification_id = %s
            """
            params = [notification_id]
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            cursor.execute(query, params)
            self.db.commit()
            
            success = cursor.rowcount > 0
            
            if success:
                logger.debug(f"Marked notification {notification_id} as actioned")
            
            return success
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification as actioned: {e}")
            raise
        finally:
            cursor.close()
    
    def get_notification_stats(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get notification statistics for a user.
        
        Args:
            user_id: User ID
            days: Look back period in days
        
        Returns:
            Stats dict with counts by type, read rate, action rate, etc.
        """
        cursor = self.db.cursor()
        
        try:
            # Get counts by type
            cursor.execute("""
                SELECT 
                    notification_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_read THEN 1 ELSE 0 END) as read_count,
                    SUM(CASE WHEN is_actioned THEN 1 ELSE 0 END) as actioned_count
                FROM notifications
                WHERE user_id = %s
                AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY notification_type
            """, (user_id, days))
            
            type_stats = {}
            total_notifications = 0
            total_read = 0
            total_actioned = 0
            
            for row in cursor.fetchall():
                type_name = row['notification_type']
                total = row['total']
                read_count = row['read_count']
                actioned_count = row['actioned_count']
                
                type_stats[type_name] = {
                    'total': total,
                    'read': read_count,
                    'actioned': actioned_count,
                    'read_rate': read_count / total if total > 0 else 0,
                    'action_rate': actioned_count / total if total > 0 else 0
                }
                
                total_notifications += total
                total_read += read_count
                total_actioned += actioned_count
            
            return {
                'period_days': days,
                'total_notifications': total_notifications,
                'total_read': total_read,
                'total_actioned': total_actioned,
                'overall_read_rate': total_read / total_notifications if total_notifications > 0 else 0,
                'overall_action_rate': total_actioned / total_notifications if total_notifications > 0 else 0,
                'by_type': type_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            raise
        finally:
            cursor.close()


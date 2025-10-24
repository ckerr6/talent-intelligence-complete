"""
Notifications API Router

Endpoints for retrieving and managing AI-generated notifications.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from api.dependencies import get_db
from api.services.notification_service import NotificationService
from api.services.background_scheduler import trigger_monitoring_now, get_scheduler_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Pydantic models for request/response

class NotificationResponse(BaseModel):
    """Notification response model"""
    notification_id: str
    user_id: str
    notification_type: str
    priority: str
    title: str
    message: str
    person_id: Optional[str]
    person_name: Optional[str]
    action_url: Optional[str]
    action_label: str
    metadata: dict
    is_read: bool
    is_dismissed: bool
    is_actioned: bool
    created_at: datetime
    read_at: Optional[datetime]
    actioned_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications with pagination"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    offset: int
    limit: int


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    period_days: int
    total_notifications: int
    total_read: int
    total_actioned: int
    overall_read_rate: float
    overall_action_rate: float
    by_type: dict


# Default user ID for MVP (single-user)
DEFAULT_USER_ID = "default_user"


# Endpoints

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db=Depends(get_db)
):
    """
    Get notifications for the current user.
    
    Query parameters:
    - unread_only: If true, only return unread notifications
    - notification_type: Filter by type (new_match, job_change, etc.)
    - limit: Max results per page (1-100)
    - offset: Pagination offset
    
    Returns list of notifications with pagination metadata.
    """
    try:
        service = NotificationService(db)
        
        # Get notifications
        notifications = service.get_notifications(
            user_id=DEFAULT_USER_ID,
            unread_only=unread_only,
            notification_type=notification_type,
            limit=limit,
            offset=offset
        )
        
        # Get total unread count
        unread_count = service.get_unread_count(DEFAULT_USER_ID)
        
        # Convert to response models
        notification_responses = [
            NotificationResponse(**notif) for notif in notifications
        ]
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=len(notifications),  # Note: This is page total, not overall total
            unread_count=unread_count,
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(db=Depends(get_db)):
    """
    Get count of unread notifications for the current user.
    
    Returns simple count for badge display.
    """
    try:
        service = NotificationService(db)
        count = service.get_unread_count(DEFAULT_USER_ID)
        
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db=Depends(get_db)
):
    """
    Mark a notification as read.
    
    Sets is_read=true and records read_at timestamp.
    """
    try:
        service = NotificationService(db)
        success = service.mark_as_read(notification_id, DEFAULT_USER_ID)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "notification_id": notification_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_read(db=Depends(get_db)):
    """
    Mark all notifications as read for the current user.
    
    Returns count of notifications marked as read.
    """
    try:
        service = NotificationService(db)
        count = service.mark_all_read(DEFAULT_USER_ID)
        
        return {
            "success": True,
            "count": count,
            "message": f"Marked {count} notifications as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def dismiss_notification(
    notification_id: str,
    db=Depends(get_db)
):
    """
    Dismiss a notification (soft delete).
    
    Sets is_dismissed=true. Dismissed notifications won't appear in queries.
    """
    try:
        service = NotificationService(db)
        success = service.dismiss_notification(notification_id, DEFAULT_USER_ID)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "notification_id": notification_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/action")
async def mark_notification_actioned(
    notification_id: str,
    db=Depends(get_db)
):
    """
    Mark a notification as actioned.
    
    Use this when user takes action on the notification
    (e.g., clicks through to profile, adds to list).
    """
    try:
        service = NotificationService(db)
        success = service.mark_as_actioned(notification_id, DEFAULT_USER_ID)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "notification_id": notification_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as actioned: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    days: int = Query(7, ge=1, le=90, description="Look back period in days"),
    db=Depends(get_db)
):
    """
    Get notification statistics for the current user.
    
    Returns counts by type, read rates, action rates, etc.
    """
    try:
        service = NotificationService(db)
        stats = service.get_notification_stats(DEFAULT_USER_ID, days)
        
        return NotificationStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin/Testing endpoints

@router.post("/trigger-monitoring")
async def trigger_monitoring_manual(db=Depends(get_db)):
    """
    Manually trigger the monitoring job (for testing/debugging).
    
    WARNING: This should be protected with authentication in production.
    """
    try:
        logger.info("Manual monitoring trigger requested via API")
        results = trigger_monitoring_now()
        
        return {
            "success": True,
            "results": results,
            "message": f"Monitoring complete: {results['notifications_created']} notifications created"
        }
        
    except Exception as e:
        logger.error(f"Error triggering monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
async def get_scheduler_status_endpoint():
    """
    Get background scheduler status.
    
    Shows whether scheduler is running and when jobs will run next.
    """
    try:
        status = get_scheduler_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


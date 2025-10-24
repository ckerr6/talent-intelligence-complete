"""
Notification Models

Database models for AI-powered notifications.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Notification(Base):
    __tablename__ = "notifications"
    
    notification_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String, nullable=False)  # new_match, job_change, github_activity, rising_talent
    priority = Column(String, default='medium')  # low, medium, high, urgent
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Related entity
    person_id = Column(String, nullable=True, index=True)
    person_name = Column(String, nullable=True)
    
    # Action details
    action_url = Column(String, nullable=True)
    action_label = Column(String, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default={})  # Additional context (match_score, reason, etc.)
    
    # State
    is_read = Column(Boolean, default=False, index=True)
    is_dismissed = Column(Boolean, default=False)
    is_actioned = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    actioned_at = Column(DateTime, nullable=True)
    
    # Optional: Link to user (if you have users table)
    # user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    preference_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    
    # Email notifications
    email_enabled = Column(Boolean, default=True)
    email_frequency = Column(String, default='immediate')  # immediate, daily_digest, weekly_digest
    
    # Notification type preferences
    new_matches_enabled = Column(Boolean, default=True)
    job_changes_enabled = Column(Boolean, default=True)
    github_activity_enabled = Column(Boolean, default=True)
    rising_talent_enabled = Column(Boolean, default=True)
    network_changes_enabled = Column(Boolean, default=True)
    
    # Thresholds
    min_match_score = Column(Integer, default=70)  # Only notify for matches above this score
    min_github_prs = Column(Integer, default=5)  # Minimum PRs for GitHub activity alerts
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Integer, default=22)  # 10 PM
    quiet_hours_end = Column(Integer, default=8)  # 8 AM
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SavedSearch(Base):
    __tablename__ = "saved_searches"
    
    search_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Search details
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Search criteria
    filters = Column(JSON, nullable=False)  # Companies, locations, skills, etc.
    
    # Monitoring settings
    monitor_enabled = Column(Boolean, default=False)  # Auto-monitor for new matches
    notification_enabled = Column(Boolean, default=True)
    
    # Stats
    last_result_count = Column(Integer, default=0)
    last_checked_at = Column(DateTime, nullable=True)
    times_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


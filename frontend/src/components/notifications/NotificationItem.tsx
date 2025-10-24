/**
 * NotificationItem Component
 * 
 * Individual notification card with icon, title, message, and actions.
 */

import { useNavigate } from 'react-router-dom';
import { Target, Bell, Github, Star, Users, Sparkles, X } from 'lucide-react';
import type { Notification } from '../../types/notifications';
import { notificationService } from '../../services/notificationService';

interface NotificationItemProps {
  notification: Notification;
  onRead?: (notificationId: string) => void;
  onDismiss?: (notificationId: string) => void;
  compact?: boolean;
}

const NOTIFICATION_ICONS: Record<string, any> = {
  new_match: Target,
  job_change: Bell,
  github_activity: Github,
  rising_talent: Star,
  network_connection: Users,
  ai_suggestion: Sparkles,
};

const NOTIFICATION_COLORS: Record<string, string> = {
  new_match: 'text-indigo-600 bg-indigo-50',
  job_change: 'text-orange-600 bg-orange-50',
  github_activity: 'text-purple-600 bg-purple-50',
  rising_talent: 'text-yellow-600 bg-yellow-50',
  network_connection: 'text-blue-600 bg-blue-50',
  ai_suggestion: 'text-pink-600 bg-pink-50',
};

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'border-l-4 border-red-500',
  high: 'border-l-4 border-orange-500',
  medium: 'border-l-4 border-blue-500',
  low: 'border-l-4 border-gray-300',
};

export default function NotificationItem({
  notification,
  onRead,
  onDismiss,
  compact = false
}: NotificationItemProps) {
  const navigate = useNavigate();

  const Icon = NOTIFICATION_ICONS[notification.notification_type] || Sparkles;
  const iconColorClass = NOTIFICATION_COLORS[notification.notification_type] || 'text-gray-600 bg-gray-50';
  const priorityClass = PRIORITY_COLORS[notification.priority] || '';

  const handleClick = async () => {
    // Mark as read
    if (!notification.is_read) {
      try {
        await notificationService.markAsRead(notification.notification_id);
        onRead?.(notification.notification_id);
      } catch (error) {
        console.error('Error marking notification as read:', error);
      }
    }

    // Mark as actioned
    try {
      await notificationService.markAsActioned(notification.notification_id);
    } catch (error) {
      console.error('Error marking notification as actioned:', error);
    }

    // Navigate to action URL
    if (notification.action_url) {
      navigate(notification.action_url);
    }
  };

  const handleDismiss = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    try {
      await notificationService.dismiss(notification.notification_id);
      onDismiss?.(notification.notification_id);
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
  };

  const timeAgo = getTimeAgo(notification.created_at);

  return (
    <div
      className={`
        group relative bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer
        ${!notification.is_read ? 'bg-blue-50' : ''}
        ${priorityClass}
        ${compact ? 'p-3' : 'p-4'}
      `}
      onClick={handleClick}
    >
      {/* Dismiss Button */}
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-100"
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4 text-gray-400 hover:text-gray-600" />
      </button>

      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={`flex-shrink-0 p-2 rounded-full ${iconColorClass}`}>
          <Icon className="w-5 h-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h4 className={`font-semibold text-gray-900 ${compact ? 'text-sm' : 'text-base'} mb-1`}>
            {notification.title}
          </h4>

          {/* Message */}
          <p className={`text-gray-600 ${compact ? 'text-xs' : 'text-sm'} mb-2`}>
            {notification.message}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">{timeAgo}</span>
            
            {notification.action_label && (
              <span className="text-xs text-indigo-600 font-medium">
                {notification.action_label} →
              </span>
            )}
          </div>

          {/* Metadata badges (if not compact) */}
          {!compact && notification.metadata && (
            <div className="mt-2 flex flex-wrap gap-2">
              {notification.metadata.match_score && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {notification.metadata.match_score}% match
                </span>
              )}
              {notification.metadata.merged_prs && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  {notification.metadata.merged_prs} PRs
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Unread indicator */}
      {!notification.is_read && (
        <div className="absolute top-1/2 -left-1 w-2 h-2 bg-blue-600 rounded-full -translate-y-1/2" />
      )}
    </div>
  );
}

// Helper function to format time ago
function getTimeAgo(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  
  return then.toLocaleDateString();
}


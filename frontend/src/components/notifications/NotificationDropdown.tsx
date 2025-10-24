/**
 * NotificationDropdown Component
 * 
 * Dropdown panel showing recent notifications.
 * Appears when clicking the notification bell.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCheck, Eye } from 'lucide-react';
import { notificationService } from '../../services/notificationService';
import type { Notification } from '../../types/notifications';
import NotificationItem from './NotificationItem';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';

interface NotificationDropdownProps {
  onClose: () => void;
}

export default function NotificationDropdown({ onClose }: NotificationDropdownProps) {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await notificationService.getNotifications({
        limit: 10,  // Show recent 10 notifications
        offset: 0
      });
      
      setNotifications(response.notifications);
    } catch (err) {
      console.error('Error loading notifications:', err);
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleRead = (notificationId: string) => {
    // Update local state
    setNotifications(prev =>
      prev.map(n =>
        n.notification_id === notificationId
          ? { ...n, is_read: true }
          : n
      )
    );
  };

  const handleDismiss = (notificationId: string) => {
    // Remove from local state
    setNotifications(prev =>
      prev.filter(n => n.notification_id !== notificationId)
    );
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      
      // Update local state
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      );
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  const handleViewAll = () => {
    onClose();
    navigate('/notifications');
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <p className="text-sm text-gray-600">
                {unreadCount} unread
              </p>
            )}
          </div>
          
          {notifications.length > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-md transition-colors"
              title="Mark all as read"
            >
              <CheckCheck className="w-4 h-4" />
              <span>Mark all read</span>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner message="Loading notifications..." />
          </div>
        ) : error ? (
          <div className="px-4 py-12">
            <EmptyState
              icon={<Eye className="w-8 h-8" />}
              title="Error loading notifications"
              description={error}
            />
          </div>
        ) : notifications.length === 0 ? (
          <div className="px-4 py-12">
            <EmptyState
              icon={<Eye className="w-8 h-8" />}
              title="No notifications"
              description="You're all caught up! New discoveries will appear here."
            />
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {notifications.map((notification) => (
              <div key={notification.notification_id} className="px-4 py-3 hover:bg-gray-50">
                <NotificationItem
                  notification={notification}
                  onRead={handleRead}
                  onDismiss={handleDismiss}
                  compact
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleViewAll}
            className="w-full text-center text-sm text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
          >
            View All Notifications →
          </button>
        </div>
      )}
    </div>
  );
}


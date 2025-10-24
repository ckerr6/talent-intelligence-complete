/**
 * NotificationsPage Component
 * 
 * Full notification center with tabs, filters, and bulk actions.
 */

import { useState, useEffect } from 'react';
import { Bell, CheckCheck, Eye, Target, Github, Star, Users } from 'lucide-react';
import { notificationService } from '../services/notificationService';
import type { Notification, NotificationType } from '../types/notifications';
import NotificationItem from '../components/notifications/NotificationItem';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EmptyState from '../components/common/EmptyState';
import Button from '../components/common/Button';

const NOTIFICATION_TABS: Array<{ id: string; label: string; type?: NotificationType; icon: any }> = [
  { id: 'all', label: 'All', icon: Bell },
  { id: 'new_match', label: 'New Matches', type: 'new_match', icon: Target },
  { id: 'job_change', label: 'Job Changes', type: 'job_change', icon: Bell },
  { id: 'github_activity', label: 'GitHub Activity', type: 'github_activity', icon: Github },
  { id: 'rising_talent', label: 'Rising Talent', type: 'rising_talent', icon: Star },
  { id: 'network', label: 'Network', type: 'network_connection', icon: Users },
];

export default function NotificationsPage() {
  const [activeTab, setActiveTab] = useState('all');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const pageSize = 50;

  useEffect(() => {
    loadNotifications();
  }, [activeTab, unreadOnly, page]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);

      const activeTabData = NOTIFICATION_TABS.find(t => t.id === activeTab);
      
      const response = await notificationService.getNotifications({
        unreadOnly,
        notificationType: activeTabData?.type,
        limit: pageSize,
        offset: page * pageSize,
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
    setNotifications(prev =>
      prev.map(n =>
        n.notification_id === notificationId
          ? { ...n, is_read: true }
          : n
      )
    );
  };

  const handleDismiss = (notificationId: string) => {
    setNotifications(prev =>
      prev.filter(n => n.notification_id !== notificationId)
    );
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      
      // Reload notifications
      await loadNotifications();
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Bell className="w-8 h-8 mr-3 text-indigo-600" />
            Notifications
          </h1>
          <p className="mt-2 text-gray-600">
            AI-powered talent discoveries and updates
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Unread Only Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">Unread only</span>
          </label>

          {/* Mark All Read */}
          {unreadCount > 0 && (
            <Button
              variant="secondary"
              onClick={handleMarkAllRead}
              icon={<CheckCheck className="w-4 h-4" />}
            >
              Mark all read ({unreadCount})
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {NOTIFICATION_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setPage(0);
                }}
                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    isActive
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner message="Loading notifications..." />
        </div>
      ) : error ? (
        <EmptyState
          icon={<Eye className="w-12 h-12" />}
          title="Error loading notifications"
          description={error}
        />
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={<Eye className="w-12 h-12" />}
          title={unreadOnly ? "No unread notifications" : "No notifications"}
          description={
            unreadOnly
              ? "You're all caught up! New discoveries will appear here."
              : "AI monitoring will discover candidates and notify you here."
          }
        />
      ) : (
        <div className="space-y-3">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.notification_id}
              notification={notification}
              onRead={handleRead}
              onDismiss={handleDismiss}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {notifications.length === pageSize && (
        <div className="flex items-center justify-center gap-4 pt-6">
          <Button
            variant="secondary"
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page + 1}
          </span>
          <Button
            variant="secondary"
            onClick={() => setPage(page + 1)}
            disabled={notifications.length < pageSize}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}


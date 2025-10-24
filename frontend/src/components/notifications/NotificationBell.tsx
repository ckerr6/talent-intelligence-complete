/**
 * NotificationBell Component
 * 
 * Bell icon in header with unread count badge.
 * Opens dropdown on click.
 */

import { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { notificationService } from '../../services/notificationService';
import NotificationDropdown from './NotificationDropdown';

interface NotificationBellProps {
  className?: string;
}

export default function NotificationBell({ className = '' }: NotificationBellProps) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Start polling for unread count on mount
    notificationService.startPolling(30000); // Poll every 30 seconds

    // Subscribe to unread count changes
    const unsubscribe = notificationService.onUnreadCountChange((count) => {
      setUnreadCount(count);
    });

    // Initial fetch
    notificationService.getUnreadCount().then(setUnreadCount).catch(console.error);

    // Cleanup on unmount
    return () => {
      notificationService.stopPolling();
      unsubscribe();
    };
  }, []);

  const handleClick = () => {
    setIsOpen(!isOpen);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Bell Button */}
      <button
        onClick={handleClick}
        className="relative p-2 rounded-full hover:bg-gray-100 transition-colors duration-200"
        aria-label="Notifications"
      >
        <Bell className="w-6 h-6 text-gray-600" />
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full border-2 border-white">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={handleClose}
          />
          
          {/* Dropdown Panel */}
          <div className="absolute right-0 mt-2 w-96 z-50">
            <NotificationDropdown onClose={handleClose} />
          </div>
        </>
      )}
    </div>
  );
}


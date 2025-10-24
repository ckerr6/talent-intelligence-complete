/**
 * Notification Service Client
 * 
 * API client for AI-powered notifications and monitoring.
 */

import axios, { AxiosInstance } from 'axios';
import type {
  NotificationListResponse,
  NotificationStats,
  NotificationType,
  MonitoringResults,
  SchedulerStatus,
} from '../types/notifications';

class NotificationService {
  private client: AxiosInstance;
  private pollingInterval: number | null = null;
  private unreadCountCallbacks: Set<(count: number) => void> = new Set();

  constructor() {
    this.client = axios.create({
      baseURL: '/api/notifications',
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use((config) => {
      console.log(`[Notifications API] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[Notifications API Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get list of notifications
   */
  async getNotifications(params?: {
    unreadOnly?: boolean;
    notificationType?: NotificationType;
    limit?: number;
    offset?: number;
  }): Promise<NotificationListResponse> {
    const response = await this.client.get('', { params });
    return response.data;
  }

  /**
   * Get count of unread notifications
   */
  async getUnreadCount(): Promise<number> {
    const response = await this.client.get('/unread-count');
    return response.data.count;
  }

  /**
   * Mark a notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    await this.client.post(`/${notificationId}/read`);
  }

  /**
   * Mark all notifications as read
   */
  async markAllRead(): Promise<{ count: number }> {
    const response = await this.client.post('/mark-all-read');
    return response.data;
  }

  /**
   * Dismiss a notification (soft delete)
   */
  async dismiss(notificationId: string): Promise<void> {
    await this.client.delete(`/${notificationId}`);
  }

  /**
   * Mark a notification as actioned
   */
  async markAsActioned(notificationId: string): Promise<void> {
    await this.client.post(`/${notificationId}/action`);
  }

  /**
   * Get notification statistics
   */
  async getStats(days: number = 7): Promise<NotificationStats> {
    const response = await this.client.get('/stats', {
      params: { days }
    });
    return response.data;
  }

  /**
   * Manually trigger monitoring job (for testing)
   */
  async triggerMonitoring(): Promise<MonitoringResults> {
    const response = await this.client.post('/trigger-monitoring');
    return response.data.results;
  }

  /**
   * Get scheduler status
   */
  async getSchedulerStatus(): Promise<SchedulerStatus> {
    const response = await this.client.get('/scheduler-status');
    return response.data;
  }

  /**
   * Start polling for unread count updates
   * Polls every 30 seconds by default
   */
  startPolling(interval: number = 30000): void {
    if (this.pollingInterval) {
      return; // Already polling
    }

    // Initial fetch
    this.pollUnreadCount();

    // Set up interval
    this.pollingInterval = window.setInterval(() => {
      this.pollUnreadCount();
    }, interval);

    console.log(`[Notifications] Started polling every ${interval/1000}s`);
  }

  /**
   * Stop polling for unread count updates
   */
  stopPolling(): void {
    if (this.pollingInterval) {
      window.clearInterval(this.pollingInterval);
      this.pollingInterval = null;
      console.log('[Notifications] Stopped polling');
    }
  }

  /**
   * Register a callback to be called when unread count changes
   */
  onUnreadCountChange(callback: (count: number) => void): () => void {
    this.unreadCountCallbacks.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.unreadCountCallbacks.delete(callback);
    };
  }

  /**
   * Internal method to poll unread count and notify callbacks
   */
  private async pollUnreadCount(): Promise<void> {
    try {
      const count = await this.getUnreadCount();
      
      // Notify all registered callbacks
      this.unreadCountCallbacks.forEach(callback => {
        try {
          callback(count);
        } catch (error) {
          console.error('[Notifications] Error in unread count callback:', error);
        }
      });
    } catch (error) {
      console.error('[Notifications] Error polling unread count:', error);
    }
  }
}

// Export singleton instance
export const notificationService = new NotificationService();

// Also export the class for testing
export { NotificationService };


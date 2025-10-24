/**
 * Notification types for AI-First Recruiting Platform
 */

export type NotificationType = 
  | 'new_match' 
  | 'job_change' 
  | 'github_activity' 
  | 'rising_talent' 
  | 'network_connection' 
  | 'ai_suggestion';

export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Notification {
  notification_id: string;
  user_id: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  title: string;
  message: string;
  person_id?: string;
  person_name?: string;
  action_url?: string;
  action_label: string;
  metadata: Record<string, any>;
  is_read: boolean;
  is_dismissed: boolean;
  is_actioned: boolean;
  created_at: string;
  read_at?: string;
  actioned_at?: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  offset: number;
  limit: number;
}

export interface NotificationStats {
  period_days: number;
  total_notifications: number;
  total_read: number;
  total_actioned: number;
  overall_read_rate: number;
  overall_action_rate: number;
  by_type: Record<string, {
    total: number;
    read: number;
    actioned: number;
    read_rate: number;
    action_rate: number;
  }>;
}

export interface MonitoringResults {
  user_id: string;
  run_at: string;
  new_matches: any[];
  job_changes: any[];
  github_activity: any[];
  rising_talent: any[];
  notifications_created: number;
  errors: string[];
}

export interface SchedulerStatus {
  running: boolean;
  jobs: Array<{
    id: string;
    name: string;
    next_run: string | null;
    trigger: string;
  }>;
  timezone?: string;
}


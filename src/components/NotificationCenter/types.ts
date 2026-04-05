export type NotificationType =
  | 'task_status'
  | 'agent_alert'
  | 'collaboration'
  | 'system_announce'
  | 'permission_change';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  content: string;
  read: boolean;
  createdAt: string;
  targetUrl?: string;
  metadata?: Record<string, unknown>;
}

export interface NotificationPreference {
  type: NotificationType;
  enabled: boolean;
  popup: boolean;
  inApp: boolean;
}

export interface NotificationFilters {
  readStatus: 'all' | 'unread' | 'read';
  type?: NotificationType;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface UnreadCountResponse {
  count: number;
}

export interface WsNotificationMessage {
  type: 'new_notification';
  payload: Notification;
}

export type ReadStatusFilter = 'all' | 'unread' | 'read';

export const NOTIFICATION_TYPE_CONFIG: Record<NotificationType, {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
}> = {
  task_status: {
    label: '任务状态',
    icon: 'ClipboardDocumentCheckIcon',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
  },
  agent_alert: {
    label: '智能体告警',
    icon: 'BellAlertIcon',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
  },
  collaboration: {
    label: '协同邀请',
    icon: 'UserGroupIcon',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
  },
  system_announce: {
    label: '系统公告',
    icon: 'MegaphoneIcon',
    color: 'text-gray-400',
    bgColor: 'bg-gray-500/20',
  },
  permission_change: {
    label: '权限变更',
    icon: 'KeyIcon',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
  },
};

export const DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreference[] = [
  { type: 'task_status', enabled: true, popup: true, inApp: true },
  { type: 'agent_alert', enabled: true, popup: true, inApp: true },
  { type: 'collaboration', enabled: true, popup: true, inApp: true },
  { type: 'system_announce', enabled: true, popup: false, inApp: true },
  { type: 'permission_change', enabled: true, popup: true, inApp: true },
];

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BellIcon,
  CheckIcon,
  CheckCircleIcon,
  ChatBubbleLeftIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string | null;
  content: string;
  link: string | null;
  action_text: string | null;
  related_id: string | null;
  related_type: string | null;
  is_read: boolean;
  created_at: string | null;
}

const NotificationBell: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadUnreadCount = useCallback(async () => {
    try {
      const response = await api.get('/notifications/unread-count');
      setUnreadCount(response.data.unread_count);
    } catch {
      console.error('Failed to load unread count');
    }
  }, []);

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/notifications', { params: { limit: 10 } });
      setNotifications(response.data.notifications);
      setUnreadCount(response.data.unread_count);
    } catch {
      showToast.error('加载通知失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [loadUnreadCount]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      loadNotifications();
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      try {
        await api.put(`/notifications/${notification.id}/read`);
        setNotifications(notifications.map(n =>
          n.id === notification.id ? { ...n, is_read: true } : n
        ));
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch {
        console.error('Failed to mark as read');
      }
    }

    setIsOpen(false);

    if (notification.link) {
      navigate(notification.link);
    } else if (notification.related_id) {
      if (notification.related_type === 'task' || notification.related_type === 'report') {
        navigate(`/tasks/${notification.related_id}/report`);
      } else if (notification.related_type === 'team') {
        navigate(`/teams/${notification.related_id}`);
      }
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      showToast.success('已全部标记为已读');
    } catch {
      showToast.error('操作失败');
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'report_completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'report_failed':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      case 'comment_mention':
      case 'comment_reply':
        return <ChatBubbleLeftIcon className="w-5 h-5 text-blue-500" />;
      case 'refund':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'integral_low':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'complaint_reply':
        return <ChatBubbleLeftIcon className="w-5 h-5 text-purple-500" />;
      case 'task_shared':
        return <DocumentTextIcon className="w-5 h-5 text-primary-500" />;
      case 'member_joined':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      default:
        return <DocumentTextIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={handleToggle}
        className="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
      >
        <BellIcon className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 overflow-hidden z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">通知</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700"
              >
                全部已读
              </button>
            )}
          </div>

          {/* Content */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">加载中...</div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <BellIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                <p className="text-gray-500 dark:text-gray-400">暂无通知</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-700">
                {notifications.map((notification) => (
                  <button
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      !notification.is_read ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className={`text-sm ${!notification.is_read ? 'font-semibold' : 'font-medium'} text-gray-900 dark:text-white`}>
                            {notification.title || '通知'}
                          </p>
                          {!notification.is_read && (
                            <span className="w-2 h-2 bg-primary-500 rounded-full flex-shrink-0" />
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                          {notification.content}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {formatTime(notification.created_at)}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-3 border-t border-gray-100 dark:border-gray-700">
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate('/notifications');
                }}
                className="w-full text-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700"
              >
                查看全部通知
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;

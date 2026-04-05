import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BellIcon,
  CheckCircleIcon,
  ChatBubbleLeftIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

interface Notification {
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

const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/notifications', { 
        params: { limit: 50, is_read: filter === 'unread' ? false : undefined } 
      });
      setNotifications(response.data.notifications);
      setUnreadCount(response.data.unread_count);
    } catch {
      showToast.error('加载通知失败');
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n =>
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {
      showToast.error('操作失败');
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

  const handleDelete = async (notificationId: string) => {
    try {
      await api.delete(`/notifications/${notificationId}`);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      showToast.success('通知已删除');
    } catch {
      showToast.error('删除失败');
    }
  };

  const handleBatchMarkRead = async () => {
    if (selectedIds.size === 0) return;
    try {
      await Promise.all(
        Array.from(selectedIds).map(id => api.put(`/notifications/${id}/read`))
      );
      setNotifications(notifications.map(n =>
        selectedIds.has(n.id) ? { ...n, is_read: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - selectedIds.size));
      setSelectedIds(new Set());
      showToast.success(`已标记 ${selectedIds.size} 条为已读`);
    } catch {
      showToast.error('操作失败');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    try {
      await Promise.all(
        Array.from(selectedIds).map(id => api.delete(`/notifications/${id}`))
      );
      setNotifications(notifications.filter(n => !selectedIds.has(n.id)));
      setSelectedIds(new Set());
      showToast.success(`已删除 ${selectedIds.size} 条通知`);
    } catch {
      showToast.error('删除失败');
    }
  };

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === notifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(notifications.map(n => n.id)));
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      await handleMarkAsRead(notification.id);
    }

    if (notification.link) {
      navigate(notification.link);
    } else if (notification.related_id) {
      if (notification.related_type === 'task' || notification.related_type === 'report') {
        navigate(`/tasks/${notification.related_id}/report`);
      }
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'report_completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'report_failed':
        return <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />;
      case 'comment_mention':
      case 'comment_reply':
        return <ChatBubbleLeftIcon className="w-6 h-6 text-blue-500" />;
      case 'refund':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'integral_low':
        return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-500" />;
      case 'complaint_reply':
        return <ChatBubbleLeftIcon className="w-6 h-6 text-purple-500" />;
      case 'task_shared':
        return <DocumentTextIcon className="w-6 h-6 text-primary-500" />;
      case 'member_joined':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      default:
        return <DocumentTextIcon className="w-6 h-6 text-gray-500" />;
    }
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      report_completed: '报告完成',
      report_failed: '报告失败',
      comment_mention: '评论提及',
      comment_reply: '评论回复',
      report_shared: '报告分享',
      refund: '积分退还',
      integral_low: '积分不足',
      complaint_reply: '申诉回复',
      system: '系统通知',
      welcome: '欢迎消息',
      task_shared: '任务分享',
      member_joined: '成员加入',
    };
    return labels[type] || '通知';
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return <LoadingCard message="加载通知..." />;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <BellIcon className="w-7 h-7 text-primary-600" />
            通知中心
          </h1>
          {unreadCount > 0 && (
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              您有 <span className="font-medium text-primary-600 dark:text-primary-400">{unreadCount}</span> 条未读通知
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as 'all' | 'unread')}
            className="px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-200"
          >
            <option value="all">全部通知</option>
            <option value="unread">未读通知</option>
          </select>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <CheckIcon className="w-4 h-4" />
              全部已读
            </button>
          )}
        </div>
      </div>

      {/* Batch Actions */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
          <span className="text-sm text-primary-700 dark:text-primary-300">
            已选择 {selectedIds.size} 条
          </span>
          <button
            onClick={handleBatchMarkRead}
            className="px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            标记已读
          </button>
          <button
            onClick={handleBatchDelete}
            className="px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-red-600 dark:text-red-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            删除
          </button>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            取消选择
          </button>
        </div>
      )}

      {/* Notifications List */}
      {notifications.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <BellIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">暂无通知</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">当有新动态时会在这里通知您</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {/* Select All */}
          <div className="flex items-center gap-3 p-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
            <input
              type="checkbox"
              checked={selectedIds.size === notifications.length && notifications.length > 0}
              onChange={toggleSelectAll}
              className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">全选</span>
          </div>
          
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                  !notification.is_read ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(notification.id)}
                    onChange={() => toggleSelect(notification.id)}
                    className="mt-1 w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
                  />
                  <div className="flex-shrink-0 mt-1">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                          {getTypeLabel(notification.type)}
                        </span>
                        {!notification.is_read && (
                          <span className="w-2 h-2 bg-primary-500 rounded-full" />
                        )}
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        {formatTime(notification.created_at)}
                      </span>
                    </div>
                    <h3 className={`mt-1 ${!notification.is_read ? 'font-semibold' : 'font-medium'} text-gray-900 dark:text-white`}>
                      {notification.title || '通知'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{notification.content}</p>
                    <div className="flex items-center gap-3 mt-3">
                      {(notification.link || notification.related_id) && (
                        <button
                          onClick={() => handleNotificationClick(notification)}
                          className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700"
                        >
                          {notification.action_text || '查看详情'}
                        </button>
                      )}
                      {!notification.is_read && (
                        <button
                          onClick={() => handleMarkAsRead(notification.id)}
                          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                        >
                          标记已读
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(notification.id)}
                        className="text-sm text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;

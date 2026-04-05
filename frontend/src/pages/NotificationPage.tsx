import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Notification {
  id: string;
  type: 'system' | 'task_complete' | 'integral' | 'feedback_reply' | 'promotion';
  title: string;
  content: string;
  read: boolean;
  created_at: string;
}

const NotificationPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'system' | 'task_complete' | 'integral' | 'feedback_reply' | 'promotion'>('all');

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (filter !== 'all') params.append('type', filter);

      const response = await fetch(`http://localhost:8000/api/notifications?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`http://localhost:8000/api/notifications/${id}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      setNotifications(prev =>
        prev.map(n => n.read ? { ...n, isRead: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch('http://localhost:8000/api/notifications/read-all', {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      system: '🔔',
      task_complete: '✅',
      integral: '💰',
      feedback_reply: '💬',
      promotion: '🎁',
    };
    return icons[type] || '🔔';
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      system: 'bg-blue-100 text-blue-700',
      task_complete: 'bg-green-100 text-green-700',
      integral: 'bg-yellow-100 text-yellow-700',
      feedback_reply: 'bg-purple-100 text-purple-700',
      promotion: 'bg-pink-100 text-pink-700',
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };

  const getTypeName = (type: string) => {
    const names: Record<string, string> = {
      system: '系统通知',
      task_complete: '任务完成',
      integral: '积分变动',
      feedback_reply: '反馈回复',
      promotion: '促销活动',
    };
    return names[type] || type;
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">通知中心</h1>
        {unreadCount > 0 && (
          <span className="bg-red-500 text-white text-sm px-2 py-1 rounded-full">
            {unreadCount} 条未读
          </span>
        )}
      </div>

      <div className="flex gap-2 mb-6">
        {['all', 'system', 'task_complete', 'integral', 'feedback_reply', 'promotion'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-3 py-1 rounded-full text-sm ${
              filter === type ? 'bg-primary text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {getTypeName(type)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          暂无通知
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow ${
                !notification.read ? 'border-l-2 border-blue-200' : ''
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{getTypeIcon(notification.type)}</span>
                <div className="flex-1">
                  <h3 className="font-medium">{notification.title}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {new Date(notification.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                {!notification.read && (
                  <button
                    onClick={() => handleMarkAsRead(notification.id)}
                    className="text-xs text-primary hover:text-primaryDark"
                  >
                    标为已读
                  </button>
                )}
              </div>
              <p className="text-gray-600 mt-2">{notification.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationPage;

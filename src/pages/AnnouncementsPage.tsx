import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  MegaphoneIcon,
  InformationCircleIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CheckIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Announcement {
  id: string;
  title: string;
  content: string;
  type: string;
  is_pinned: boolean;
  published_at: string;
  is_read: boolean;
}

const AnnouncementsPage: React.FC = () => {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnnouncement, setSelectedAnnouncement] = useState<Announcement | null>(null);

  useEffect(() => {
    loadAnnouncements();
  }, []);

  const loadAnnouncements = async () => {
    setLoading(true);
    try {
      const response = await api.get('announcements');
      setAnnouncements(response.data);
    } catch {
      showToast.error('加载公告失败');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: string) => {
    try {
      await api.post(`/api/announcements/${id}/read`);
      setAnnouncements(announcements.map(a => 
        a.id === id ? { ...a, is_read: true } : a
      ));
      if (selectedAnnouncement?.id === id) {
        setSelectedAnnouncement({ ...selectedAnnouncement, is_read: true });
      }
    } catch {
      showToast.error('标记失败');
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('announcements/read-all');
      setAnnouncements(announcements.map(a => ({ ...a, is_read: true })));
      showToast.success('已全部标记为已读');
    } catch {
      showToast.error('操作失败');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'feature':
        return <SparklesIcon className="w-5 h-5 text-purple-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      default:
        return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
    }
  };

  const getTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      feature: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
      warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
      success: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    };
    const labels: Record<string, string> = {
      feature: '新功能',
      warning: '警告',
      success: '好消息',
      info: '通知',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[type] || styles.info}`}>
        {labels[type] || '通知'}
      </span>
    );
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const unreadCount = announcements.filter(a => !a.is_read).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <MegaphoneIcon className="w-7 h-7 text-primary-600" />
              公告中心
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              {unreadCount > 0 ? `您有 ${unreadCount} 条未读公告` : '所有公告已读'}
            </p>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
            >
              <CheckIcon className="w-4 h-4" />
              全部标记已读
            </button>
          )}
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-500">加载中...</p>
          </div>
        ) : announcements.length === 0 ? (
          <div className="text-center py-12">
            <MegaphoneIcon className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-gray-500 dark:text-gray-400">暂无公告</p>
          </div>
        ) : (
          <div className="space-y-4">
            {announcements.map((announcement, index) => (
              <motion.div
                key={announcement.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={`bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow ${
                  !announcement.is_read ? 'ring-2 ring-primary-500 ring-opacity-50' : ''
                }`}
              >
                <div
                  className="p-6 cursor-pointer"
                  onClick={() => setSelectedAnnouncement(announcement)}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {getTypeIcon(announcement.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        {announcement.is_pinned && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 rounded">
                            置顶
                          </span>
                        )}
                        {getTypeBadge(announcement.type)}
                        {!announcement.is_read && (
                          <span className="w-2 h-2 bg-primary-500 rounded-full" />
                        )}
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        {announcement.title}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400 text-sm line-clamp-2">
                        {announcement.content}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                        发布于 {formatDate(announcement.published_at)}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <EyeIcon className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {selectedAnnouncement && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
            >
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  {getTypeIcon(selectedAnnouncement.type)}
                  {getTypeBadge(selectedAnnouncement.type)}
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  {selectedAnnouncement.title}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  发布于 {formatDate(selectedAnnouncement.published_at)}
                </p>
              </div>
              <div className="p-6 overflow-y-auto max-h-[50vh]">
                <div className="prose dark:prose-invert max-w-none">
                  {selectedAnnouncement.content.split('\n').map((paragraph, index) => (
                    <p key={index} className="text-gray-600 dark:text-gray-400 leading-relaxed">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  onClick={() => setSelectedAnnouncement(null)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                >
                  关闭
                </button>
                {!selectedAnnouncement.is_read && (
                  <button
                    onClick={() => markAsRead(selectedAnnouncement.id)}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    标记已读
                  </button>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnnouncementsPage;

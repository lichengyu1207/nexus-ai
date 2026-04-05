import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  FunnelIcon,
  ArrowDownTrayIcon,
  CheckCheckIcon,
  TrashIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { FixedSizeList as List } from 'react-window';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow, format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import {
  useNotifications,
  useUnreadCount,
  useNotificationPreferences,
} from '../../components/NotificationCenter';
import {
  NotificationItem,
  NOTIFICATION_TYPE_CONFIG,
} from '../../components/NotificationCenter';
import type { Notification, NotificationType, NotificationFilters } from '../../components/NotificationCenter/types';

const ITEM_HEIGHT = 100;

export default function NotificationHistory() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<NotificationFilters>({
    readStatus: 'all',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  const { unreadCount, resetUnreadCount } = useUnreadCount();

  const {
    notifications,
    total,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    isMarkingAllRead,
  } = useNotifications({ filters, pageSize: 30 });

  const preferences = useNotificationPreferences();

  const filteredNotifications = notifications.filter((n) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      n.title.toLowerCase().includes(query) ||
      n.content.toLowerCase().includes(query)
    );
  });

  const handleSelectAll = () => {
    if (selectedIds.size === filteredNotifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredNotifications.map((n) => n.id)));
    }
  };

  const handleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleBatchMarkRead = () => {
    selectedIds.forEach((id) => markAsRead(id));
    setSelectedIds(new Set());
  };

  const handleBatchDelete = () => {
    selectedIds.forEach((id) => deleteNotification(id));
    setSelectedIds(new Set());
  };

  const handleExport = useCallback(() => {
    const data = filteredNotifications.map((n) => ({
      标题: n.title,
      内容: n.content,
      类型: NOTIFICATION_TYPE_CONFIG[n.type].label,
      状态: n.read ? '已读' : '未读',
      时间: format(new Date(n.createdAt), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN }),
    }));

    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map((row) => Object.values(row).join(',')),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notifications-${format(new Date(), 'yyyyMMdd-HHmmss')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredNotifications]);

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    if (notification.targetUrl) {
      navigate(notification.targetUrl);
    }
  };

  const handleTypeFilter = (type?: NotificationType) => {
    setFilters((prev) => ({ ...prev, type }));
  };

  const handleReadStatusFilter = (status: 'all' | 'unread' | 'read') => {
    setFilters((prev) => ({ ...prev, readStatus: status }));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-2xl font-bold text-white mb-2">通知历史</h1>
          <p className="text-gray-400 text-sm">
            共 {total} 条通知，{unreadCount} 条未读
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-4 flex flex-wrap items-center gap-3"
        >
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="搜索通知..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              showFilters ? 'bg-amber-500 text-gray-900' : 'bg-white/5 text-gray-300 hover:bg-white/10'
            }`}
          >
            <FunnelIcon className="w-5 h-5" />
            筛选
          </button>

          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 text-gray-300 rounded-lg hover:bg-white/10 transition-colors"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            导出
          </button>

          <button
            onClick={markAllAsRead}
            disabled={isMarkingAllRead}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500/20 text-amber-400 rounded-lg hover:bg-amber-500/30 transition-colors disabled:opacity-50"
          >
            <CheckCheckIcon className="w-5 h-5" />
            全部已读
          </button>
        </motion.div>

        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-4 bg-white/5 border border-white/10 rounded-lg"
          >
            <div className="flex flex-wrap gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">阅读状态</label>
                <div className="flex gap-2">
                  {(['all', 'unread', 'read'] as const).map((status) => (
                    <button
                      key={status}
                      onClick={() => handleReadStatusFilter(status)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                        filters.readStatus === status
                          ? 'bg-amber-500 text-gray-900'
                          : 'bg-white/5 text-gray-300 hover:bg-white/10'
                      }`}
                    >
                      {status === 'all' ? '全部' : status === 'unread' ? '未读' : '已读'}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">通知类型</label>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleTypeFilter(undefined)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      !filters.type
                        ? 'bg-amber-500 text-gray-900'
                        : 'bg-white/5 text-gray-300 hover:bg-white/10'
                    }`}
                  >
                    全部类型
                  </button>
                  {Object.entries(NOTIFICATION_TYPE_CONFIG).map(([type, config]) => (
                    <button
                      key={type}
                      onClick={() => handleTypeFilter(type as NotificationType)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                        filters.type === type
                          ? 'bg-amber-500 text-gray-900'
                          : 'bg-white/5 text-gray-300 hover:bg-white/10'
                      }`}
                    >
                      {config.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-3 bg-amber-500/20 border border-amber-500/30 rounded-lg flex items-center gap-4"
          >
            <span className="text-amber-400 text-sm">
              已选择 {selectedIds.size} 条通知
            </span>
            <button
              onClick={handleBatchMarkRead}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors"
            >
              <CheckCheckIcon className="w-4 h-4" />
              标记已读
            </button>
            <button
              onClick={handleBatchDelete}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
            >
              <TrashIcon className="w-4 h-4" />
              删除
            </button>
            <button
              onClick={() => setSelectedIds(new Set())}
              className="ml-auto text-sm text-gray-400 hover:text-white transition-colors"
            >
              取消选择
            </button>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-white/5 border border-white/10 rounded-xl overflow-hidden"
        >
          <div className="flex items-center gap-4 p-3 border-b border-white/10 bg-white/5">
            <input
              type="checkbox"
              checked={selectedIds.size === filteredNotifications.length && filteredNotifications.length > 0}
              onChange={handleSelectAll}
              className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
            />
            <span className="text-sm text-gray-400 flex-1">通知内容</span>
            <span className="text-sm text-gray-400 w-24 text-center">类型</span>
            <span className="text-sm text-gray-400 w-20 text-center">状态</span>
            <span className="text-sm text-gray-400 w-32 text-right">时间</span>
            <span className="text-sm text-gray-400 w-20 text-center">操作</span>
          </div>

          <div className="min-h-[400px]">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
                />
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <span className="text-4xl mb-2">🔔</span>
                <p className="text-sm">暂无通知</p>
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {filteredNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className="flex items-center gap-4 p-3 hover:bg-white/5 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.has(notification.id)}
                      onChange={() => handleSelect(notification.id)}
                      className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
                    />
                    <div className="flex-1 min-w-0">
                      <h4
                        className={`text-sm truncate cursor-pointer ${
                          !notification.read ? 'font-semibold text-white' : 'text-gray-300'
                        }`}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        {notification.title}
                      </h4>
                      <p className="text-xs text-gray-500 truncate mt-0.5">
                        {notification.content}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-0.5 text-xs rounded ${
                        NOTIFICATION_TYPE_CONFIG[notification.type].bgColor
                      } ${NOTIFICATION_TYPE_CONFIG[notification.type].color} w-24 text-center`}
                    >
                      {NOTIFICATION_TYPE_CONFIG[notification.type].label}
                    </span>
                    <span
                      className={`text-xs w-20 text-center ${
                        notification.read ? 'text-gray-500' : 'text-amber-400'
                      }`}
                    >
                      {notification.read ? '已读' : '未读'}
                    </span>
                    <span className="text-xs text-gray-500 w-32 text-right">
                      {formatDistanceToNow(new Date(notification.createdAt), {
                        addSuffix: true,
                        locale: zhCN,
                      })}
                    </span>
                    <div className="flex items-center gap-1 w-20 justify-center">
                      {!notification.read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="p-1 rounded hover:bg-white/10 transition-colors"
                          aria-label="标记已读"
                        >
                          <CheckCheckIcon className="w-4 h-4 text-gray-400 hover:text-green-400" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="p-1 rounded hover:bg-white/10 transition-colors"
                        aria-label="删除"
                      >
                        <TrashIcon className="w-4 h-4 text-gray-400 hover:text-red-400" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {hasNextPage && (
            <div className="p-4 border-t border-white/10 flex justify-center">
              <button
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="px-6 py-2 text-sm text-amber-400 bg-amber-500/10 rounded-lg hover:bg-amber-500/20 transition-colors disabled:opacity-50"
              >
                {isFetchingNextPage ? '加载中...' : '加载更多'}
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

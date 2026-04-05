import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cog6ToothIcon, CheckCheckIcon, ArrowRightIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import type { Notification, ReadStatusFilter } from './types';
import { NotificationList } from './NotificationList';
import { NotificationSettingsModal } from './NotificationSettingsModal';

export interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: Notification[];
  isLoading: boolean;
  isFetchingNextPage: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
  onMarkRead: (id: string) => void;
  onMarkAllRead: () => void;
  onDelete: (id: string) => void;
  onNotificationClick?: (notification: Notification) => void;
  isMarkingAllRead: boolean;
  preferences: {
    preferences: import('./types').NotificationPreference[];
    updatePreferences: (prefs: import('./types').NotificationPreference[]) => void;
    isUpdating: boolean;
  };
}

const TABS: { key: ReadStatusFilter; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'unread', label: '未读' },
  { key: 'read', label: '已读' },
];

export function NotificationPanel({
  isOpen,
  onClose,
  notifications,
  isLoading,
  isFetchingNextPage,
  hasMore,
  onLoadMore,
  onMarkRead,
  onMarkAllRead,
  onDelete,
  onNotificationClick,
  isMarkingAllRead,
  preferences,
}: NotificationPanelProps) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<ReadStatusFilter>('all');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const filteredNotifications = notifications.filter((n) => {
    if (activeTab === 'unread') return !n.read;
    if (activeTab === 'read') return n.read;
    return true;
  });

  const handleViewAll = useCallback(() => {
    navigate('/notifications');
    onClose();
  }, [navigate, onClose]);

  const handleNotificationClick = useCallback(
    (notification: Notification) => {
      if (notification.targetUrl) {
        navigate(notification.targetUrl);
        onClose();
      }
      onNotificationClick?.(notification);
    },
    [navigate, onClose, onNotificationClick]
  );

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 w-[380px] bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
            role="dialog"
            aria-label="通知中心"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <h3 className="text-base font-semibold text-white">通知中心</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsSettingsOpen(true)}
                  className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                  aria-label="通知设置"
                >
                  <Cog6ToothIcon className="w-5 h-5 text-gray-400" />
                </button>
                <button
                  onClick={onMarkAllRead}
                  disabled={isMarkingAllRead}
                  className="flex items-center gap-1 px-2 py-1 text-xs text-amber-400 hover:bg-amber-500/10 rounded-lg transition-colors disabled:opacity-50"
                  aria-label="全部已读"
                >
                  <CheckCheckIcon className="w-4 h-4" />
                  全部已读
                </button>
              </div>
            </div>

            <div className="flex border-b border-white/10">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`
                    flex-1 py-2.5 text-sm font-medium transition-colors relative
                    ${activeTab === tab.key ? 'text-amber-400' : 'text-gray-400 hover:text-white'}
                  `}
                >
                  {tab.label}
                  {activeTab === tab.key && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400"
                    />
                  )}
                </button>
              ))}
            </div>

            <div className="h-[400px] overflow-hidden">
              <NotificationList
                notifications={filteredNotifications}
                isLoading={isLoading}
                isFetchingNextPage={isFetchingNextPage}
                hasMore={hasMore}
                onLoadMore={onLoadMore}
                onMarkRead={onMarkRead}
                onDelete={onDelete}
                onClick={handleNotificationClick}
                height={400}
              />
            </div>

            <div className="p-3 border-t border-white/10">
              <button
                onClick={handleViewAll}
                className="w-full flex items-center justify-center gap-1 py-2 text-sm text-amber-400 hover:bg-amber-500/10 rounded-lg transition-colors"
              >
                查看全部通知
                <ArrowRightIcon className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <NotificationSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        preferences={preferences.preferences}
        onUpdatePreferences={preferences.updatePreferences}
        isUpdating={preferences.isUpdating}
      />
    </>
  );
}

import { useState, useRef, useEffect, useCallback } from 'react';
import { NotificationBell } from './NotificationBell';
import { NotificationPanel } from './NotificationPanel';
import { useNotifications } from './hooks/useNotifications';
import { useUnreadCount } from './hooks/useUnreadCount';
import { useNotificationPreferences } from './hooks/useNotificationPreferences';
import { useNotificationWebSocket } from './hooks/useNotificationWebSocket';
import type { Notification, NotificationFilters } from './types';

export interface NotificationCenterProps {
  onNotificationClick?: (notification: Notification) => void;
}

export function NotificationCenter({ onNotificationClick }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [filters, setFilters] = useState<NotificationFilters>({
    readStatus: 'all',
  });
  const containerRef = useRef<HTMLDivElement>(null);

  const { unreadCount } = useUnreadCount();

  const {
    notifications,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    isMarkingAllRead,
  } = useNotifications({ filters });

  const preferences = useNotificationPreferences();

  const handleNewNotification = useCallback(
    (notification: Notification) => {
      if (preferences.shouldShowPopup(notification.type)) {
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);
      }
    },
    [preferences]
  );

  const { isConnected } = useNotificationWebSocket({
    onNewNotification: handleNewNotification,
    enabled: true,
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    onNotificationClick?.(notification);
  };

  return (
    <div ref={containerRef} className="relative">
      <NotificationBell
        onClick={handleToggle}
        unreadCount={unreadCount}
        isShaking={isShaking}
      />

      <NotificationPanel
        isOpen={isOpen}
        onClose={handleClose}
        notifications={notifications}
        isLoading={isLoading}
        isFetchingNextPage={isFetchingNextPage}
        hasMore={hasNextPage ?? false}
        onLoadMore={fetchNextPage}
        onMarkRead={markAsRead}
        onMarkAllRead={markAllAsRead}
        onDelete={deleteNotification}
        onNotificationClick={handleNotificationClick}
        isMarkingAllRead={isMarkingAllRead}
        preferences={{
          preferences: preferences.preferences,
          updatePreferences: preferences.updatePreferences,
          isUpdating: preferences.isUpdating,
        }}
      />

      {!isConnected && (
        <span className="absolute -bottom-1 -right-1 w-2 h-2 rounded-full bg-yellow-500" />
      )}
    </div>
  );
}

export { NotificationBell } from './NotificationBell';
export { NotificationPanel } from './NotificationPanel';
export { NotificationList } from './NotificationList';
export { NotificationItem } from './NotificationItem';
export { NotificationSettingsModal } from './NotificationSettingsModal';
export * from './types';
export * from './hooks/useNotifications';
export * from './hooks/useUnreadCount';
export * from './hooks/useNotificationPreferences';
export * from './hooks/useNotificationWebSocket';

import { create } from 'zustand';
import type { NotificationPayload } from '../types';

interface NotificationStore {
  notifications: NotificationPayload[];
  unreadCount: number;
  loading: boolean;
  error: string | null;

  setNotifications: (notifications: NotificationPayload[]) => void;
  addNotification: (notification: NotificationPayload) => void;
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  removeNotification: (notificationId: string) => void;
  clearNotifications: () => void;
  incrementUnreadCount: () => void;
  decrementUnreadCount: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: null,

  setNotifications: (notifications) => {
    const unreadCount = notifications.filter((n) => !n.read).length;
    set({ notifications, unreadCount });
  },

  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
    }));
  },

  markAsRead: (notificationId) => {
    set((state) => {
      const notification = state.notifications.find((n) => n.id === notificationId);
      const wasUnread = notification && !notification.read;

      return {
        notifications: state.notifications.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        ),
        unreadCount: wasUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount,
      };
    });
  },

  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }));
  },

  removeNotification: (notificationId) => {
    set((state) => {
      const notification = state.notifications.find((n) => n.id === notificationId);
      const wasUnread = notification && !notification.read;

      return {
        notifications: state.notifications.filter((n) => n.id !== notificationId),
        unreadCount: wasUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount,
      };
    });
  },

  clearNotifications: () => {
    set({ notifications: [], unreadCount: 0 });
  },

  incrementUnreadCount: () => {
    set((state) => ({
      unreadCount: state.unreadCount + 1,
    }));
  },

  decrementUnreadCount: () => {
    set((state) => ({
      unreadCount: Math.max(0, state.unreadCount - 1),
    }));
  },

  setLoading: (loading) => {
    set({ loading });
  },

  setError: (error) => {
    set({ error });
  },
}));

export default useNotificationStore;

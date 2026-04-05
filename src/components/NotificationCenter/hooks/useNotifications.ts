import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Notification, NotificationFilters, NotificationListResponse } from '../types';

const API_BASE = '/api/notifications';

async function fetchNotifications(
  page: number,
  limit: number,
  filters: NotificationFilters
): Promise<NotificationListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
    readStatus: filters.readStatus,
  });

  if (filters.type) {
    params.append('type', filters.type);
  }

  const response = await fetch(`${API_BASE}?${params}`);
  if (!response.ok) {
    throw new Error('Failed to fetch notifications');
  }
  return response.json();
}

async function markAsRead(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}/read`, {
    method: 'PUT',
  });
  if (!response.ok) {
    throw new Error('Failed to mark notification as read');
  }
}

async function markAllAsRead(): Promise<void> {
  const response = await fetch(`${API_BASE}/read-all`, {
    method: 'PUT',
  });
  if (!response.ok) {
    throw new Error('Failed to mark all notifications as read');
  }
}

async function deleteNotification(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete notification');
  }
}

export interface UseNotificationsOptions {
  filters: NotificationFilters;
  pageSize?: number;
}

export function useNotifications(options: UseNotificationsOptions) {
  const { filters, pageSize = 20 } = options;
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: ['notifications', filters],
    queryFn: ({ pageParam = 1 }) => fetchNotifications(pageParam, pageSize, filters),
    getNextPageParam: (lastPage) => (lastPage.hasMore ? lastPage.page + 1 : undefined),
    initialPageParam: 1,
  });

  const markReadMutation = useMutation({
    mutationFn: markAsRead,
    onSuccess: (_, id) => {
      queryClient.setQueryData<{ pages: NotificationListResponse[] }>(
        ['notifications', filters],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              notifications: page.notifications.map((n) =>
                n.id === id ? { ...n, read: true } : n
              ),
            })),
          };
        }
      );
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteNotification,
    onSuccess: (_, id) => {
      queryClient.setQueryData<{ pages: NotificationListResponse[] }>(
        ['notifications', filters],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              notifications: page.notifications.filter((n) => n.id !== id),
              total: page.total - 1,
            })),
          };
        }
      );
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    },
  });

  const notifications = query.data?.pages.flatMap((page) => page.notifications) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;

  return {
    notifications,
    total,
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    error: query.error,
    markAsRead: markReadMutation.mutate,
    markAllAsRead: markAllReadMutation.mutate,
    deleteNotification: deleteMutation.mutate,
    isMarkingRead: markReadMutation.isPending,
    isMarkingAllRead: markAllReadMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}

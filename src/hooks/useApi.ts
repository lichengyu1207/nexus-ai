import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { AppApiError } from '@/services/api';

export interface Task {
  id: string;
  user_id: string;
  query: string;
  status: string;
  progress: number;
  style: string;
  created_at: string;
  completed_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  has_more: boolean;
}

export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...taskKeys.lists(), filters] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
};

export const reportKeys = {
  all: ['reports'] as const,
  lists: () => [...reportKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...reportKeys.lists(), filters] as const,
  details: () => [...reportKeys.all, 'detail'] as const,
  detail: (id: string) => [...reportKeys.details(), id] as const,
};

export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  unreadCount: () => [...notificationKeys.all, 'unreadCount'] as const,
};

export function useTasks(params: {
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: taskKeys.list(params),
    queryFn: async () => {
      const response = await api.get('/tasks', { params });
      return response.data as Task[];
    },
    staleTime: 1000 * 30,
  });
}

export function useTask(taskId: string) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: async () => {
      const response = await api.get(`/tasks/${taskId}`);
      return response.data as Task;
    },
    enabled: !!taskId,
    staleTime: 1000 * 60,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { query: string; style?: string }) => {
      const response = await api.post('/tasks', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (taskId: string) => {
      await api.delete(`/tasks/${taskId}`);
      return taskId;
    },
    onSuccess: (taskId) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      queryClient.removeQueries({ queryKey: taskKeys.detail(taskId) });
    },
  });
}

export function useReports(params: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: reportKeys.list(params),
    queryFn: async () => {
      const response = await api.get('/reports', { params });
      return response.data;
    },
    staleTime: 1000 * 60,
  });
}

export function useReport(reportId: string) {
  return useQuery({
    queryKey: reportKeys.detail(reportId),
    queryFn: async () => {
      const response = await api.get(`/reports/${reportId}`);
      return response.data;
    },
    enabled: !!reportId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useNotifications(params: { limit?: number; is_read?: boolean }) {
  return useQuery({
    queryKey: notificationKeys.lists(),
    queryFn: async () => {
      const response = await api.get('/notifications', { params });
      return response.data;
    },
    staleTime: 1000 * 10,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: async () => {
      const response = await api.get('/notifications/unread-count');
      return response.data.count as number;
    },
    staleTime: 1000 * 10,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (notificationId: string) => {
      await api.put(`/notifications/${notificationId}/read`);
      return notificationId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      await api.put('/notifications/read-all');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function usePrefetchTask() {
  const queryClient = useQueryClient();
  
  return (taskId: string) => {
    queryClient.prefetchQuery({
      queryKey: taskKeys.detail(taskId),
      queryFn: async () => {
        const response = await api.get(`/tasks/${taskId}`);
        return response.data;
      },
    });
  };
}

export function useInfiniteTasks(params: { limit?: number }) {
  const limit = params.limit || 20;
  
  return useInfiniteQuery({
    queryKey: taskKeys.list({ limit, infinite: true }),
    queryFn: async ({ pageParam = 0 }) => {
      const response = await api.get('/tasks', {
        params: { limit, offset: pageParam },
      });
      return {
        items: response.data as Task[],
        nextOffset: response.data.length === limit ? pageParam + limit : undefined,
      };
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextOffset,
  });
}

export function useApiError() {
  return (error: unknown) => {
    if (error instanceof AppApiError) {
      return error.message;
    }
    if (error instanceof Error) {
      return error.message;
    }
    return '发生未知错误';
  };
}

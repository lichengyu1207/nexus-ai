import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { taskApi, Task, TaskListResponse, TaskMessage, TaskStep } from '../services/api';

export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...taskKeys.lists(), { filters }] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
  messages: (id: string) => [...taskKeys.detail(id), 'messages'] as const,
  steps: (id: string) => [...taskKeys.detail(id), 'steps'] as const,
  report: (id: string) => [...taskKeys.detail(id), 'report'] as const,
};

export function useTasks(params?: { limit?: number; offset?: number; status?: string }) {
  return useQuery({
    queryKey: taskKeys.list(params || {}),
    queryFn: () => taskApi.list(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTask(taskId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => taskApi.get(taskId),
    enabled: options?.enabled !== false && !!taskId,
    staleTime: 2 * 60 * 1000,
    refetchInterval: (query) => {
      const task = query.state.data;
      if (task && task.status === 'running') {
        return 2000;
      }
      return false;
    },
  });
}

export function useTaskMessages(taskId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: taskKeys.messages(taskId),
    queryFn: () => taskApi.getMessages(taskId),
    enabled: options?.enabled !== false && !!taskId,
    staleTime: 30 * 1000,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && data.messages.some(m => m.type === 'agent_progress')) {
        return 1000;
      }
      return false;
    },
  });
}

export function useTaskSteps(taskId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: taskKeys.steps(taskId),
    queryFn: () => taskApi.getSteps(taskId),
    enabled: options?.enabled !== false && !!taskId,
    staleTime: 30 * 1000,
  });
}

export function useTaskReport(taskId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: taskKeys.report(taskId),
    queryFn: () => taskApi.getReport(taskId),
    enabled: options?.enabled !== false && !!taskId,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { query: string; style?: string }) => taskApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
}

export function useCreateBatchTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { queries: string[]; style?: string }) => taskApi.createBatch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => taskApi.delete(taskId),
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      queryClient.removeQueries({ queryKey: taskKeys.detail(taskId) });
    },
  });
}

export function useInfiniteTasks(params?: { limit?: number; status?: string }) {
  const limit = params?.limit || 10;

  return useInfiniteQuery({
    queryKey: taskKeys.list(params || {}),
    queryFn: ({ pageParam = 0 }) =>
      taskApi.list({
        limit,
        offset: pageParam * limit,
        status: params?.status,
      }),
    getNextPageParam: (lastPage, pages) => {
      const totalFetched = pages.reduce((sum, page) => sum + page.tasks.length, 0);
      if (totalFetched < lastPage.total) {
        return pages.length;
      }
      return undefined;
    },
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePrefetchTask() {
  const queryClient = useQueryClient();

  return (taskId: string) => {
    queryClient.prefetchQuery({
      queryKey: taskKeys.detail(taskId),
      queryFn: () => taskApi.get(taskId),
      staleTime: 2 * 60 * 1000,
    });
  };
}

export function useTaskPolling(taskId: string, options?: {
  enabled?: boolean;
  interval?: number;
  onComplete?: (task: Task) => void;
  onError?: (error: Error) => void;
}) {
  const queryClient = useQueryClient();
  const enabled = options?.enabled !== false && !!taskId;
  const interval = options?.interval || 2000;

  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: async () => {
      const task = await taskApi.get(taskId);

      if (task.status === 'completed' && options?.onComplete) {
        options.onComplete(task);
      }

      if (task.status === 'failed' && options?.onError) {
        options.onError(new Error('Task failed'));
      }

      return task;
    },
    enabled,
    refetchInterval: (query) => {
      const task = query.state.data;
      if (task && (task.status === 'running' || task.status === 'pending')) {
        return interval;
      }
      return false;
    },
    staleTime: 0,
  });
}

export function useUpdateTaskCache() {
  const queryClient = useQueryClient();

  return {
    updateTask: (taskId: string, updates: Partial<Task>) => {
      queryClient.setQueryData(taskKeys.detail(taskId), (old: Task | undefined) => {
        if (!old) return old;
        return { ...old, ...updates };
      });
    },
    addMessage: (taskId: string, message: TaskMessage) => {
      queryClient.setQueryData(taskKeys.messages(taskId), (old: { messages: TaskMessage[] } | undefined) => {
        if (!old) return { task_id: taskId, messages: [message], total: 1 };
        return {
          ...old,
          messages: [...old.messages, message],
          total: old.total + 1,
        };
      });
    },
    updateProgress: (taskId: string, progress: number, status?: string) => {
      queryClient.setQueryData(taskKeys.detail(taskId), (old: Task | undefined) => {
        if (!old) return old;
        return {
          ...old,
          progress,
          ...(status && { status }),
        };
      });
    },
  };
}

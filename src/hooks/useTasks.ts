import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { TaskStatusCardData } from '../components/tasks/TaskStatusCard';

interface TasksResponse {
  tasks: TaskStatusCardData[];
  total: number;
  page: number;
  limit: number;
}

interface TasksParams {
  status?: string;
  page?: number;
  limit?: number;
}

const fetchTasks = async (params: TasksParams): Promise<TasksResponse> => {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.append('status', params.status);
  if (params.page) searchParams.append('page', params.page.toString());
  if (params.limit) searchParams.append('limit', params.limit.toString());

  const response = await fetch(`/api/tasks?${searchParams.toString()}`);
  if (!response.ok) throw new Error('Failed to fetch tasks');
  return response.json();
};

const fetchTask = async (taskId: string): Promise<TaskStatusCardData> => {
  const response = await fetch(`/api/tasks/${taskId}`);
  if (!response.ok) throw new Error('Failed to fetch task');
  return response.json();
};

const createTask = async (data: { query: string; style?: string }): Promise<{ taskId: string }> => {
  const response = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create task');
  return response.json();
};

const deleteTask = async (taskId: string): Promise<void> => {
  const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete task');
};

export const useTasks = (params: TasksParams = {}) => {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: () => fetchTasks(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useTask = (taskId: string) => {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => fetchTask(taskId),
    enabled: !!taskId,
    staleTime: 2 * 60 * 1000,
  });
};

export const useCreateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useDeleteTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useBatchDeleteTasks = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskIds: string[]) => {
      await Promise.all(taskIds.map((id) => deleteTask(id)));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

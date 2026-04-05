import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';

export const useTasks = (params?: { status?: string; page?: number }) => {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.status) queryParams.append('status', params.status);
      if (params?.page) queryParams.append('page', String(params.page));
      const response = await api.get(`/api/tasks?${queryParams}`);
      return response.data;
    },
  });
};

export const useTask = (taskId: string | null) => {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => {
      if (!taskId) return null;
      const response = await api.get(`/api/tasks/${taskId}`);
      return response.data;
    },
    enabled: !!taskId,
  });
};

export const useCreateTask = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { query: string; type?: string }) => {
      const response = await api.post('/api/tasks', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useTaskSteps = (taskId: string | null) => {
  return useQuery({
    queryKey: ['task-steps', taskId],
    queryFn: async () => {
      if (!taskId) return [];
      const response = await api.get(`/api/tasks/${taskId}/steps`);
      return response.data.steps || [];
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      const steps = query.state.data;
      const hasRunning = steps?.some((s: any) => s.status === 'running');
      return hasRunning ? 2000 : false;
    },
  });
};

export const useTaskReport = (taskId: string | null) => {
  return useQuery({
    queryKey: ['task-report', taskId],
    queryFn: async () => {
      if (!taskId) return null;
      const response = await api.get(`/api/tasks/${taskId}/report`);
      return response.data;
    },
    enabled: !!taskId,
  });
};

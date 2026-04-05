import { useQuery } from '@tanstack/react-query';
import type { TaskDetail } from '../types';

async function fetchTaskDetail(taskId: string): Promise<TaskDetail> {
  const response = await fetch(`/api/tasks/${taskId}/detail`);
  if (!response.ok) {
    throw new Error('Failed to fetch task detail');
  }
  return response.json();
}

export function useTaskDetail(taskId: string | null) {
  return useQuery<TaskDetail, Error>({
    queryKey: ['taskDetail', taskId],
    queryFn: () => fetchTaskDetail(taskId!),
    enabled: taskId !== null,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });
}

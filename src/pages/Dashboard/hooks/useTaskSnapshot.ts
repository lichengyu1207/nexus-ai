import { useQuery } from '@tanstack/react-query';
import type { TaskSnapshot } from '../types';

async function fetchTaskSnapshot(): Promise<TaskSnapshot[]> {
  const response = await fetch('/api/dashboard/task-snapshot');
  if (!response.ok) throw new Error('Failed to fetch task snapshot');
  return response.json();
}

export function useTaskSnapshot() {
  return useQuery({
    queryKey: ['dashboard', 'task-snapshot'],
    queryFn: fetchTaskSnapshot,
    staleTime: 60000,
    refetchInterval: 30000,
  });
}

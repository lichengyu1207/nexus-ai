import { useQuery } from '@tanstack/react-query';
import type { ActivitySnapshot } from '../types';

async function fetchActivitySnapshot(): Promise<ActivitySnapshot> {
  const response = await fetch('/api/activity/snapshot');
  if (!response.ok) {
    throw new Error('Failed to fetch activity snapshot');
  }
  return response.json();
}

export function useActivitySnapshot(enabled: boolean = true) {
  return useQuery<ActivitySnapshot, Error>({
    queryKey: ['activitySnapshot'],
    queryFn: fetchActivitySnapshot,
    enabled,
    staleTime: 0,
    refetchOnWindowFocus: false,
    retry: 2,
  });
}

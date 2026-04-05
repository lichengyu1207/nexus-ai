import { useQuery } from '@tanstack/react-query';
import type { DashboardStats } from '../types';

async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch('/api/dashboard/stats');
  if (!response.ok) throw new Error('Failed to fetch dashboard stats');
  return response.json();
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: fetchDashboardStats,
    staleTime: 60000,
    refetchInterval: 30000,
  });
}

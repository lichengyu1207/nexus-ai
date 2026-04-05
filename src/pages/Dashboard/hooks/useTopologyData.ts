import { useQuery } from '@tanstack/react-query';
import type { TopologyData } from '../types';

async function fetchTopologyData(): Promise<TopologyData> {
  const response = await fetch('/api/dashboard/topology');
  if (!response.ok) throw new Error('Failed to fetch topology data');
  return response.json();
}

export function useTopologyData() {
  return useQuery({
    queryKey: ['dashboard', 'topology'],
    queryFn: fetchTopologyData,
    staleTime: 120000,
    refetchInterval: 60000,
  });
}

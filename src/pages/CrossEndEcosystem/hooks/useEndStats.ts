import { useQuery } from '@tanstack/react-query';
import type { EndStats, EndName } from '../types';

async function fetchEndStats(endId: EndName): Promise<EndStats> {
  const response = await fetch(`/api/ends/${endId}/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch end stats');
  }
  return response.json();
}

export function useEndStats(endId: EndName | null) {
  return useQuery<EndStats, Error>({
    queryKey: ['endStats', endId],
    queryFn: () => fetchEndStats(endId!),
    enabled: endId !== null,
    staleTime: 30000,
    refetchOnWindowFocus: true,
  });
}

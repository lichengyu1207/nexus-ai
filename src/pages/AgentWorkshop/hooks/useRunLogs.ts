import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { PaginatedLogs, RunLog } from '../types';

export const logKeys = {
  all: ['logs'] as const,
  byAgent: (agentId: string) => [...logKeys.all, agentId] as const,
  list: (agentId: string, filters: Record<string, unknown>) => [...logKeys.byAgent(agentId), 'list', filters] as const,
  detail: (agentId: string, logId: string) => [...logKeys.byAgent(agentId), 'detail', logId] as const,
};

export function useRunLogs(agentId: string, limit: number = 20) {
  return useInfiniteQuery<PaginatedLogs>({
    queryKey: logKeys.list(agentId, { limit }),
    queryFn: async ({ pageParam = 1 }) => {
      const response = await api.get(`/agents/${agentId}/logs`, {
        params: { page: pageParam, limit },
      });
      return response.data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.hasMore) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    enabled: !!agentId,
    staleTime: 30 * 1000,
  });
}

export function useRunLog(agentId: string, logId: string) {
  return useQuery<RunLog>({
    queryKey: logKeys.detail(agentId, logId),
    queryFn: async () => {
      const response = await api.get(`/agents/${agentId}/logs/${logId}`);
      return response.data;
    },
    enabled: !!agentId && !!logId,
    staleTime: 60 * 1000,
  });
}

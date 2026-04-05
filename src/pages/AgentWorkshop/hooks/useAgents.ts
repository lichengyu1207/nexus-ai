import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { Agent } from '../types';

export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...agentKeys.lists(), filters] as const,
  detail: (id: string) => [...agentKeys.all, 'detail', id] as const,
};

export function useAgents(filters?: { department?: 'san' | 'liu'; status?: 'healthy' | 'busy' | 'error' }) {
  return useQuery<Agent[]>({
    queryKey: agentKeys.list(filters || {}),
    queryFn: async () => {
      const response = await api.get('/agents', { params: filters });
      return response.data;
    },
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

export function useAgent(agentId: string) {
  return useQuery<Agent>({
    queryKey: agentKeys.detail(agentId),
    queryFn: async () => {
      const response = await api.get(`/agents/${agentId}`);
      return response.data;
    },
    enabled: !!agentId,
    staleTime: 60 * 1000,
  });
}

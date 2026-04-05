import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { GraphNode, GraphLink, MemoryFilters } from '../types';

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export const graphKeys = {
  all: ['memoryGraph'] as const,
  data: (filters?: MemoryFilters) => [...graphKeys.all, filters] as const,
  byIds: (ids: string[]) => [...graphKeys.all, 'ids', ids] as const,
};

export function useMemoryGraph(filters?: MemoryFilters) {
  return useQuery<GraphData>({
    queryKey: graphKeys.data(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      
      if (filters?.type?.length) params.append('type', filters.type.join(','));
      if (filters?.importanceMin) params.append('importanceMin', String(filters.importanceMin));
      if (filters?.dateRange) {
        params.append('start', filters.dateRange.start);
        params.append('end', filters.dateRange.end);
      }
      if (filters?.agentIds?.length) params.append('agentIds', filters.agentIds.join(','));
      
      const response = await api.get('/memories/graph', { params });
      return response.data;
    },
    staleTime: 10 * 60 * 1000,
  });
}

export function useMemoryGraphByIds(ids: string[]) {
  return useQuery<GraphData>({
    queryKey: graphKeys.byIds(ids),
    queryFn: async () => {
      const response = await api.get('/memories/graph', {
        params: { ids: ids.join(',') },
      });
      return response.data;
    },
    enabled: ids.length > 0,
    staleTime: 10 * 60 * 1000,
  });
}

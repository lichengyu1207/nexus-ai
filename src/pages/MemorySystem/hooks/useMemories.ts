import { useInfiniteQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { Memory, MemoryFilters, PaginatedMemories } from '../types';

export const memoryKeys = {
  all: ['memories'] as const,
  lists: () => [...memoryKeys.all, 'list'] as const,
  list: (filters: MemoryFilters) => [...memoryKeys.lists(), filters] as const,
  details: () => [...memoryKeys.all, 'detail'] as const,
  detail: (id: string) => [...memoryKeys.details(), id] as const,
  search: (query: string) => [...memoryKeys.all, 'search', query] as const,
};

export function useMemories(filters: MemoryFilters = {}, limit: number = 20) {
  return useInfiniteQuery<PaginatedMemories>({
    queryKey: memoryKeys.list(filters),
    queryFn: async ({ pageParam = 1 }) => {
      const params = new URLSearchParams({
        page: String(pageParam),
        limit: String(limit),
      });
      
      if (filters.searchText) params.append('q', filters.searchText);
      if (filters.type?.length) params.append('type', filters.type.join(','));
      if (filters.importanceMin) params.append('importanceMin', String(filters.importanceMin));
      if (filters.dateRange) {
        params.append('start', filters.dateRange.start);
        params.append('end', filters.dateRange.end);
      }
      if (filters.agentIds?.length) params.append('agentIds', filters.agentIds.join(','));
      if (filters.tags?.length) params.append('tags', filters.tags.join(','));
      
      const response = await api.get('/memories', { params });
      return response.data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.hasMore) return lastPage.page + 1;
      return undefined;
    },
    staleTime: 30 * 1000,
  });
}

export function useSearchMemories(query: string, limit: number = 20) {
  return useInfiniteQuery<PaginatedMemories>({
    queryKey: memoryKeys.search(query),
    queryFn: async ({ pageParam = 1 }) => {
      const response = await api.get('/memories/search', {
        params: { q: query, page: pageParam, limit },
      });
      return response.data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.hasMore) return lastPage.page + 1;
      return undefined;
    },
    enabled: !!query && query.length >= 2,
    staleTime: 60 * 1000,
  });
}

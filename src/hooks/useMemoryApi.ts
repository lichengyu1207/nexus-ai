import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import memoryApi, { Memory, MemoryGraph, MemorySearchParams } from '../api/memory';

export const memoryKeys = {
  all: ['memories'] as const,
  lists: () => [...memoryKeys.all, 'list'] as const,
  list: (params: MemorySearchParams) => [...memoryKeys.lists(), params] as const,
  details: () => [...memoryKeys.all, 'detail'] as const,
  detail: (id: string) => [...memoryKeys.details(), id] as const,
  graph: () => [...memoryKeys.all, 'graph'] as const,
  stats: () => [...memoryKeys.all, 'stats'] as const,
  timeline: (params?: { startDate?: string; endDate?: string }) => 
    [...memoryKeys.all, 'timeline', params] as const,
};

export function useMemories(params?: MemorySearchParams) {
  return useQuery({
    queryKey: memoryKeys.list(params || {}),
    queryFn: () => memoryApi.getMemories(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMemory(id: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: memoryKeys.detail(id),
    queryFn: () => memoryApi.getMemory(id),
    enabled: options?.enabled !== false && !!id,
    staleTime: 10 * 60 * 1000,
  });
}

export function useMemoryGraph(params?: {
  minImportance?: number;
  maxNodes?: number;
  agentFilter?: string[];
}) {
  return useQuery({
    queryKey: memoryKeys.graph(),
    queryFn: () => memoryApi.getMemoryGraph(params),
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

export function useMemoryStats() {
  return useQuery({
    queryKey: memoryKeys.stats(),
    queryFn: () => memoryApi.getMemoryStats(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMemoryTimeline(params?: {
  startDate?: string;
  endDate?: string;
  groupBy?: 'day' | 'week' | 'month';
}) {
  return useQuery({
    queryKey: memoryKeys.timeline(params),
    queryFn: () => memoryApi.getMemoryTimeline(params),
    staleTime: 10 * 60 * 1000,
  });
}

export function useInfiniteMemories(params?: Omit<MemorySearchParams, 'page'>) {
  const pageSize = params?.pageSize || 20;

  return useInfiniteQuery({
    queryKey: memoryKeys.list({ ...params, page: 1, pageSize } as MemorySearchParams),
    queryFn: ({ pageParam = 1 }) =>
      memoryApi.getMemories({
        ...params,
        page: pageParam,
        pageSize,
      }),
    getNextPageParam: (lastPage, pages) => {
      const totalFetched = pages.reduce((sum, page) => sum + page.memories.length, 0);
      if (totalFetched < lastPage.total) {
        return pages.length + 1;
      }
      return undefined;
    },
    initialPageParam: 1,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateMemory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof memoryApi.createMemory>[0]) =>
      memoryApi.createMemory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.graph() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.stats() });
    },
  });
}

export function useUpdateMemory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof memoryApi.updateMemory>[1] }) =>
      memoryApi.updateMemory(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.graph() });
    },
  });
}

export function useUpdateMemoryImportance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, importance }: { id: string; importance: number }) =>
      memoryApi.updateImportance(id, importance),
    onSuccess: (_, { id, importance }) => {
      queryClient.setQueryData(memoryKeys.detail(id), (old: Memory | undefined) => {
        if (!old) return old;
        return { ...old, importance };
      });
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.graph() });
    },
  });
}

export function useDeleteMemory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => memoryApi.deleteMemory(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: memoryKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.graph() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.stats() });
    },
  });
}

export function useStartMining() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params?: { depth?: number; focusArea?: string }) =>
      memoryApi.startMining(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: memoryKeys.graph() });
    },
  });
}

export function useMiningStatus(taskId: string | null) {
  return useQuery({
    queryKey: ['mining', taskId],
    queryFn: () => taskId ? memoryApi.getMiningStatus(taskId) : null,
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && data.progress < 100) {
        return 2000;
      }
      return false;
    },
    staleTime: 0,
  });
}

export function useSearchMemories(query: string, limit?: number) {
  return useQuery({
    queryKey: ['memories', 'search', query, limit],
    queryFn: () => memoryApi.searchMemories(query, limit),
    enabled: query.length >= 2,
    staleTime: 30 * 1000,
  });
}

export function useRelatedMemories(id: string, limit?: number) {
  return useQuery({
    queryKey: [...memoryKeys.detail(id), 'related', limit],
    queryFn: () => memoryApi.getRelatedMemories(id, limit),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePrefetchMemory() {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: memoryKeys.detail(id),
      queryFn: () => memoryApi.getMemory(id),
      staleTime: 10 * 60 * 1000,
    });
  };
}

export function useUpdateMemoryCache() {
  const queryClient = useQueryClient();

  return {
    addMemoryToGraph: (memory: Memory) => {
      queryClient.setQueryData(memoryKeys.graph(), (old: MemoryGraph | undefined) => {
        if (!old) return old;
        return {
          ...old,
          nodes: [
            ...old.nodes,
            {
              id: memory.id,
              label: memory.input.substring(0, 30),
              type: memory.type,
              importance: memory.importance,
            },
          ],
        };
      });
    },
    updateNodeImportance: (id: string, importance: number) => {
      queryClient.setQueryData(memoryKeys.graph(), (old: MemoryGraph | undefined) => {
        if (!old) return old;
        return {
          ...old,
          nodes: old.nodes.map((node) =>
            node.id === id ? { ...node, importance } : node
          ),
        };
      });
    },
    addEdge: (from: string, to: string, strength: number) => {
      queryClient.setQueryData(memoryKeys.graph(), (old: MemoryGraph | undefined) => {
        if (!old) return old;
        return {
          ...old,
          edges: [...old.edges, { from, to, strength }],
        };
      });
    },
  };
}

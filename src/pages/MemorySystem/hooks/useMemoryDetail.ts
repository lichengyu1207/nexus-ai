import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { Memory, MemoryVersion } from '../types';
import { memoryKeys } from './useMemories';

export function useMemoryDetail(memoryId: string | null) {
  return useQuery<Memory>({
    queryKey: memoryKeys.detail(memoryId || ''),
    queryFn: async () => {
      const response = await api.get(`/memories/${memoryId}`);
      return response.data;
    },
    enabled: !!memoryId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useMemoryVersions(memoryId: string | null) {
  return useQuery<MemoryVersion[]>({
    queryKey: [...memoryKeys.detail(memoryId || ''), 'versions'],
    queryFn: async () => {
      const response = await api.get(`/memories/${memoryId}/versions`);
      return response.data;
    },
    enabled: !!memoryId,
    staleTime: 10 * 60 * 1000,
  });
}

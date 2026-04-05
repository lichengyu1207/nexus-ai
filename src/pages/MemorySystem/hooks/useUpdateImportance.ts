import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { Memory } from '../types';
import { memoryKeys } from './useMemories';

interface UpdateImportanceParams {
  memoryId: string;
  importance: number;
}

export function useUpdateImportance() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ memoryId, importance }: UpdateImportanceParams) => {
      const response = await api.patch(`/memories/${memoryId}`, { importance });
      return response.data as Memory;
    },
    onMutate: async ({ memoryId, importance }) => {
      await queryClient.cancelQueries({ queryKey: memoryKeys.detail(memoryId) });
      
      const previousMemory = queryClient.getQueryData<Memory>(memoryKeys.detail(memoryId));
      
      if (previousMemory) {
        queryClient.setQueryData<Memory>(memoryKeys.detail(memoryId), {
          ...previousMemory,
          importance,
        });
      }
      
      return { previousMemory };
    },
    onError: (err, { memoryId }, context) => {
      if (context?.previousMemory) {
        queryClient.setQueryData<Memory>(memoryKeys.detail(memoryId), context.previousMemory);
      }
    },
    onSettled: (data, error, { memoryId }) => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.detail(memoryId) });
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() });
    },
  });
}

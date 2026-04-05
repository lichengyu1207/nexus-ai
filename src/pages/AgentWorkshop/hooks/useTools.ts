import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { Tool } from '../types';

export const toolKeys = {
  all: ['tools'] as const,
  byAgent: (agentId: string) => [...toolKeys.all, agentId] as const,
};

export function useTools(agentId: string) {
  return useQuery<Tool[]>({
    queryKey: toolKeys.byAgent(agentId),
    queryFn: async () => {
      const response = await api.get(`/agents/${agentId}/tools`);
      return response.data;
    },
    enabled: !!agentId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateToolPermission(agentId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ toolId, enabled }: { toolId: string; enabled: boolean }) => {
      const response = await api.put(`/agents/${agentId}/tools/${toolId}`, { enabled });
      return response.data;
    },
    onMutate: async ({ toolId, enabled }) => {
      await queryClient.cancelQueries({ queryKey: toolKeys.byAgent(agentId) });
      
      const previousTools = queryClient.getQueryData<Tool[]>(toolKeys.byAgent(agentId));
      
      if (previousTools) {
        const updatedTools = previousTools.map(tool =>
          tool.id === toolId ? { ...tool, enabled } : tool
        );
        queryClient.setQueryData<Tool[]>(toolKeys.byAgent(agentId), updatedTools);
      }
      
      return { previousTools };
    },
    onError: (err, variables, context) => {
      if (context?.previousTools) {
        queryClient.setQueryData<Tool[]>(toolKeys.byAgent(agentId), context.previousTools);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: toolKeys.byAgent(agentId) });
    },
  });
}

export function useUpdateToolParameters(agentId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ toolId, parameters }: { toolId: string; parameters: Record<string, unknown> }) => {
      const response = await api.put(`/agents/${agentId}/tools/${toolId}/parameters`, { parameters });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: toolKeys.byAgent(agentId) });
    },
  });
}

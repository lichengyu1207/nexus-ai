import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { WorkflowData, WorkflowNode } from '../types';

export const workflowKeys = {
  all: ['workflow'] as const,
  byAgent: (agentId: string) => [...workflowKeys.all, agentId] as const,
  node: (agentId: string, nodeId: string) => [...workflowKeys.all, agentId, 'node', nodeId] as const,
};

export function useWorkflowData(agentId: string) {
  return useQuery<WorkflowData>({
    queryKey: workflowKeys.byAgent(agentId),
    queryFn: async () => {
      const response = await api.get(`/agents/${agentId}/workflow`);
      return response.data;
    },
    enabled: !!agentId,
    staleTime: 30 * 1000,
    refetchInterval: 10 * 1000,
  });
}

export function useNodeDetail(agentId: string, nodeId: string) {
  return useQuery<WorkflowNode>({
    queryKey: workflowKeys.node(agentId, nodeId),
    queryFn: async () => {
      const response = await api.get(`/agents/${agentId}/workflow/nodes/${nodeId}`);
      return response.data;
    },
    enabled: !!agentId && !!nodeId,
    staleTime: 60 * 1000,
  });
}
